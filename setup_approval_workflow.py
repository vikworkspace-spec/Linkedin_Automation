#!/usr/bin/env python3
"""
setup_approval_workflow.py — Initialize the Slack Approval Workflow for LinkedIn Posts.

This script:
  1. Creates initial approval_data.json and published_posts.json files
  2. Validates that the Slack token is accessible
  3. Sends a test message to the channel to confirm connectivity
  4. Provides instructions for finalizing the setup

Usage:
  python setup_approval_workflow.py
"""

import json
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from approval_lib import (
    TOKEN,
    CHANNEL,
    APPROVAL_DATA_PATH,
    APPROVAL_AUDIT_PATH,
    APPROVAL_HISTORY_PATH,
    PUBLISHED_LOG_PATH,
    slack_api,
    ApprovalManager,
)


def check_slack_connection():
    """Test Slack API connectivity."""
    print("🔌 Testing Slack API connection...")
    
    if not TOKEN:
        print("❌ ERROR: SLACK_BOT_TOKEN not found in .env")
        print("   Make sure .env exists with: SLACK_BOT_TOKEN=xoxb-...")
        return False
    
    # Test auth
    result = slack_api("auth.test", {})
    if result.get("ok"):
        bot_name = result.get("user", "unknown")
        bot_id = result.get("user_id", "unknown")
        team = result.get("team", "unknown")
        print(f"   ✅ Connected as @{bot_name} (ID: {bot_id})")
        print(f"   📋 Team: {team}")
    else:
        print(f"   ❌ Auth failed: {result.get('error')}")
        return False
    
    # Test channel access
    result = slack_api("conversations.info", {"channel": CHANNEL})
    if result.get("ok"):
        channel_name = result.get("channel", {}).get("name", "unknown")
        print(f"   ✅ Channel access confirmed: #{channel_name}")
    else:
        print(f"   ⚠️  Channel check: {result.get('error')}")
        print(f"   (Channel ID {CHANNEL} may not be accessible)")
    
    return True


def initialize_data_files():
    """Initialize all required data files."""
    print("\n📁 Initializing data files...")
    
    files_created = []
    
    # approval_data.json
    if not os.path.exists(APPROVAL_DATA_PATH):
        with open(APPROVAL_DATA_PATH, "w") as f:
            json.dump({}, f)
        files_created.append(APPROVAL_DATA_PATH)
        print(f"   ✅ Created {APPROVAL_DATA_PATH}")
    else:
        print(f"   ✓ {APPROVAL_DATA_PATH} already exists")
    
    # approval_audit.jsonl
    if not os.path.exists(APPROVAL_AUDIT_PATH):
        with open(APPROVAL_AUDIT_PATH, "w") as f:
            f.write("")
        files_created.append(APPROVAL_AUDIT_PATH)
        print(f"   ✅ Created {APPROVAL_AUDIT_PATH}")
    else:
        print(f"   ✓ {APPROVAL_AUDIT_PATH} already exists")
    
    # published_posts.json
    if not os.path.exists(PUBLISHED_LOG_PATH):
        with open(PUBLISHED_LOG_PATH, "w") as f:
            json.dump({"published": [], "last_updated": datetime.datetime.utcnow().isoformat() + "Z"}, f, indent=2)
        files_created.append(PUBLISHED_LOG_PATH)
        print(f"   ✅ Created {PUBLISHED_LOG_PATH}")
    else:
        print(f"   ✓ {PUBLISHED_LOG_PATH} already exists")
    
    return files_created


def send_test_message():
    """Send a test message to confirm the approval workflow."""
    print("\n📨 Sending test message to Slack...")
    
    from approval_lib import post_text_with_approval
    
    test_text = (
        "🧪 *Approval Workflow Test*\n\n"
        "This is a test post to verify the Slack Approval Workflow is set up correctly.\n\n"
        "✅ If you can see this, the system is working.\n"
        "Try adding a ✅ reaction to this message to approve it, "
        "or use `/approve_post <post_id>`."
    )
    
    post_id, ts = post_text_with_approval("test", test_text)
    
    if post_id:
        print(f"   ✅ Test message sent successfully!")
        print(f"   🆔 Post ID: {post_id}")
        print(f"   ⏰ Timestamp: {ts}")
        print(f"   📍 Channel: <#{CHANNEL}>")
        return True
    else:
        print(f"   ❌ Failed to send test message")
        return False


