#!/usr/bin/env python3
"""
ai_automation_coordinator.py — AI Automation Coordinator for LinkedIn Content Pipeline

Listens to Slack Events API in real-time and orchestrates the LinkedIn content
approval and publishing workflow.

## Operational Modes:

### 1. RECORD REACTIONS (Continuous Listening)
When a 'reaction_added' event is received:
  - ✅ (white_check_mark) → Post status changed to "Approved"
  - ❌ (x) → Post status changed to "Denied"
  - Updates approval_data.json accordingly (NO LinkedIn API call yet)

### 2. EXECUTE ONE-SHOT PUBLISH (The Final Trigger)
When an 'app_mention' event containing "publish" or "reviewed all" is received:
  - Scans approval_data.json for all posts marked strictly as "Approved"
  - Loops through approved posts and sends them to LinkedIn API sequentially
  - Posts a final summary message back to the Slack channel

### 3. URL Verification
Handles Slack's URL verification challenge during Events API setup.

## Slack Events API Setup:
1. Go to https://api.slack.com/apps → Your App
2. Enable "Event Subscriptions"
3. Set Request URL to: https://your-server:port/slack/events
4. Subscribe to bot events:
   - reaction_added
   - app_mention
5. Add the following OAuth Scopes:
   - reactions:read
   - chat:write
   - app_mentions:read
   - channels:history
   - channels:read

## Usage:
  # Run the server (development):
  python ai_automation_coordinator.py

  # Run with custom port:
  python ai_automation_coordinator.py --port 8080

  # Dry-run: Show what would happen without actually publishing:
  python ai_automation_coordinator.py --dry-run

  # One-time batch publish (without server):
  python ai_automation_coordinator.py --publish-batch

  # Simulate an app_mention event:
  python ai_automation_coordinator.py --simulate-mention "publish"
"""

import json
import os
import sys
import time
import datetime
import hmac
import hashlib
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add current dir for imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from approval_lib import (
    ApprovalManager,
    slack_api,
    CHANNEL,
    EMOJI_APPROVE,
    EMOJI_REJECT,
    EMOJI_REVISE,
    EMOJI_PUBLISHED,
    _emoji_to_name,
    _name_to_emoji,
)

from linkedin_publisher import LinkedInPublisher, get_approved_content


# ── Configuration ──────────────────────────────────────────────────────────

def _load_env():
    """Load environment variables from .env file."""
    env_vars = {}
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()
    return env_vars

ENV = _load_env()

# Slack signing secret for request verification
SLACK_SIGNING_SECRET = ENV.get("SLACK_SIGNING_SECRET") or os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_BOT_TOKEN = ENV.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_BOT_TOKEN", "")

# Server config
PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 3000
DRY_RUN = "--dry-run" in sys.argv


# ── Request Signature Verification ─────────────────────────────────────────

def verify_slack_signature(request_body, timestamp, signature):
    """
    Verify that requests are genuinely from Slack using the signing secret.
    
    Args:
        request_body: Raw request body as bytes
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header
    
    Returns:
        bool: True if signature is valid
    """
    if not SLACK_SIGNING_SECRET:
        # If no signing secret configured, skip verification (dev mode)
        return True
    
    # Check if timestamp is within 5 minutes
    try:
        if abs(int(time.time()) - int(timestamp)) > 300:
            return False
    except (ValueError, TypeError):
        return False
    
    # Create the basestring
    req = f"v0:{timestamp}:".encode("utf-8") + request_body
    
    # Compute signature
    my_signature = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode("utf-8"),
        req,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(my_signature, signature)


# ── Event Handlers ─────────────────────────────────────────────────────────

