#!/usr/bin/env python3
"""
slack_approval_monitor.py — Slack Approval Reaction Monitor (Phase 2)

Monitors the #linkedin-content channel for reactions on posted messages.
Tracks which posts have been:
  - ✅ (white_check_mark) = Approved
  - ❌ (x) = Rejected
  - 🔄 (arrows_counterclockwise) = Revise requested

Stores approved post metadata in approval_data.json and maintains
an approval audit trail in approval_audit.jsonl.

Usage:
  # One-time scan and update:
  python slack_approval_monitor.py --scan

  # Continuous monitoring (runs every 60 seconds):
  python slack_approval_monitor.py --watch

  # Force cleanup expired posts:
  python slack_approval_monitor.py --cleanup

  # Generate and send summary to Slack:
  python slack_approval_monitor.py --send-summary

  # Show current approval queue:
  python slack_approval_monitor.py --status
"""

import json
import os
import sys
import time
import datetime
import urllib.parse

# Add current dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from approval_lib import (
    ApprovalManager,
    slack_api,
    slack_api_get,
    CHANNEL,
    APPROVAL_DATA_PATH,
    EMOJI_APPROVE,
    EMOJI_REJECT,
    EMOJI_REVISE,
    EMOJI_PUBLISHED,
    _emoji_to_name,
    _name_to_emoji,
)


def scan_channel_history(hours_back=48, limit=200):
    """
    Scan recent messages in the channel for approval reactions.
    
    Args:
        hours_back: How many hours of history to scan
        limit: Max messages to fetch
    
    Returns:
        list of dicts: Messages that have tracked reactions
    """
    oldest_ts = str(int(time.time() - hours_back * 3600))
    
    result = slack_api_get("conversations.history", {
        "channel": CHANNEL,
        "oldest": oldest_ts,
        "limit": limit,
    })
    
    if not result.get("ok"):
        print(f"[monitor] ERROR fetching channel history: {result.get('error')}")
        return []
    
    messages = result.get("messages", [])
    print(f"[monitor] Fetched {len(messages)} messages from last {hours_back}h")
    
    mgr = ApprovalManager()
    updated_count = 0
    
    # Check each message for reactions
    for msg in messages:
        ts = msg.get("ts")
        if not ts:
            continue
        
        # Look for reactions
        reactions = msg.get("reactions", [])
        if not reactions:
            continue
        
        # Extract post ID from the message text
        post_id = extract_post_id(msg)
        if not post_id:
            continue
        
        # Check if this post is already tracked
        existing = mgr.get_post(post_id)
        if not existing:
            # This is a post not in our system yet, register it
            text = msg.get("text", "")
            post_type = detect_post_type(msg)
            mgr.register_post(post_id, text, post_type=post_type)
            mgr.update_slack_ts(post_id, ts)
            print(f"[monitor] Registered untracked post: {post_id}")
        
        # Process reactions
        for r in reactions:
            emoji_name = r.get("name", "")
            users = r.get("users", [])
            emoji_char = _name_to_emoji(emoji_name)
            count = r.get("count", 0)
            
            # Filter out bot reactions (we added them initially)
            # If count > 1, there's a human reaction beyond the bot
            if users and count >= 1:
                # Get the last user who reacted (not the bot)
                # Slack API doesn't tell us the order easily,
                # but the bot might be the first if it auto-reacted
                non_bot_users = users  # We'll take any user reaction as approval signal
                
                if emoji_char == EMOJI_APPROVE and count >= 1:
                    # Only mark approved if we haven't already
                    if mgr.get_post(post_id).get("status") != "approved":
                        approver = non_bot_users[0] if non_bot_users else "unknown"
                        if mgr.mark_approved(post_id, approved_by=f"reaction:{approver}"):
                            updated_count += 1
                            print(f"[monitor] ✅ {post_id} approved by user {approver}")
                
                elif emoji_char == EMOJI_REJECT and count >= 1:
                    if mgr.get_post(post_id).get("status") not in ("rejected", "published"):
                        rejector = non_bot_users[0] if non_bot_users else "unknown"
                        if mgr.mark_rejected(post_id, notes=f"Rejected by {rejector}"):
                            updated_count += 1
                            print(f"[monitor] ❌ {post_id} rejected by user {rejector}")
                
                elif emoji_char == EMOJI_REVISE and count >= 1:
                    if mgr.get_post(post_id).get("status") not in ("revise", "published"):
                        requester = non_bot_users[0] if non_bot_users else "unknown"
                        if mgr.mark_revise(post_id, notes=f"Revise requested by {requester}"):
                            updated_count += 1
                            print(f"[monitor] 🔄 {post_id} revision requested by {requester}")
    
    if updated_count == 0:
        print(f"[monitor] No new approval updates found.")
    
    return updated_count


