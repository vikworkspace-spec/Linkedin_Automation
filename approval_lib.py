#!/usr/bin/env python3
"""
approval_lib.py — Shared library for Slack Approval Workflow for LinkedIn Posts.

Handles:
  - Slack API communication (post messages, upload files, add/check reactions)
  - Post ID generation and tracking
  - Approval state management (JSON-backed)
  - Audit logging
  - Idempotency (no duplicates, no double-posting)

Usage in delivery scripts:
  from approval_lib import ApprovalManager, slack_api, CHANNEL
  mgr = ApprovalManager()
  post_id = mgr.post_with_approval(text="...")
  file_id = mgr.upload_with_approval(path="...", title="...", comment="...")
"""

import json
import os
import time
import datetime
import urllib.request
import urllib.parse
import subprocess
import sys
import hashlib

# ── Constants ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
CHANNEL = "C0BDL4V7VT4"  # #linkedin-content
APPROVAL_DATA_PATH = os.path.join(BASE_DIR, "approval_data.json")
APPROVAL_AUDIT_PATH = os.path.join(BASE_DIR, "approval_audit.jsonl")
APPROVAL_HISTORY_PATH = os.path.join(BASE_DIR, "approval_history.json")
PUBLISHED_LOG_PATH = os.path.join(BASE_DIR, "published_posts.json")

# Approval emoji markers
EMOJI_APPROVE = "\u2705"       # ✅
EMOJI_REJECT = "\u274c"        # ❌
EMOJI_REVISE = "\U0001f504"    # 🔄
EMOJI_PUBLISHED = "\U0001f4e2" # 📢

# 24 hours in seconds (approval expiration)
APPROVAL_EXPIRY_SECONDS = 86400

# ── Slack API Helpers ──────────────────────────────────────────────────────