class EventHandler:
    """
    Handles Slack Events API event types.
    Routes events to the appropriate handler methods.
    """
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.publisher = LinkedInPublisher()
        self.mgr = ApprovalManager()
    
    def handle_event(self, event_data):
        """
        Main event dispatcher.
        
        Args:
            event_data: Parsed Slack Events API payload
        
        Returns:
            str: Response message (for logging/debugging)
        """
        event = event_data.get("event", {})
        event_type = event.get("type", "")
        
        if event_type == "reaction_added":
            return self._handle_reaction_added(event)
        elif event_type == "app_mention":
            return self._handle_app_mention(event)
        elif event_type == "message":
            # Handle direct messages that may contain commands
            return self._handle_message(event)
        else:
            # Acknowledge but don't process other event types
            return f"Ignored event type: {event_type}"
    
    def _get_post_id_from_message(self, message_text, message_ts=None):
        """
        Extract a post ID from a Slack message.
        
        Post IDs format: `post_YYYYMMDD_HHMMSS_XXXXXX`
        
        Also checks if the message's timestamp matches any stored post
        in the approval system.
        """
        # Try to extract from text
        match = re.search(r'`(post_\d{8}_\d{6}_[a-f0-9]{6})`', message_text or "")
        if match:
            return match.group(1)
        
        # If no explicit post ID in text, look up by Slack message timestamp
        if message_ts:
            for pid, record in self.mgr.approvals.items():
                if record.get("slack_message_ts") == message_ts:
                    return pid
        
        return None
    
    def _get_post_id_from_reaction_event(self, event):
        """
        When a reaction is added to a message, find the associated post ID.
        """
        item = event.get("item", {})
        message_ts = item.get("ts", "")
        channel = item.get("channel", "")
        
        # First, fetch the message to look for a post ID in its text
        if message_ts and channel:
            try:
                msg_result = slack_api("conversations.history", {
                    "channel": channel,
                    "latest": message_ts,
                    "limit": 1,
                    "inclusive": True,
                })
                if msg_result.get("ok") and msg_result.get("messages"):
                    msg = msg_result["messages"][0]
                    msg_text = msg.get("text", "")
                    
                    # Look for post ID in the message text
                    post_id = self._get_post_id_from_message(msg_text, message_ts)
                    if post_id:
                        return post_id
                    
                    # Also check thread replies
                    thread_ts = msg.get("thread_ts")
                    if thread_ts:
                        replies_result = slack_api("conversations.replies", {
                            "channel": channel,
                            "ts": thread_ts,
                            "limit": 10,
                        })
                        if replies_result.get("ok"):
                            for reply in replies_result.get("messages", []):
                                post_id = self._get_post_id_from_message(
                                    reply.get("text", ""), 
                                    reply.get("ts")
                                )
                                if post_id:
                                    return post_id
            except Exception as e:
                print(f"[coordinator] ⚠️ Error fetching message: {e}")
        
        # Fallback: Search by timestamp in approval data
        if message_ts:
            for pid, record in self.mgr.approvals.items():
                if record.get("slack_message_ts") == message_ts:
                    return pid
        
        return None
    
    def _handle_reaction_added(self, event):
        """
        Handle reaction_added events.
        
        - ✅ (white_check_mark) → Mark post as Approved
        - ❌ (x) → Mark post as Denied
        - 🔄 (arrows_counterclockwise) → Mark post for Revision
        
        Updates approval_data.json. Does NOT send LinkedIn API request.
        """
        reaction = event.get("reaction", "")
        user = event.get("user", "")
        item_user = event.get("item_user", "")
        
        # Skip reactions added by the bot itself
        bot_user_id = self._get_bot_user_id()
        if user == bot_user_id:
            return "Ignored bot's own reaction"
        
        # Map Slack emoji name to emoji character
        emoji_char = _name_to_emoji(reaction)
        
        # Only process relevant emoji reactions
        if emoji_char not in (EMOJI_APPROVE, EMOJI_REJECT, EMOJI_REVISE):
            return f"Ignored non-approval reaction: {reaction}"
        
        # Find the post ID this reaction was added to
        post_id = self._get_post_id_from_reaction_event(event)
        
        if not post_id:
            # Check if the message itself has a post ID we can extract
            item = event.get("item", {})
            channel = item.get("channel", "")
            message_ts = item.get("ts", "")
            
            # Try fetching the message
            if message_ts and channel:
                msg_result = slack_api("conversations.history", {
                    "channel": channel,
                    "latest": message_ts,
                    "limit": 1,
                    "inclusive": True,
                })
                if msg_result.get("ok") and msg_result.get("messages"):
                    msg = msg_result["messages"][0]
                    msg_text = msg.get("text", "")
                    
                    # Broad search for any post ID pattern
                    broad_match = re.search(r'(post_\d{8}_\d{6}_[a-f0-9]{6})', msg_text or "")
                    if broad_match:
                        post_id = broad_match.group(1)
            
            if not post_id:
                return f"Could not find post ID for reaction (emoji: {reaction}, user: {user})"
        
        # Process the reaction
        old_status = self.mgr.get_post(post_id)
        old_status_val = old_status.get("status") if old_status else "none"
        
        if emoji_char == EMOJI_APPROVE:
            # ✅ → Approve
            if old_status and old_status.get("status") == "published":
                return f"Post {post_id} already published, ignoring approval"
            
            if old_status and old_status.get("status") == "rejected":
                # Reset to pending first, then approve
                self.mgr.mark_pending(post_id)
            
            success = self.mgr.mark_approved(post_id, approved_by=f"reaction:{user}")
            
            if success:
                print(f"[coordinator] ✅ {post_id} APPROVED by <@{user}>")
                return f"✅ {post_id} approved"
            else:
                return f"⚠️ Could not approve {post_id}"
        
        elif emoji_char == EMOJI_REJECT:
            # ❌ → Deny
            if old_status and old_status.get("status") == "published":
                return f"Post {post_id} already published, cannot reject"
            
            success = self.mgr.mark_rejected(post_id, notes=f"Rejected by {user}")
            
            if success:
                print(f"[coordinator] ❌ {post_id} DENIED by <@{user}>")
                return f"❌ {post_id} denied"
            else:
                return f"⚠️ Could not reject {post_id}"
        
        elif emoji_char == EMOJI_REVISE:
            # 🔄 → Revise
            success = self.mgr.mark_revise(post_id, notes=f"Revise requested by {user}")
            
            if success:
                print(f"[coordinator] 🔄 {post_id} REVISION requested by <@{user}>")
                return f"🔄 {post_id} marked for revision"
            else:
                return f"⚠️ Could not mark {post_id} for revision"
        
        return f"Processed reaction {reaction} on post {post_id}"
    
    def _handle_app_mention(self, event):
        """
        Handle app_mention events.
        
        When the bot is mentioned with "publish" or "reviewed all":
        1. Scans for all "Approved" posts
        2. Publishes each to LinkedIn API sequentially
        3. Sends final summary to Slack
        
        Also supports:
          - "status" → Show approval queue status
          - "help" → Show available commands
          - "queue" → Show publish queue
        """
        text = event.get("text", "").lower()
        channel = event.get("channel", "")
        user = event.get("user", "")
        thread_ts = event.get("thread_ts") or event.get("ts", "")
        
        print(f"[coordinator] 📩 App mention from <@{user}>: {text[:200]}")
        
        # Parse the command
        if "publish" in text or "reviewed all" in text or "publish all" in text or "go live" in text:
            return self._execute_publish(channel, thread_ts)
        
        elif "status" in text or "summary" in text:
            return self._show_status(channel, thread_ts)
        
        elif "queue" in text or "approved" in text:
            return self._show_queue(channel, thread_ts)
        
        elif "help" in text or "commands" in text or "what can you" in text:
            return self._show_help(channel, thread_ts)
        
        elif "reset" in text or "unapprove" in text or "pending" in text:
            return self._show_pending(channel, thread_ts)
        
        elif "dry run" in text or "preview" in text or "what would" in text:
            return self._preview_publish(channel, thread_ts)
        
        else:
            # Default: show help
            return self._show_help(channel, thread_ts)
    
    def _handle_message(self, event):
        """
        Handle direct messages (non-mention messages).
        Only process if it's a DM to the bot.
        """
        channel_type = event.get("channel_type", "")
        text = event.get("text", "").lower()
        user = event.get("user", "")
        channel = event.get("channel", "")
        thread_ts = event.get("ts", "")
        
        # Only respond to direct messages (not channel messages without mention)
        if channel_type not in ("im", "mpim"):
            return "Ignored non-DM message"
        
        if "publish" in text or "reviewed all" in text:
            return self._execute_publish(channel, thread_ts)
        elif "status" in text:
            return self._show_status(channel, thread_ts)
        elif "help" in text:
            return self._show_help(channel, thread_ts)
        else:
            return self._show_help(channel, thread_ts)
    
    def _get_bot_user_id(self):
        """Get the bot's own user ID from Slack API."""
        try:
            result = slack_api("auth.test", {})
            if result.get("ok"):
                return result.get("user_id")
        except:
            pass
        return None
    
    # ── Publish Execution ─────────────────────────────────────────────
    
    def _execute_publish(self, channel, thread_ts):
        """
        Execute the one-shot publish workflow.
        
        1. Scan for all "Approved" posts
        2. Publish each via LinkedIn API
        3. Send final summary
        """
        if DRY_RUN:
            return self._preview_publish(channel, thread_ts)
        
        # Send "working on it" message
        slack_api("chat.postMessage", {
            "channel": channel or CHANNEL,
            "text": "🔄 *Processing your request...*\nScanning approval queue and preparing posts for LinkedIn.",
            "thread_ts": thread_ts,
        })
        
        # Get approved posts
        approved = get_approved_content()
        
        if not approved:
            # No approved posts found
            summary = (
                f"📭 *No Approved Posts Found*\n\n"
                f"There are no posts marked as *Approved* in the queue.\n\n"
                f"To approve posts:\n"
                f"  • React with {EMOJI_APPROVE} on any post in #linkedin-content\n"
                f"  • Or use: `/approve_post <post_id>`\n"
                f"  • Or just say: `@AI Coordinator approve all`\n\n"
                f"_Nothing to publish right now._"
            )
            slack_api("chat.postMessage", {
                "channel": channel or CHANNEL,
                "text": summary,
                "thread_ts": thread_ts,
            })
            return "No approved posts to publish"
        
        # Publish each approved post
        print(f"[coordinator] 🚀 Publishing {len(approved)} approved post(s)...")
        
        slack_api("chat.postMessage", {
            "channel": channel or CHANNEL,
            "text": f"🚀 *Starting batch publish...*\n{len(approved)} approved post(s) will be published to LinkedIn sequentially.",
            "thread_ts": thread_ts,
        })
        
        results = self.publisher.publish_batch(approved, send_summary=True)
        
        published_count = len(results["published"])
        skipped_count = len(results["failed"]) + len(results["skipped"])
        
        print(f"[coordinator] ✅ Batch complete. Published: {published_count}, Skipped: {skipped_count}")
        
        # The summary is already sent by publish_batch(), but send a confirmation
        slack_api("chat.postMessage", {
            "channel": channel or CHANNEL,
            "text": f"✅ All done! {published_count} posts published, {skipped_count} skipped.",
            "thread_ts": thread_ts,
        })
        
        return f"Published {published_count} posts, skipped {skipped_count}"
    
    def _preview_publish(self, channel, thread_ts):
        """Show what would be published (dry run)."""
        approved = get_approved_content()
        
        if not approved:
            msg = "📭 *Dry Run: Nothing to publish.*\nNo approved posts in the queue."
        else:
            lines = [f"🧪 *Dry Run: {len(approved)} post(s) ready to publish*"]
            lines.append("")
            for pid, rec in approved.items():
                ptype = rec.get("post_type", "text")
                preview = (rec.get("content", "") or "")[:100].replace("\n", " ")
                lines.append(f"  • `{pid}` ({ptype}): {preview}...")
            lines.append("")
            lines.append(f"_To publish, say `@AI Coordinator publish`_")
            msg = "\n".join(lines)
        
        slack_api("chat.postMessage", {
            "channel": channel or CHANNEL,
            "text": msg,
            "thread_ts": thread_ts,
        })
        
        return f"Preview: {len(approved)} posts ready"
    
    def _show_status(self, channel, thread_ts):
        """Show the current approval queue status."""
        stats = self.mgr.get_summary_stats()
        
        msg = (
            f"📊 *Approval Queue Status*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 Pending:    {stats.get('pending', 0)}\n"
            f"✅ Approved:   {stats.get('approved', 0)}\n"
            f"❌ Rejected:   {stats.get('rejected', 0)}\n"
            f"🔄 Revise:     {stats.get('revise', 0)}\n"
            f"📢 Published:  {stats.get('published', 0)}\n"
            f"⏰ Expired:    {stats.get('expired', 0)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Total tracked: {stats.get('total', 0)}"
        )
        
        slack_api("chat.postMessage", {
            "channel": channel or CHANNEL,
            "text": msg,
            "thread_ts": thread_ts,
        })
        
        return f"Status shown: {json.dumps(stats)}"
    
    def _show_queue(self, channel, thread_ts):
        """Show the publish queue (approved posts)."""
        approved = get_approved_content()
        
        if not approved:
            msg = "📭 *Publish Queue*\nNo approved posts waiting to publish."
        else:
            lines = [f"✅ *Publish Queue — {len(approved)} post(s) ready*"]
            lines.append("")
            for pid, rec in approved.items():
                ptype = rec.get("post_type", "text")
                preview = (rec.get("content", "") or "")[:80].replace("\n", " ")
                lines.append(f"  • `{pid}` ({ptype})")
            lines.append("")
            lines.append(f"_To publish all, say `@AI Coordinator publish`_")
            msg = "\n".join(lines)
        
        slack_api("chat.postMessage", {
            "channel": channel or CHANNEL,
            "text": msg,
            "thread_ts": thread_ts,
        })
        
        return f"Queue: {len(approved)} approved"
    
    def _show_pending(self, channel, thread_ts):
        """Show pending posts awaiting review."""
        pending = self.mgr.get_pending_posts()
        
        if not pending:
            msg = "📭 No pending posts awaiting review."
        else:
            lines = [f"📝 *Pending Posts — {len(pending)} awaiting review*"]
            lines.append("")
            for pid, rec in list(pending.items())[:15]:
                ptype = rec.get("post_type", "text")
                preview = (rec.get("content", "") or "")[:60].replace("\n", " ")
                lines.append(f"  • `{pid}` ({ptype}): {preview}...")
            if len(pending) > 15:
                lines.append(f"  ... and {len(pending) - 15} more")
            lines.append("")
            lines.append(f"_React with {EMOJI_APPROVE} to approve, {EMOJI_REJECT} to reject_")
            msg = "\n".join(lines)
        
        slack_api("chat.postMessage", {
            "channel": channel or CHANNEL,
            "text": msg,
            "thread_ts": thread_ts,
        })
        
        return f"Pending: {len(pending)}"
    
    def _show_help(self, channel, thread_ts):
        """Show available commands."""
        msg = (
            f"🤖 *AI Automation Coordinator — Help*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*Commands:*\n"
            f"  `@AI Coordinator publish` — Publish all approved posts to LinkedIn\n"
            f"  `@AI Coordinator reviewed all` — Same as publish\n"
            f"  `@AI Coordinator status` — Show approval queue status\n"
            f"  `@AI Coordinator queue` — Show approved posts ready to publish\n"
            f"  `@AI Coordinator pending` — Show posts awaiting review\n"
            f"  `@AI Coordinator dry run` — Preview what would be published\n"
            f"  `@AI Coordinator help` — Show this help message\n\n"
            f"*Reactions (on any post in #linkedin-content):*\n"
            f"  {EMOJI_APPROVE} — Approve post for publishing\n"
            f"  {EMOJI_REJECT} — Reject/Deny post\n"
            f"  {EMOJI_REVISE} — Request revision\n\n"
            f"*Workflow:*\n"
            f"  1. Posts are delivered to #linkedin-content with unique IDs\n"
            f"  2. Add {EMOJI_APPROVE} reaction to approve\n"
            f"  3. Say `@AI Coordinator publish` when ready\n"
            f"  4. I'll publish all approved posts and send a summary 🎉"
        )
        
        slack_api("chat.postMessage", {
            "channel": channel or CHANNEL,
            "text": msg,
            "thread_ts": thread_ts,
        })
        
        return "Help shown"