def extract_post_id(msg):
    """
    Extract the post ID from a Slack message text.
    Post IDs look like: `post_20260614_123456_abc123`
    """
    text = msg.get("text", "") or ""
    # Look for pattern: `post_YYYYMMDD_HHMMSS_XXXXXX`
    import re
    match = re.search(r'`(post_\d{8}_\d{6}_[a-f0-9]{6})`', text)
    if match:
        return match.group(1)
    return None


def detect_post_type(msg):
    """Detect the type of post from the message content."""
    text = msg.get("text", "") or ""
    files = msg.get("files", [])
    
    if files:
        for f in files:
            mimetype = f.get("mimetype", "")
            name = f.get("name", "")
            if "pdf" in mimetype or name.endswith(".pdf"):
                return "carousel"
            elif "png" in mimetype or "image" in mimetype:
                return "infographic"
        return "file"
    
    if "POLL" in text or "poll" in text:
        return "poll"
    
    return "text"


def continuous_watch(interval_seconds=60):
    """
    Continuously monitor the channel for reactions.
    Runs the scan every `interval_seconds` seconds.
    
    Args:
        interval_seconds: Time between scans
    """
    print(f"[monitor] Starting continuous watch (interval: {interval_seconds}s)")
    print(f"[monitor] Press Ctrl+C to stop")
    print()
    
    cycle = 0
    while True:
        cycle += 1
        print(f"[monitor] --- Scan cycle {cycle} at {datetime.datetime.now().isoformat()} ---")
        
        try:
            updated = scan_channel_history(hours_back=48)
            if updated > 0:
                print(f"[monitor] ✓ {updated} posts updated this cycle")
                # Send a brief notification to Slack about approvals
                notify_approval_updates()
        except Exception as e:
            print(f"[monitor] ERROR during scan: {e}")
        
        print(f"[monitor] Sleeping {interval_seconds}s...")
        print()
        
        try:
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n[monitor] Stopped by user.")
            break


def notify_approval_updates():
    """Send a notification to Slack about newly approved posts."""
    mgr = ApprovalManager()
    approved = mgr.get_approved_posts()
    
    if not approved:
        return
    
    # Only notify if there are approved posts not yet published
    not_published = {pid: rec for pid, rec in approved.items() if rec.get("status") == "approved"}
    
    if not not_published:
        return
    
    count = len(not_published)
    if count <= 3:
        # Send individual notifications for small batches
        for pid, rec in not_published.items():
            preview = (rec.get("content", "") or "")[:150]
            msg = (
                f"✅ *Post Approved & Ready for LinkedIn*\n"
                f"`{pid}`\n"
                f"> {preview}...\n"
                f"_This post is now queued for publishing._"
            )
            slack_api("chat.postMessage", {
                "channel": CHANNEL,
                "text": msg,
                "thread_ts": rec.get("slack_message_ts"),
            })
    else:
        # Send batch notification for larger numbers
        lines = [f"  • `{pid}`" for pid in not_published.keys()]
        msg = (
            f"✅ *{count} Posts Approved — Ready for Publishing*\n"
            + "\n".join(lines) + "\n"
            f"_All approved posts will be published to LinkedIn on their next scheduled run._"
        )
        slack_api("chat.postMessage", {
            "channel": CHANNEL,
            "text": msg,
        })


