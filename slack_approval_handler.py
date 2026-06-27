#!/usr/bin/env python3
"""
slack_approval_handler.py — Interactive Slack Approval UX (Phase 4)

Provides user-friendly approval workflows:
  1. Slash command handler for `/approve_post <post_id>`
  2. Interactive button response handler
  3. Bulk approval support
  4. Approval status feedback messages

This script is designed to be invoked in multiple ways:
  - Called from a Slack Events API server when a slash command is received
  - Run via CLI for manual approval actions
  - Used as a module by other scripts for programmatic access

Slack Slash Command Setup:
  In Slack API, create a slash command `/approve_post` pointing to:
  Any server that runs: python slack_approval_handler.py --slash-command

Usage:
  # Approve a specific post:
  python slack_approval_handler.py approve <post_id> [--user U123]

  # Reject a post:
  python slack_approval_handler.py reject <post_id> [--user U123]

  # Get status of a post:
  python slack_approval_handler.py status <post_id>

  # List all pending posts:
  python slack_approval_handler.py pending

  # Bulk approve all pending posts:
  python slack_approval_handler.py approve-all

  # Send approval confirmation as thread reply:
  python slack_approval_handler.py confirm <post_id>
"""

import json
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from approval_lib import (
    ApprovalManager,
    slack_api,
    CHANNEL,
    EMOJI_APPROVE,
    EMOJI_REJECT,
    EMOJI_REVISE,
    EMOJI_PUBLISHED,
    handle_slash_command,
)


# ── Interactive Message Blocks ─────────────────────────────────────────────

def build_approval_buttons(post_id, status="pending"):
    """
    Build a Slack Block Kit interactive button layout for approval actions.
    
    Returns a list of block dicts for use in chat.postMessage or chat.update.
    """
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📋 *Post `{post_id}`*\n*Current Status:* {status}\n\nWhat would you like to do?"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"{EMOJI_APPROVE} Approve", "emoji": True},
                    "style": "primary",
                    "value": f"approve_{post_id}",
                    "action_id": f"approve_post_{post_id}",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"{EMOJI_REJECT} Reject", "emoji": True},
                    "style": "danger",
                    "value": f"reject_{post_id}",
                    "action_id": f"reject_post_{post_id}",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"{EMOJI_REVISE} Revise", "emoji": True},
                    "value": f"revise_{post_id}",
                    "action_id": f"revise_post_{post_id}",
                },
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Post ID: `{post_id}` | Expires ~24h from posting"
                }
            ]
        }
    ]
    return blocks