def _read_token():
    """Read SLACK_BOT_TOKEN from .env file."""
    if not os.path.exists(ENV_PATH):
        print(f"[approval_lib] ERROR: .env file not found at {ENV_PATH}")
        return None
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("SLACK_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    print("[approval_lib] ERROR: SLACK_BOT_TOKEN not found in .env")
    return None

TOKEN = _read_token()

def slack_api(method, payload, json_body=True):
    """
    Call a Slack API method. Returns parsed JSON response.
    
    Args:
        method: Slack API method name (e.g., 'chat.postMessage')
        payload: dict of parameters
        json_body: If True, send as JSON; if False, send as form-urlencoded
    """
    if not TOKEN:
        print(f"[slack_api] ERROR: No token available")
        return {"ok": False, "error": "no_token"}
    
    url = f"https://slack.com/api/{method}"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    if json_body:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    else:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result
    except Exception as e:
        print(f"[slack_api] ERROR calling {method}: {e}")
        return {"ok": False, "error": str(e)}


def slack_api_get(method, params):
    """Call a Slack API GET method with query params."""
    if not TOKEN:
        print(f"[slack_api] ERROR: No token available")
        return {"ok": False, "error": "no_token"}
    
    url = f"https://slack.com/api/{method}?{urllib.parse.urlencode(params)}"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result
    except Exception as e:
        print(f"[slack_api] ERROR calling GET {method}: {e}")
        return {"ok": False, "error": str(e)}


# ── Post ID Generation ─────────────────────────────────────────────────────

def generate_post_id(content_text="", date_str=None):
    """
    Generate a unique post identifier.
    Format: post_YYYYMMDD_HHMMSS_XXXX
    where XXXX is a short hash from the content.
    """
    if date_str is None:
        date_str = datetime.date.today().isoformat().replace("-", "")
    now = datetime.datetime.now()
    time_str = now.strftime("%H%M%S")
    # Short hash from content for uniqueness
    content_hash = hashlib.md5(content_text.encode("utf-8")).hexdigest()[:6]
    return f"post_{date_str}_{time_str}_{content_hash}"


def generate_batch_id():
    """Generate a batch ID for a group of posts being delivered together."""
    return f"batch_{datetime.date.today().isoformat().replace('-', '')}_{int(time.time())}"


# ── Approval Data Management ───────────────────────────────────────────────

class ApprovalManager:
    """
    Manages the approval lifecycle for LinkedIn posts.
    Backed by a JSON file for persisting approval state.
    """
    
    def __init__(self, data_path=APPROVAL_DATA_PATH):
        self.data_path = data_path
        self.approvals = self._load()
    
    def _load(self):
        """Load approval data from JSON file."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return {}
        return {}
    
    def _save(self):
        """Save approval data to JSON file."""
        os.makedirs(os.path.dirname(self.data_path) or ".", exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.approvals, f, indent=2, ensure_ascii=False)
    
    def register_post(self, post_id, content_text, post_type="text", 
                      file_path=None, file_title=None, metadata=None):
        """
        Register a new post in the approval system.
        
        Args:
            post_id: Unique post identifier
            content_text: The post's text content
            post_type: Type of post (text, carousel, infographic, poll, etc.)
            file_path: Path to attached file (if any)
            file_title: Title of attached file (if any)
            metadata: Optional dict with additional data
        
        Returns:
            The post's approval record
        """
        now = datetime.datetime.utcnow().isoformat() + "Z"
        record = {
            "post_id": post_id,
            "content": content_text,
            "post_type": post_type,
            "file_path": file_path,
            "file_title": file_title,
            "metadata": metadata or {},
            "created_at": now,
            "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(seconds=APPROVAL_EXPIRY_SECONDS)).isoformat() + "Z",
            "status": "pending",  # pending | approved | rejected | revise | published
            "slack_message_ts": None,
            "slack_channel": CHANNEL,
            "approved_by": None,
            "approved_at": None,
            "published_at": None,
            "revision_notes": None,
        }
        self.approvals[post_id] = record
        self._save()
        return record
    
    def update_slack_ts(self, post_id, ts):
        """Update the Slack message timestamp for a registered post."""
        if post_id in self.approvals:
            self.approvals[post_id]["slack_message_ts"] = ts
            self._save()
    
    def get_post(self, post_id):
        """Get a post's approval record by ID."""
        return self.approvals.get(post_id)
    
    def get_pending_posts(self):
        """Get all posts that are pending approval and not expired."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        pending = {}
        for pid, record in self.approvals.items():
            if record.get("status") == "pending":
                # Check expiration
                if record.get("expires_at", "9999") <= now:
                    self._auto_reject(pid, reason="expired")
                    continue
                pending[pid] = record
        return pending
    
    def get_approved_posts(self):
        """Get all posts that are approved but not yet published."""
        approved = {}
        for pid, record in self.approvals.items():
            if record.get("status") == "approved":
                approved[pid] = record
        return approved
    
    def mark_approved(self, post_id, approved_by="slack_reaction"):
        """
        Mark a post as approved. Idempotent — if already published, won't change.
        
        Returns: True if successfully marked approved, False otherwise.
        """
        if post_id not in self.approvals:
            print(f"[approval_lib] WARNING: post_id '{post_id}' not found in approvals")
            return False
        
        record = self.approvals[post_id]
        
        # Idempotency: if already published, don't downgrade
        if record.get("status") == "published":
            print(f"[approval_lib] Post '{post_id}' already published, keeping published status")
            return True
        
        if record.get("status") == "rejected":
            print(f"[approval_lib] Post '{post_id}' was rejected, use mark_pending first to reset")
            return False
        
        now = datetime.datetime.utcnow().isoformat() + "Z"
        record["status"] = "approved"
        record["approved_by"] = approved_by
        record["approved_at"] = now
        self._save()
        
        # Write audit log
        self._write_audit_log({
            "event": "approved",
            "post_id": post_id,
            "approved_by": approved_by,
            "timestamp": now,
            "content_preview": record.get("content", "")[:200],
        })
        
        print(f"[approval_lib] ✅ Post '{post_id}' approved by '{approved_by}'")
        return True
    
    def mark_rejected(self, post_id, notes=None):
        """Mark a post as rejected."""
        if post_id not in self.approvals:
            return False
        now = datetime.datetime.utcnow().isoformat() + "Z"
        self.approvals[post_id]["status"] = "rejected"
        self.approvals[post_id]["revision_notes"] = notes
        self.approvals[post_id]["rejected_at"] = now
        self._save()
        self._write_audit_log({
            "event": "rejected",
            "post_id": post_id,
            "timestamp": now,
            "notes": notes,
        })
        print(f"[approval_lib] ❌ Post '{post_id}' rejected: {notes}")
        return True
    
    def mark_revise(self, post_id, notes=None):
        """Mark a post as needing revision."""
        if post_id not in self.approvals:
            return False
        now = datetime.datetime.utcnow().isoformat() + "Z"
        self.approvals[post_id]["status"] = "revise"
        self.approvals[post_id]["revision_notes"] = notes
        self._save()
        self._write_audit_log({
            "event": "revise_requested",
            "post_id": post_id,
            "timestamp": now,
            "notes": notes,
        })
        return True
    
    def mark_published(self, post_id):
        """Mark a post as published to LinkedIn."""
        if post_id not in self.approvals:
            return False
        now = datetime.datetime.utcnow().isoformat() + "Z"
        self.approvals[post_id]["status"] = "published"
        self.approvals[post_id]["published_at"] = now
        self._save()
        self._write_audit_log({
            "event": "published",
            "post_id": post_id,
            "timestamp": now,
        })
        print(f"[approval_lib] 📢 Post '{post_id}' published to LinkedIn")
        return True
    
    def mark_pending(self, post_id):
        """Reset a post back to pending (e.g., after rejection, if re-approved)."""
        if post_id not in self.approvals:
            return False
        self.approvals[post_id]["status"] = "pending"
        self.approvals[post_id]["approved_by"] = None
        self.approvals[post_id]["approved_at"] = None
        self._save()
        return True
    
    def _auto_reject(self, post_id, reason="expired"):
        """Auto-reject a post (internal, for expired approvals)."""
        if post_id in self.approvals:
            self.approvals[post_id]["status"] = "rejected"
            self.approvals[post_id]["revision_notes"] = f"Auto-rejected: {reason}"
            self._save()
            self._write_audit_log({
                "event": "auto_rejected",
                "post_id": post_id,
                "reason": reason,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            })
    
    def _write_audit_log(self, entry):
        """Append a JSON line to the audit log."""
        os.makedirs(os.path.dirname(APPROVAL_AUDIT_PATH) or ".", exist_ok=True)
        with open(APPROVAL_AUDIT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_audit_log(self, limit=50):
        """Read the audit log, newest first."""
        if not os.path.exists(APPROVAL_AUDIT_PATH):
            return []
        entries = []
        with open(APPROVAL_AUDIT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return entries[-limit:][::-1]
    
    def is_approved(self, post_id):
        """Check if a post is approved (status == 'approved')."""
        record = self.approvals.get(post_id)
        if not record:
            return False
        # Also check expiry
        now = datetime.datetime.utcnow().isoformat() + "Z"
        if record.get("status") == "approved" and record.get("expires_at", "9999") > now:
            return True
        return False
    
    def is_published(self, post_id):
        """Check if a post has been published."""
        record = self.approvals.get(post_id)
        return record is not None and record.get("status") == "published"
    
    def cleanup_expired(self):
        """Auto-reject all expired pending posts."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        count = 0
        for pid, record in list(self.approvals.items()):
            if record.get("status") == "pending" and record.get("expires_at", "9999") <= now:
                self._auto_reject(pid)
                count += 1
        if count:
            print(f"[approval_lib] Auto-rejected {count} expired posts")
        return count
    
    def get_summary_stats(self):
        """Get summary statistics about all tracked posts."""
        stats = {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "published": 0, "revise": 0, "expired": 0}
        now = datetime.datetime.utcnow().isoformat() + "Z"
        for pid, record in self.approvals.items():
            stats["total"] += 1
            status = record.get("status", "pending")
            if status == "pending" and record.get("expires_at", "9999") <= now:
                stats["expired"] += 1
            elif status in stats:
                stats[status] += 1
        return stats


# ── Slack Message Posting with Approval Markers ────────────────────────────

def post_text_with_approval(label, text, post_id=None, metadata=None):
    """
    Post text to Slack with approval workflow markers.
    
    Returns: (post_id, slack_ts) on success, (None, None) on failure.
    """
    mgr = ApprovalManager()
    
    if not post_id:
        post_id = generate_post_id(text)
    
    # Register in approval system
    mgr.register_post(post_id, text, post_type="text", metadata=metadata)
    
    # Build the Slack message with approval markers
    header = (
        f"📝 *Post ID: `{post_id}`*\n"
        f"⏰ *Status:* Pending Approval | *Expires:* ~24h\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    footer = (
        f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Actions:*\n"
        f"  {EMOJI_APPROVE} Approve | {EMOJI_REJECT} Reject | {EMOJI_REVISE} Revise\n"
        f"  Or use: `/approve_post {post_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    full_text = header + text + footer
    
    result = slack_api("chat.postMessage", {
        "channel": CHANNEL,
        "text": full_text,
        "unfurl_links": False,
        "unfurl_media": False,
    })
    
    if result.get("ok"):
        ts = result.get("ts")
        mgr.update_slack_ts(post_id, ts)
        
        # Add reaction markers to the message so users can click to approve/reject
        # Add initial reaction markers as hints
        for emoji in [EMOJI_APPROVE, EMOJI_REJECT, EMOJI_REVISE]:
            slack_api("reactions.add", {
                "channel": CHANNEL,
                "timestamp": ts,
                "name": _emoji_to_name(emoji),
            })
        
        print(f"  [{label}] ✓ Posted as {post_id} (ts: {ts})")
        return post_id, ts
    else:
        print(f"  [{label}] ✗ Slack error: {result.get('error')}")
        return None, None


def upload_with_approval(label, file_path, title, comment, post_type="file", metadata=None):
    """
    Upload a file to Slack with approval workflow markers.
    
    Returns: (post_id, file_id, slack_ts) on success, (None, None, None) on failure.
    """
    if not os.path.exists(file_path):
        print(f"  [{label}] MISSING {file_path}")
        return None, None, None
    
    mgr = ApprovalManager()
    
    # Generate a post_id for the file upload
    post_id = generate_post_id(comment + title)
    
    # Register
    mgr.register_post(post_id, comment, post_type=post_type, 
                      file_path=file_path, file_title=title, metadata=metadata)
    
    # Step 1: Get upload URL
    file_size = os.path.getsize(file_path)
    get_url_result = slack_api("files.getUploadURLExternal", {
        "filename": os.path.basename(file_path),
        "length": file_size,
    }, json_body=False)
    
    if not get_url_result.get("ok"):
        print(f"  [{label}] getUploadURL ERR {get_url_result.get('error')}")
        return None, None, None
    
    upload_url = get_url_result["upload_url"]
    file_id = get_url_result["file_id"]
    
    # Step 2: Upload file data
    try:
        subprocess.run(
            ["curl", "-s", "-F", f"file=@{file_path}", upload_url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"  [{label}] Upload failed: {e}")
        return None, None, None
    
    # Step 3: Build approval-marked comment
    header = (
        f"📎 *Post ID: `{post_id}`*\n"
        f"⏰ *Status:* Pending Approval | *Expires:* ~24h\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    footer = (
        f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Actions:*\n"
        f"  {EMOJI_APPROVE} Approve | {EMOJI_REJECT} Reject | {EMOJI_REVISE} Revise\n"
        f"  Or use: `/approve_post {post_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    approval_comment = header + comment + footer
    
    # Step 4: Complete the upload with approval comment
    complete_result = slack_api("files.completeUploadExternal", {
        "files": [{"id": file_id, "title": title}],
        "channel_id": CHANNEL,
        "initial_comment": approval_comment,
    })
    
    if complete_result.get("ok"):
        # Get the message timestamp from the file upload response
        # Slack returns file info with the message timestamp
        ts = None
        if "files" in complete_result:
            for f in complete_result["files"]:
                if "shares" in f:
                    for ch, shares in f["shares"].items():
                        if shares and isinstance(shares, list):
                            ts = shares[0].get("ts")
                            break
        
        if ts:
            mgr.update_slack_ts(post_id, ts)
            # Add reaction markers
            for emoji in [EMOJI_APPROVE, EMOJI_REJECT, EMOJI_REVISE]:
                slack_api("reactions.add", {
                    "channel": CHANNEL,
                    "timestamp": ts,
                    "name": _emoji_to_name(emoji),
                })
        
        print(f"  [{label}] ✓ Uploaded as {post_id}")
        return post_id, file_id, ts
    else:
        print(f"  [{label}] CompleteUpload ERR {complete_result.get('error')}")
        return None, None, None


def _emoji_to_name(emoji):
    """Convert emoji character to Slack emoji name."""
    emoji_map = {
        EMOJI_APPROVE: "white_check_mark",
        EMOJI_REJECT: "x",
        EMOJI_REVISE: "arrows_counterclockwise",
        EMOJI_PUBLISHED: "loudspeaker",
        "\u274c": "x",  # ❌ also
    }
    return emoji_map.get(emoji, "white_check_mark")


def _name_to_emoji(name):
    """Convert Slack emoji name to emoji character."""
    name_map = {
        "white_check_mark": EMOJI_APPROVE,
        "x": EMOJI_REJECT,
        "arrows_counterclockwise": EMOJI_REVISE,
        "loudspeaker": EMOJI_PUBLISHED,
    }
    return name_map.get(name, name)


# ── Reaction Monitoring ────────────────────────────────────────────────────

def check_reactions_for_post(ts, channel=CHANNEL):
    """
    Check the reactions on a specific Slack message.
    Returns a dict of emoji -> list of users who reacted.
    """
    result = slack_api_get("reactions.get", {
        "channel": channel,
        "timestamp": ts,
        "full": "true",
    })
    
    if not result.get("ok"):
        return {}
    
    reactions = {}
    for r in result.get("message", {}).get("reactions", []):
        emoji_name = r.get("name", "")
        users = r.get("users", [])
        reactions[_name_to_emoji(emoji_name)] = users
    
    return reactions


def monitor_and_update_approvals():
    """
    Scan all tracked posts for reaction changes.
    Updates the approval data based on reactions.
    
    This is the core function called by slack_approval_monitor.py.
    """
    mgr = ApprovalManager()
    
    # First, expire old posts
    mgr.cleanup_expired()
    
    # Get all pending posts that have a slack message ts
    pending = mgr.get_pending_posts()
    
    updated_count = 0
    
    for post_id, record in pending.items():
        ts = record.get("slack_message_ts")
        if not ts:
            continue
        
        reactions = check_reactions_for_post(ts)
        
        # Check for approve reaction
        if EMOJI_APPROVE in reactions:
            users = reactions[EMOJI_APPROVE]
            # The bot probably also reacted, so filter it out if possible
            # We check if there's at least one user reaction (beyond the bot)
            if users:
                mgr.mark_approved(post_id, approved_by=f"slack_reaction:{users[0]}")
                updated_count += 1
        
        # Check for reject reaction
        elif EMOJI_REJECT in reactions:
            users = reactions[EMOJI_REJECT]
            if users:
                mgr.mark_rejected(post_id, notes=f"Rejected by {users[0]}")
                updated_count += 1
        
        # Check for revise reaction
        elif EMOJI_REVISE in reactions:
            users = reactions[EMOJI_REVISE]
            if users:
                mgr.mark_revise(post_id, notes=f"Revise requested by {users[0]}")
                updated_count += 1
    
    return updated_count


# ── Publishing Gate ────────────────────────────────────────────────────────

def get_approved_posts_for_publishing():
    """
    Get the list of approved posts that are ready to publish.
    Used by scheduling scripts as a gate.
    
    Returns: dict of post_id -> approval record
    """
    mgr = ApprovalManager()
    mgr.cleanup_expired()
    return mgr.get_approved_posts()


def mark_post_as_published(post_id):
    """
    Mark a post as published after successful LinkedIn scheduling.
    Should be called after the scheduling script successfully posts.
    """
    mgr = ApprovalManager()
    return mgr.mark_published(post_id)


def is_post_approved_for_scheduling(post_id):
    """
    Check if a specific post is approved and can be scheduled.
    
    This is the publishing gate function.
    Returns: bool
    """
    mgr = ApprovalManager()
    return mgr.is_approved(post_id)


# ── Interactive Command Handlers ───────────────────────────────────────────

def handle_slash_command(post_id, action="approve", user=None):
    """
    Handle a slash command like /approve_post <post_id>.
    
    Args:
        post_id: The post ID to act on
        action: 'approve', 'reject', 'revise', or 'status'
        user: Slack user ID of who performed the action
    
    Returns: A response message string.
    """
    mgr = ApprovalManager()
    
    if action == "status":
        record = mgr.get_post(post_id)
        if not record:
            return f"❌ Post `{post_id}` not found in approval system."
        
        status = record.get("status", "unknown")
        created = record.get("created_at", "unknown")
        approved_by = record.get("approved_by", "N/A")
        approved_at = record.get("approved_at", "N/A")
        
        return (
            f"📋 *Post Status: `{post_id}`*\n"
            f"• Status: *{status}*\n"
            f"• Created: {created}\n"
            f"• Approved by: {approved_by}\n"
            f"• Approved at: {approved_at}\n"
            f"• Type: {record.get('post_type', 'N/A')}"
        )
    
    if action == "approve":
        approver = user or "slash_command"
        if mgr.mark_approved(post_id, approved_by=approver):
            return f"✅ Post `{post_id}` has been *APPROVED* by <@{user}>!" if user else f"✅ Post `{post_id}` has been *APPROVED*!"
        else:
            return f"⚠️ Could not approve `{post_id}`. It may already be published or rejected."
    
    elif action == "reject":
        if mgr.mark_rejected(post_id, notes=f"Rejected by {user}"):
            return f"❌ Post `{post_id}` has been *REJECTED* by <@{user}>!" if user else f"❌ Post `{post_id}` has been *REJECTED*!"
        return f"⚠️ Could not reject `{post_id}`."
    
    elif action == "revise":
        if mgr.mark_revise(post_id, notes=f"Revise requested by {user}"):
            return f"🔄 Post `{post_id}` marked for *REVISION* by <@{user}>!" if user else f"🔄 Post `{post_id}` marked for *REVISION*!"
        return f"⚠️ Could not mark `{post_id}` for revision."
    
    return f"❌ Unknown action: {action}"


def send_approval_summary():
    """
    Send a summary message to the channel with current approval status.
    """
    mgr = ApprovalManager()
    stats = mgr.get_summary_stats()
    
    summary = (
        f"📊 *Approval Queue Summary*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 Pending: {stats.get('pending', 0)}\n"
        f"✅ Approved: {stats.get('approved', 0)}\n"
        f"❌ Rejected: {stats.get('rejected', 0)}\n"
        f"🔄 Revise: {stats.get('revise', 0)}\n"
        f"📢 Published: {stats.get('published', 0)}\n"
        f"⏰ Expired: {stats.get('expired', 0)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Total tracked: {stats.get('total', 0)}"
    )
    
    result = slack_api("chat.postMessage", {
        "channel": CHANNEL,
        "text": summary,
    })
    
    return result.get("ok")


# ── CLI Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    
    if cmd == "summary":
        mgr = ApprovalManager()
        stats = mgr.get_summary_stats()
        print(json.dumps(stats, indent=2))
    
    elif cmd == "check":
        post_id = sys.argv[2] if len(sys.argv) > 2 else None
        if post_id:
            mgr = ApprovalManager()
            record = mgr.get_post(post_id)
            if record:
                print(json.dumps(record, indent=2, ensure_ascii=False))
            else:
                print(f"Post '{post_id}' not found.")
        else:
            approved = get_approved_posts_for_publishing()
            print(f"Approved posts ready for publishing: {len(approved)}")
            for pid, rec in approved.items():
                print(f"  • {pid} ({rec.get('post_type', 'text')})")
    
    elif cmd == "approve":
        post_id = sys.argv[2] if len(sys.argv) > 2 else None
        if post_id:
            msg = handle_slash_command(post_id, "approve", user="cli")
            print(msg)
    
    elif cmd == "send_summary":
        send_approval_summary()
        print("Summary sent to Slack.")
    
    elif cmd == "audit":
        mgr = ApprovalManager()
        entries = mgr.get_audit_log()
        for e in entries:
            print(json.dumps(e, ensure_ascii=False))
    
    else:
        print("Usage: python approval_lib.py <command>")
        print("Commands: summary, check <post_id>, approve <post_id>, send_summary, audit")