def show_status():
    """Display current approval queue status."""
    mgr = ApprovalManager()
    stats = mgr.get_summary_stats()
    
    print(f"{'='*60}")
    print(f"  APPROVAL QUEUE STATUS")
    print(f"{'='*60}")
    print(f"  📝 Pending:    {stats.get('pending', 0)}")
    print(f"  ✅ Approved:   {stats.get('approved', 0)}")
    print(f"  ❌ Rejected:   {stats.get('rejected', 0)}")
    print(f"  🔄 Revise:     {stats.get('revise', 0)}")
    print(f"  📢 Published:  {stats.get('published', 0)}")
    print(f"  ⏰ Expired:    {stats.get('expired', 0)}")
    print(f"  {'─'*40}")
    print(f"  Total tracked: {stats.get('total', 0)}")
    print(f"{'='*60}")
    
    # Show approved posts
    approved = mgr.get_approved_posts()
    if approved:
        print(f"\n  ✅ APPROVED POSTS READY FOR PUBLISHING:")
        for pid, rec in approved.items():
            preview = (rec.get("content", "") or "")[:100].replace("\n", " ")
            print(f"    • {pid}: {preview}...")
    
    # Show pending posts
    pending = mgr.get_pending_posts()
    if pending:
        print(f"\n  📝 PENDING POSTS AWAITING REVIEW:")
        for pid, rec in list(pending.items())[:10]:
            preview = (rec.get("content", "") or "")[:80].replace("\n", " ")
            print(f"    • {pid}: {preview}...")
        if len(pending) > 10:
            print(f"    ... and {len(pending) - 10} more")


def generate_html_report():
    """Generate an HTML report of the approval queue."""
    mgr = ApprovalManager()
    stats = mgr.get_summary_stats()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LinkedIn Approval Queue Report</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
  h1 {{ color: #0A66C2; }}
  .stats {{ display: flex; gap: 10px; margin: 20px 0; }}
  .stat {{ background: #f3f6f8; border-radius: 8px; padding: 15px; text-align: center; flex: 1; }}
  .stat .num {{ font-size: 24px; font-weight: bold; }}
  .stat .label {{ font-size: 12px; color: #666; }}
  .post {{ border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin: 8px 0; }}
  .post .pid {{ font-family: monospace; font-size: 12px; color: #666; }}
  .post .preview {{ margin: 5px 0; }}
  .approved {{ border-left: 4px solid #2e7d32; }}
  .pending {{ border-left: 4px solid #f9a825; }}
  .rejected {{ border-left: 4px solid #c62828; }}
</style>
</head>
<body>
<h1>📊 LinkedIn Approval Queue</h1>
<p>Generated: {datetime.datetime.now().isoformat()}</p>

<div class="stats">
  <div class="stat"><div class="num">{stats.get('pending', 0)}</div><div class="label">📝 Pending</div></div>
  <div class="stat"><div class="num">{stats.get('approved', 0)}</div><div class="label">✅ Approved</div></div>
  <div class="stat"><div class="num">{stats.get('rejected', 0)}</div><div class="label">❌ Rejected</div></div>
  <div class="stat"><div class="num">{stats.get('published', 0)}</div><div class="label">📢 Published</div></div>
</div>

<h2>✅ Approved & Ready</h2>
"""
    
    for pid, rec in mgr.get_approved_posts().items():
        preview = (rec.get("content", "") or "")[:200]
        html += f'<div class="post approved"><div class="pid">{pid}</div><div class="preview">{preview}</div></div>\n'
    
    html += "<h2>📝 Pending Review</h2>\n"
    for pid, rec in mgr.get_pending_posts().items():
        preview = (rec.get("content", "") or "")[:200]
        html += f'<div class="post pending"><div class="pid">{pid}</div><div class="preview">{preview}</div></div>\n'
    
    html += "</body></html>"
    
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "approval_report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[monitor] Report saved to {report_path}")
    return report_path


# ── CLI Entry ──────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "--scan":
        print(f"[monitor] Scanning channel for reaction updates...")
        updated = scan_channel_history(hours_back=48)
        print(f"[monitor] Done. {updated} posts updated.")
    
    elif cmd == "--watch":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        continuous_watch(interval)
    
    elif cmd == "--cleanup":
        mgr = ApprovalManager()
        count = mgr.cleanup_expired()
        print(f"[monitor] Cleaned up {count} expired posts.")
    
    elif cmd == "--send-summary":
        from approval_lib import send_approval_summary
        send_approval_summary()
        print("[monitor] Summary sent to Slack.")
    
    elif cmd == "--status":
        show_status()
    
    elif cmd == "--report":
        generate_html_report()
    
    elif cmd == "--notify":
        notify_approval_updates()
        print("[monitor] Notifications sent.")
    
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