def send_interactive_approval_message(post_id, content_preview="", thread_ts=None):
    """
    Send an interactive message with approval buttons to Slack.
    
    Args:
        post_id: The post ID
        content_preview: Short preview of the post content
        thread_ts: Optional thread timestamp to reply in thread
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📋 Pending Approval: {post_id}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Post ID:* `{post_id}`\n*Status:* ⏳ Pending Review\n\n>{content_preview[:300]}..."
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"{EMOJI_APPROVE} Approve", "emoji": True},
                    "style": "primary",
                    "value": f"approve_{post_id}",
                    "action_id": "approve_action",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"{EMOJI_REJECT} Reject", "emoji": True},
                    "style": "danger",
                    "value": f"reject_{post_id}",
                    "action_id": "reject_action",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"{EMOJI_REVISE} Revise", "emoji": True},
                    "value": f"revise_{post_id}",
                    "action_id": "revise_action",
                },
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Or use `/approve_post {post_id}`"
                }
            ]
        }
    ]
    
    payload = {
        "channel": CHANNEL,
        "blocks": blocks,
        "text": f"Pending Approval: {post_id}",
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts
    
    result = slack_api("chat.postMessage", payload)
    return result.get("ok"), result.get("ts")


def send_status_update(post_id, action="approved", user=None):
    """
    Send a status update message as a thread reply to the original post.
    
    Args:
        post_id: The post ID that was acted upon
        action: 'approved', 'rejected', 'revise', 'published'
        user: Slack user ID who performed the action
    """
    mgr = ApprovalManager()
    record = mgr.get_post(post_id)
    if not record:
        return False
    
    ts = record.get("slack_message_ts")
    if not ts:
        return False
    
    action_messages = {
        "approved": (
            f"{EMOJI_APPROVE} *Approved!*\n"
            f"This post has been approved{' by <@' + user + '>' if user else ''} "
            f"and is now queued for LinkedIn publishing."
        ),
        "rejected": (
            f"{EMOJI_REJECT} *Rejected*\n"
            f"This post has been rejected{' by <@' + user + '>' if user else ''} "
            f"and will not be published."
        ),
        "revise": (
            f"{EMOJI_REVISE} *Revision Requested*\n"
            f"Changes requested{' by <@' + user + '>' if user else ''}. "
            f"A new version will need to be submitted."
        ),
        "published": (
            f"{EMOJI_PUBLISHED} *Published to LinkedIn!*\n"
            f"This post has been successfully published."
        ),
        "pending": (
            f"📝 *Status Reset to Pending*\n"
            f"This post has been returned to the pending queue."
        ),
    }
    
    msg = action_messages.get(action, f"Status updated to: {action}")
    
    result = slack_api("chat.postMessage", {
        "channel": CHANNEL,
        "text": msg,
        "thread_ts": ts,
    })
    
    return result.get("ok")


# ── Bulk Operations ────────────────────────────────────────────────────────

def bulk_approve_all(approver="bulk_command"):
    """
    Approve all pending posts that haven't expired.
    
    Returns: (approved_count, errors)
    """
    mgr = ApprovalManager()
    pending = mgr.get_pending_posts()
    
    approved = 0
    errors = []
    
    for post_id in pending:
        try:
            if mgr.mark_approved(post_id, approved_by=approver):
                approved += 1
                send_status_update(post_id, "approved", user=approver)
        except Exception as e:
            errors.append((post_id, str(e)))
    
    return approved, errors


def bulk_approve_by_ids(post_ids, approver="bulk_command"):
    """
    Approve specific posts by their IDs.
    
    Returns: (approved_count, errors)
    """
    mgr = ApprovalManager()
    approved = 0
    errors = []
    
    for post_id in post_ids:
        try:
            if mgr.mark_approved(post_id, approved_by=approver):
                approved += 1
                send_status_update(post_id, "approved", user=approver)
            else:
                record = mgr.get_post(post_id)
                if record:
                    errors.append((post_id, f"Current status: {record.get('status')}"))
                else:
                    errors.append((post_id, "Not found"))
        except Exception as e:
            errors.append((post_id, str(e)))
    
    return approved, errors


# ── Slash Command Simulator ────────────────────────────────────────────────

def handle_slash_command_input(post_id, user_id=None, command_text=""):
    """
    Handle slash command input like `/approve_post <post_id>`.
    
    Supports:
      /approve_post <post_id>          — Approve a post
      /approve_post --status <id>      — Check status
      /approve_post --reject <id>      — Reject
      /approve_post --revise <id>      — Request revision
      /approve_post --list             — List pending
      /approve_post --approve-all      — Bulk approve all pending
    
    Returns: Response text to display to the user
    """
    parts = command_text.strip().split()
    if not parts:
        return (
            f"Usage: `/approve_post <post_id>`\n"
            f"  `/approve_post --status <post_id>` — Check status\n"
            f"  `/approve_post --reject <post_id>` — Reject\n"
            f"  `/approve_post --revise <post_id>` — Request revision\n"
            f"  `/approve_post --list` — List pending posts\n"
            f"  `/approve_post --approve-all` — Approve all pending"
        )
    
    subcmd = parts[0]
    
    if subcmd == "--list":
        mgr = ApprovalManager()
        pending = mgr.get_pending_posts()
        if not pending:
            return "📭 No pending posts awaiting approval."
        lines = [f"📝 *{len(pending)} Pending Posts:*"]
        for pid, rec in pending.items():
            preview = (rec.get("content", "") or "")[:100].replace("\n", " ")
            ptype = rec.get("post_type", "text")
            created = rec.get("created_at", "?")[:10]
            lines.append(f"  • `{pid}` ({ptype}) — {created}: {preview}...")
        return "\n".join(lines)
    
    elif subcmd == "--approve-all":
        count, errors = bulk_approve_all(approver=user_id or "slash_command")
        summary = f"✅ Bulk approved {count} posts."
        if errors:
            summary += f"\n⚠️ {len(errors)} errors: {', '.join(e[0] for e in errors[:5])}"
        return summary
    
    elif subcmd == "--status":
        if len(parts) < 2:
            return "Usage: `/approve_post --status <post_id>`"
        return handle_slash_command(parts[1], "status", user_id)
    
    elif subcmd == "--reject":
        if len(parts) < 2:
            return "Usage: `/approve_post --reject <post_id>`"
        result = handle_slash_command(parts[1], "reject", user_id)
        send_status_update(parts[1], "rejected", user=user_id)
        return result
    
    elif subcmd == "--revise":
        if len(parts) < 2:
            return "Usage: `/approve_post --revise <post_id>`"
        result = handle_slash_command(parts[1], "revise", user_id)
        send_status_update(parts[1], "revise", user=user_id)
        return result
    
    else:
        # Default: approve the post
        post_id = subcmd
        result = handle_slash_command(post_id, "approve", user_id)
        send_status_update(post_id, "approved", user=user_id)
        return result


# ── Interactive Button Handler ─────────────────────────────────────────────

def handle_interactive_button(payload):
    """
    Handle interactive button clicks from Slack Block Kit.
    
    This would be called from a Slack Events API endpoint receiving
    interactive payloads. For CLI-only mode, we simulate this.
    
    Args:
        payload: Dict from Slack's interactive endpoint
    
    Returns:
        Response dict to send back to Slack
    """
    actions = payload.get("actions", [])
    if not actions:
        return {"text": "No actions found"}
    
    action = actions[0]
    action_id = action.get("action_id", "")
    value = action.get("value", "")
    user = payload.get("user", {}).get("id", "unknown")
    
    # Parse action: approve_post_XXX, reject_post_XXX, revise_post_XXX
    if "_post_" in action_id:
        parts = action_id.split("_post_", 1)
        if len(parts) == 2:
            verb = parts[0]
            post_id = parts[1]
            
            if verb == "approve":
                msg = handle_slash_command(post_id, "approve", user)
                send_status_update(post_id, "approved", user=user)
                return {
                    "response_type": "in_channel",
                    "text": f"{EMOJI_APPROVE} Post `{post_id}` approved by <@{user}>",
                }
            elif verb == "reject":
                msg = handle_slash_command(post_id, "reject", user)
                send_status_update(post_id, "rejected", user=user)
                return {
                    "response_type": "in_channel",
                    "text": f"{EMOJI_REJECT} Post `{post_id}` rejected by <@{user}>",
                }
            elif verb == "revise":
                msg = handle_slash_command(post_id, "revise", user)
                send_status_update(post_id, "revise", user=user)
                return {
                    "response_type": "in_channel",
                    "text": f"{EMOJI_REVISE} Post `{post_id}` revision requested by <@{user}>",
                }
    
    return {"text": "Unknown action"}


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "approve":
        post_id = sys.argv[2] if len(sys.argv) > 2 else None
        user = None
        for i, arg in enumerate(sys.argv):
            if arg == "--user" and i + 1 < len(sys.argv):
                user = sys.argv[i + 1]
        
        if not post_id:
            print("Usage: python slack_approval_handler.py approve <post_id> [--user U123]")
            return
        
        result = handle_slash_command(post_id, "approve", user)
        print(result)
        send_status_update(post_id, "approved", user=user)
    
    elif cmd == "reject":
        post_id = sys.argv[2] if len(sys.argv) > 2 else None
        user = None
        for i, arg in enumerate(sys.argv):
            if arg == "--user" and i + 1 < len(sys.argv):
                user = sys.argv[i + 1]
        
        if not post_id:
            print("Usage: python slack_approval_handler.py reject <post_id> [--user U123]")
            return
        
        result = handle_slash_command(post_id, "reject", user)
        print(result)
        send_status_update(post_id, "rejected", user=user)
    
    elif cmd == "status":
        post_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not post_id:
            print("Usage: python slack_approval_handler.py status <post_id>")
            return
        result = handle_slash_command(post_id, "status")
        print(result)
    
    elif cmd == "pending":
        mgr = ApprovalManager()
        pending = mgr.get_pending_posts()
        if not pending:
            print("📭 No pending posts.")
            return
        print(f"📝 {len(pending)} Pending Posts:\n")
        for pid, rec in pending.items():
            preview = (rec.get("content", "") or "")[:100].replace("\n", " ")
            ptype = rec.get("post_type", "text")
            print(f"  • `{pid}` ({ptype}): {preview}...")
    
    elif cmd == "approve-all":
        user = None
        for i, arg in enumerate(sys.argv):
            if arg == "--user" and i + 1 < len(sys.argv):
                user = sys.argv[i + 1]
        
        count, errors = bulk_approve_all(approver=user or "cli")
        print(f"✅ Bulk approved {count} posts.")
        if errors:
            print(f"⚠️ {len(errors)} errors occurred.")
    
    elif cmd == "confirm":
        post_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not post_id:
            print("Usage: python slack_approval_handler.py confirm <post_id>")
            return
        send_status_update(post_id, "published")
        print(f"📢 Sent published confirmation for {post_id}")
    
    elif cmd == "--slash-command":
        # Simulate slash command input
        user_id = None
        for i, arg in enumerate(sys.argv):
            if arg == "--user" and i + 1 < len(sys.argv):
                user_id = sys.argv[i + 1]
        
        # Read command text from stdin or args
        if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
            command_text = " ".join(sys.argv[2:])
        else:
            command_text = sys.stdin.read().strip()
        
        response = handle_slash_command_input(command_text, user_id)
        print(response)
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