# ── HTTP Server ────────────────────────────────────────────────────────────

class SlackEventHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler for Slack Events API.
    
    Endpoints:
      POST /slack/events — Main Events API endpoint
      GET /health       — Health check
    """
    
    event_handler = EventHandler(dry_run=DRY_RUN)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        
        if parsed.path == "/health":
            self._send_json(200, {
                "status": "ok",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "dry_run": DRY_RUN,
            })
        else:
            self._send_json(404, {"error": "not_found"})
    
    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        
        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        request_body = self.rfile.read(content_length)
        
        # Verify Slack signature
        timestamp = self.headers.get("X-Slack-Request-Timestamp", "")
        signature = self.headers.get("X-Slack-Signature", "")
        
        if not verify_slack_signature(request_body, timestamp, signature):
            self._send_json(401, {"error": "invalid_signature"})
            return
        
        # Parse body
        try:
            payload = json.loads(request_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_json(400, {"error": f"invalid_json: {e}"})
            return
        
        # Route based on path
        if parsed.path == "/slack/events":
            self._handle_events_api(payload)
        else:
            self._send_json(404, {"error": "not_found"})
    
    def _handle_events_api(self, payload):
        """Handle Slack Events API payload."""
        event_type = payload.get("type", "")
        
        # URL Verification Challenge
        if event_type == "url_verification":
            challenge = payload.get("challenge", "")
            self._send_json(200, {"challenge": challenge})
            return
        
        # Event Callback
        if event_type == "event_callback":
            # Acknowledge immediately (Slack expects 200 within 3 seconds)
            self._send_json(200, {"ok": True})
            
            # Process the event asynchronously
            try:
                result = self.event_handler.handle_event(payload)
                print(f"[coordinator] Event processed: {result}")
            except Exception as e:
                print(f"[coordinator] Error processing event: {e}")
                import traceback
                traceback.print_exc()
        
        else:
            self._send_json(200, {"ok": True})
    
    def _send_json(self, status_code, data):
        """Send a JSON response."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        """Override default logging to use our format."""
        print(f"[http] {args[0]} {args[1]} {args[2]}")


# ── CLI / Server Entry Point ───────────────────────────────────────────────

def run_server():
    """Start the Slack Events API server."""
    server = HTTPServer(("0.0.0.0", PORT), SlackEventHandler)
    
    print(f"\n{'='*60}")
    print(f"  🤖 AI AUTOMATION COORDINATOR")
    print(f"{'='*60}")
    print(f"  Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print(f"  Server: http://0.0.0.0:{PORT}")
    print(f"  Endpoints:")
    print(f"    POST /slack/events  — Slack Events API")
    print(f"    GET  /health        — Health check")
    print(f"  Listening for reactions and mentions...")
    print(f"{'='*60}\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[coordinator] Server stopped by user.")
        server.server_close()


def simulate_mention(text):
    """Simulate an app_mention event (for testing)."""
    print(f"\n{'='*60}")
    print(f"  SIMULATING APP MENTION")
    print(f"{'='*60}")
    print(f"  Text: \"{text}\"\n")
    
    handler = EventHandler(dry_run=DRY_RUN)
    
    event = {
        "type": "app_mention",
        "text": text,
        "channel": CHANNEL,
        "user": "U_SIMULATED",
        "ts": str(time.time()),
    }
    
    result = handler.handle_event({"event": event})
    print(f"\n  Result: {result}")
    return result


def main():
    if "--publish-batch" in sys.argv:
        # One-time batch publish (no server)
        from linkedin_publisher import LinkedInPublisher, get_approved_content
        publisher = LinkedInPublisher()
        approved = get_approved_content()
        if approved:
            publisher.publish_batch(approved)
        else:
            print("📭 No approved posts to publish.")
        return
    
    if "--simulate-mention" in sys.argv:
        idx = sys.argv.index("--simulate-mention")
        if idx + 1 < len(sys.argv):
            text = sys.argv[idx + 1]
            simulate_mention(text)
        else:
            print("Usage: --simulate-mention <text>")
        return
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    
    # Default: Run the server
    run_server()


if __name__ == "__main__":
    main()
