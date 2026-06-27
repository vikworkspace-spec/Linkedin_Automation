#!/usr/bin/env python3
"""
approval_publish_gate.py — LinkedIn Publishing Gate (Phase 3)

Enforces that only approved posts get published to LinkedIn.
Acts as a gatekeeper between the approval system and the scheduling bots.

Key functions:
  - get_approved_content() — Returns only approved posts ready for publishing
  - verify_and_schedule() — Verifies approval before allowing scheduling
  - mark_published() — Marks posts as published after successful delivery
  - get_publish_queue() — Shows the full queue of approved posts

Usage:
  # List approved posts ready for publishing:
  python approval_publish_gate.py --queue

  # Verify a post before scheduling:
  python approval_publish_gate.py --verify <post_id>

  # Mark a post as published:
  python approval_publish_gate.py --published <post_id>

  # Export approved posts as JSON (for use by scheduling scripts):
  python approval_publish_gate.py --export > approved_posts.json

  # Generate approved posts file for scheduler consumption:
  python approval_publish_gate.py --generate-files
"""

import json
import os
import sys
import datetime
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from approval_lib import (
    ApprovalManager,
    APPROVAL_DATA_PATH,
    APPROVAL_AUDIT_PATH,
    PUBLISHED_LOG_PATH,
    EMOJI_APPROVE,
    EMOJI_PUBLISHED,
    slack_api,
    CHANNEL,
)


def get_approved_content():
    """
    Get all approved posts that are ready to be published.
    
    Returns:
        dict: {post_id: approval_record} — only posts with status 'approved'
    """
    mgr = ApprovalManager()
    mgr.cleanup_expired()
    
    approved = {}
    for pid, record in mgr.approvals.items():
        if record.get("status") == "approved":
            # Double-check expiry
            now = datetime.datetime.utcnow().isoformat() + "Z"
            if record.get("expires_at", "9999") > now:
                approved[pid] = record
    
    return approved


def verify_post_for_scheduling(post_id):
    """
    Verify that a post is approved and can be scheduled on LinkedIn.
    
    This is the main GATE function. Returns:
        (True, record) if post is approved
        (False, reason) if post is not approved
    
    Idempotency: If already published, returns False with reason.
    """
    mgr = ApprovalManager()
    record = mgr.get_post(post_id)
    
    if not record:
        return False, f"Post '{post_id}' not found in approval system"
    
    if record.get("status") == "published":
        return False, f"Post '{post_id}' was already published on {record.get('published_at')}"
    
    if record.get("status") == "rejected":
        return False, f"Post '{post_id}' was rejected"
    
    if record.get("status") == "pending":
        return False, f"Post '{post_id}' is still pending approval"
    
    if record.get("status") == "approved":
        # Check expiry
        now = datetime.datetime.utcnow().isoformat() + "Z"
        expires = record.get("expires_at", "9999")
        if expires <= now:
            return False, f"Post '{post_id}' approval has expired"
        return True, record
    
    return False, f"Post '{post_id}' has unknown status: {record.get('status')}"


def batch_verify(posts_list):
    """
    Verify multiple posts at once.
    
    Args:
        posts_list: List of post_id strings
    
    Returns:
        dict: {post_id: {"approved": bool, "record": dict|str}}
    """
    results = {}
    for pid in posts_list:
        ok, data = verify_post_for_scheduling(pid)
        results[pid] = {"approved": ok, "detail": data if ok else data}
    return results


def mark_as_published(post_id, scheduled_time=None):
    """
    Mark a post as published to LinkedIn.
    Should be called AFTER successful scheduling.
    
    Also sends a confirmation message to Slack.
    
    Args:
        post_id: The ID of the published post
        scheduled_time: Optional scheduled time string
    
    Returns:
        bool: True if successfully marked
    """
    mgr = ApprovalManager()
    result = mgr.mark_published(post_id)
    
    if result and scheduled_time:
        # Update the published_at with the actual scheduled time
        mgr.approvals[post_id]["scheduled_time"] = scheduled_time
        mgr._save()
    
    if result:
        # Notify Slack
        record = mgr.get_post(post_id)
        preview = (record.get("content", "") or "")[:150]
        msg = (
            f"{EMOJI_PUBLISHED} *Post Published to LinkedIn*\n"
            f"`{post_id}`\n"
            f"> {preview}...\n"
            f"_Scheduled: {scheduled_time or 'immediately'}_"
        )
        slack_api("chat.postMessage", {
            "channel": CHANNEL,
            "text": msg,
        })
        
        # Add published emoji reaction to the original post
        if record.get("slack_message_ts"):
            slack_api("reactions.add", {
                "channel": CHANNEL,
                "timestamp": record["slack_message_ts"],
                "name": "loudspeaker",
            })
    
    return result


def batch_publish(post_id_schedule_pairs):
    """
    Mark multiple posts as published in batch.
    
    Args:
        post_id_schedule_pairs: list of (post_id, scheduled_time) tuples
    
    Returns:
        (success_count, fail_count, errors)
    """
    success = 0
    fail = 0
    errors = []
    
    for pid, sched_time in post_id_schedule_pairs:
        if mark_as_published(pid, sched_time):
            success += 1
        else:
            fail += 1
            errors.append(pid)
    
    return success, fail, errors