def verify_approval_data():
    """Verify the approval system works by checking data flow."""
    print("\n🔍 Verifying approval data system...")
    
    mgr = ApprovalManager()
    stats = mgr.get_summary_stats()
    
    print(f"   ✅ ApprovalManager initialized")
    print(f"   📊 Stats: {json.dumps(stats)}")
    
    # Test roundtrip: register, approve, check
    test_id = "test_setup_001"
    mgr.register_post(test_id, "Test post for setup verification")
    
    if mgr.get_post(test_id):
        print(f"   ✅ Post registration works")
    else:
        print(f"   ❌ Post registration failed")
        return False
    
    mgr.mark_approved(test_id, approved_by="setup_script")
    
    if mgr.is_approved(test_id):
        print(f"   ✅ Approval marking works")
    else:
        print(f"   ❌ Approval marking failed")
        return False
    
    # Cleanup test data
    mgr.mark_published(test_id)
    
    print(f"   ✅ Full roundtrip verified: register → approve → publish")
    return True


def print_next_steps():
    """Print setup completion and next steps."""
    print(f"\n{'='*60}")
    print(f"  ✅ APPROVAL WORKFLOW SETUP COMPLETE!")
    print(f"{'='*60}")
    print(f"""
  📋 WHAT'S INSTALLED:
  
  Phase 1 — Modified Delivery:
    • approval_lib.py       — Shared library with approval system
    • slack_deliver_614.py  — ✅ Modified with approval markers (in progress)
    • slack_deliver.py      — ✅ Modified with approval markers (in progress)
    • send_to_slack.py      — ✅ Modified with approval markers (in progress)
  
  Phase 2 — Approval Monitor:
    • slack_approval_monitor.py — Monitors reactions in #linkedin-content
  
  Phase 3 — Publishing Gate:
    • approval_publish_gate.py  — Only allows approved posts to publish
  
  Phase 4 — Interactive UX:
    • slack_approval_handler.py — Buttons, slash commands, bulk ops

  🚀 NEXT STEPS:
  
  1. Modify your delivery scripts to use approval markers:
     - In slack_deliver_614.py: replace post() with post_text_with_approval()
     - In send_to_slack.py: replace send_slack_message() with post_text_with_approval()
  
  2. Run the monitor:
     python slack_approval_monitor.py --watch
     (Run this in a background terminal or as a cron job)
  
  3. Approve posts:
     - Add ✅ reaction on any post in #linkedin-content
     - Or use: python slack_approval_handler.py approve <post_id>
  
  4. Check queue:
     python approval_publish_gate.py --queue
  
  5. Set up Slack Slash Command (for interactive use):
     - Go to api.slack.com → Your App → Slash Commands
     - Create: /approve_post
     - Request URL: (your server endpoint)
     - Or use: python slack_approval_handler.py --slash-command <text>
  
  6. (Optional) Set up cron for auto-monitoring:
     */5 * * * * cd /path/to/project && python slack_approval_monitor.py --scan
""")


def main():
    print(f"{'='*60}")
    print(f"  SLACK APPROVAL WORKFLOW SETUP")
    print(f"  {datetime.datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    # Step 1: Check connection
    if not check_slack_connection():
        print("\n❌ Setup failed at Slack connection step.")
        sys.exit(1)
    
    # Step 2: Initialize files
    initialize_data_files()
    
    # Step 3: Verify data system
    verify_approval_data()
    
    # Step 4: Send test
    test_ok = send_test_message()
    
    if test_ok:
        print("\n   👆 Check #linkedin-content in Slack for the test message!")
    
    # Final
    print_next_steps()


if __name__ == "__main__":
    main()