def export_approved_posts():
    """
    Export all approved posts as a JSON-serializable dict.
    Useful for piping into scheduling scripts.
    """
    approved = get_approved_content()
    output = {}
    
    for pid, record in approved.items():
        output[pid] = {
            "post_id": pid,
            "content": record.get("content", ""),
            "post_type": record.get("post_type", "text"),
            "file_path": record.get("file_path"),
            "file_title": record.get("file_title"),
            "approved_at": record.get("approved_at"),
            "approved_by": record.get("approved_by"),
            "slack_message_ts": record.get("slack_message_ts"),
        }
    
    return output


def generate_scheduler_files():
    """
    Generate the files that scheduling scripts expect, but only for approved posts.
    This bridges the approval system with the existing scheduler pipeline.
    
    Creates:
      - approved_for_publishing.json: Full metadata for scheduling bots
      - linkedin_approved_posts.txt: Text file with approved posts (for compat)
    """
    approved = export_approved_posts()
    
    if not approved:
        print("[gate] No approved posts to generate files for.")
        return
    
    base = os.path.dirname(os.path.abspath(__file__))
    
    # Export full metadata as JSON
    json_path = os.path.join(base, "approved_for_publishing.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(approved, f, indent=2, ensure_ascii=False)
    print(f"[gate] ✅ Exported {len(approved)} approved posts to {json_path}")
    
    # For text-based scheduler compatibility, also extract just the content
    txt_path = os.path.join(base, "approved_posts_queue.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"APPROVED POSTS QUEUE — {datetime.date.today().isoformat()}\n")
        f.write(f"{'='*60}\n\n")
        for pid, rec in approved.items():
            f.write(f"--- {pid} ---\n")
            f.write(f"Type: {rec.get('post_type', 'text')}\n")
            f.write(f"Approved: {rec.get('approved_at')} by {rec.get('approved_by')}\n")
            f.write(f"\n{rec.get('content', '')}\n\n")
    print(f"[gate] ✅ Generated text queue at {txt_path}")


def show_publish_queue():
    """Display the current publish queue in a readable format."""
    approved = get_approved_content()
    
    print(f"{'='*60}")
    print(f"  APPROVED POSTS READY FOR PUBLISHING")
    print(f"{'='*60}")
    
    if not approved:
        print("\n  No approved posts waiting to publish.\n")
        print(f"  To approve posts, add {EMOJI_APPROVE} reaction in Slack or use")
        print("  /approve_post <post_id>")
        return
    
    print(f"\n  Total: {len(approved)} post(s) ready\n")
    
    for i, (pid, rec) in enumerate(approved.items(), 1):
        post_type = rec.get("post_type", "text")
        preview = (rec.get("content", "") or "")[:200].replace("\n", " ")
        file_info = ""
        if rec.get("file_path"):
            file_info = f"  📎 File: {rec.get('file_title', os.path.basename(rec['file_path']))}"
        
        print(f"  {i}. {pid}")
        print(f"     Type: {post_type} | Approved: {rec.get('approved_at', '?')[:10]}")
        print(f"     Preview: {preview}...")
        if file_info:
            print(file_info)
        print()


def integrate_with_scheduler(scheduler_post_list):
    """
    Integration helper: Filters a list of candidate post data to only include
    posts that have been approved.
    
    Args:
        scheduler_post_list: List of dicts with at least 'id' or 'post_id' key
    
    Returns:
        Filtered list with only approved posts
    """
    approved_ids = set(get_approved_content().keys())
    
    filtered = []
    skipped = []
    for post in scheduler_post_list:
        post_id = post.get("post_id") or post.get("id")
        if not post_id:
            # Generate a potential post_id from content to check
            skipped.append(post)
            continue
        
        # Check various formats
        candidates = [post_id]
        if isinstance(post_id, int):
            candidates.append(f"post_{post_id}")
        
        is_approved = any(c in approved_ids for c in candidates)
        
        if is_approved:
            filtered.append(post)
        else:
            skipped.append(post)
    
    if skipped:
        print(f"[gate] Skipped {len(skipped)} unapproved posts")
    
    return filtered


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python approval_publish_gate.py <command> [args]")
        print("Commands:")
        print("  --queue          Show approved posts ready for publishing")
        print("  --verify <id>    Verify if a specific post is approved")
        print("  --published <id> [time]  Mark a post as published")
        print("  --export         Export approved posts as JSON")
        print("  --generate-files Generate scheduler-compatible files")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "--queue":
        show_publish_queue()
    
    elif cmd == "--verify":
        if len(sys.argv) < 3:
            print("Usage: --verify <post_id>")
            return
        post_id = sys.argv[2]
        ok, detail = verify_post_for_scheduling(post_id)
        if ok:
            print(f"✅ Post '{post_id}' is APPROVED and ready for scheduling")
        else:
            print(f"❌ Post '{post_id}' is NOT approved: {detail}")
    
    elif cmd == "--published":
        if len(sys.argv) < 3:
            print("Usage: --published <post_id> [scheduled_time]")
            return
        post_id = sys.argv[2]
        sched_time = sys.argv[3] if len(sys.argv) > 3 else None
        if mark_as_published(post_id, sched_time):
            print(f"✅ Post '{post_id}' marked as published")
        else:
            print(f"❌ Failed to mark '{post_id}' as published")
    
    elif cmd == "--export":
        output = export_approved_posts()
        print(json.dumps(output, indent=2, ensure_ascii=False))
    
    elif cmd == "--generate-files":
        generate_scheduler_files()
    
    elif cmd == "--batch-verify":
        if len(sys.argv) < 3:
            print("Usage: --batch-verify <post_id1> <post_id2> ...")
            return
        posts = sys.argv[2:]
        results = batch_verify(posts)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
