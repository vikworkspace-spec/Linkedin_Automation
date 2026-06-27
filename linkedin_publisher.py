#!/usr/bin/env python3
"""
linkedin_publisher.py — LinkedIn Browser Automation Publisher

Publishes content to LinkedIn using Puppeteer + Chrome CDP.

Uses `type_post.cjs` which:
  1. Connects to Chrome running on port 9222
  2. Finds the LinkedIn feed editor in shadow DOM
  3. Types the post text

Requirements:
  - Chrome running with remote debugging on port 9222
    chrome.exe --remote-debugging-port=9222
  - LinkedIn logged in and feed page open in that Chrome
  - Node.js and puppeteer-core installed

Integrates with the approval system to:
  - Read approved posts from approval_data.json
  - Publish them via Puppeteer
  - Mark them as published after successful delivery

Usage:
  python linkedin_publisher.py --publish-batch    # Publish ALL approved
  python linkedin_publisher.py --queue            # Show approval queue
  python linkedin_publisher.py --check            # Check prerequisites
"""

import json
import os
import sys
import time
import subprocess
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Import approval lib for state management
sys.path.insert(0, BASE_DIR)
try:
    from approval_lib import (
        ApprovalManager,
        slack_api,
        CHANNEL,
        EMOJI_PUBLISHED,
    )
except ImportError as e:
    print(f"[linkedin_publisher] WARNING: Could not import approval_lib: {e}")
    ApprovalManager = None
    slack_api = None
    CHANNEL = None
    EMOJI_PUBLISHED = "\U0001f4e2"


# ── Browser Automation Publisher ───────────────────────────────────────────

class LinkedInPublisher:
    """
    Publishes content to LinkedIn using Puppeteer + Chrome CDP.

    Uses the proven `type_post.cjs` script which:
      1. Connects to Chrome on port 9222
      2. Finds the LinkedIn feed editor in shadow DOM
      3. Types the post text character by character
    """

    def __init__(self):
        self.script_path = os.path.join(BASE_DIR, "publish_post.cjs")
        self.fallback_script = os.path.join(BASE_DIR, "type_post.cjs")
        self.available = False
        self._check_prerequisites()

    def _check_prerequisites(self):
        """Check all prerequisites are available."""
        checks_passed = True

        # 1. publish_post.cjs (or fallback type_post.cjs) exists
        if os.path.exists(self.script_path):
            print(f"[linkedin_publisher] publish_post.cjs found")
        elif os.path.exists(self.fallback_script):
            self.script_path = self.fallback_script
            print(f"[linkedin_publisher] Using type_post.cjs (fallback)")
        else:
            print(f"[linkedin_publisher] Neither publish_post.cjs nor type_post.cjs found")
            checks_passed = False

        # 2. Node.js is available
        try:
            result = subprocess.run(["node", "--version"],
                capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"[linkedin_publisher] Node.js {result.stdout.strip()}")
            else:
                print(f"[linkedin_publisher] Node.js not responding")
                checks_passed = False
        except FileNotFoundError:
            print(f"[linkedin_publisher] Node.js not found in PATH")
            checks_passed = False

        # 3. Chrome is running on port 9222
        try:
            req = urllib.request.Request("http://127.0.0.1:9222/json/version")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                chrome_ver = data.get("Browser", "unknown")
                print(f"[linkedin_publisher] Chrome running (port 9222) - {chrome_ver}")
        except Exception as e:
            print(f"[linkedin_publisher] Chrome not found on port 9222: {e}")
            print(f"[linkedin_publisher]    Start Chrome with:")
            print(f"    chrome.exe --remote-debugging-port=9222")
            print(f"    Then log into LinkedIn and open the feed page.")
            checks_passed = False

        self.available = checks_passed
        if self.available:
            print(f"[linkedin_publisher] Ready to publish")
        else:
            print(f"[linkedin_publisher] Prerequisites not met")

    def publish_text_via_puppeteer(self, text, post_id=None):
        """
        Publish a text post via Puppeteer + Chrome CDP.

        Uses publish_post.cjs which handles the full flow:
          1. Connect to Chrome on port 9222
          2. Click "Start a post"
          3. Wait for the editor
          4. Type text paragraph-by-paragraph
          5. Click "Post"

        Args:
            text: The post text content
            post_id: Optional post ID for logging

        Returns:
            str: "published-{post_id}" on success, None on failure
        """
        pid_tag = f" [{post_id}]" if post_id else ""
        print(f"[linkedin_publisher]   Publishing via Puppeteer{pid_tag}...")

        # Write text to temp file
        safe_name = (post_id or "publish").replace("/", "_").replace("\\", "_")
        temp_file = os.path.join(BASE_DIR, f"_temp_{safe_name}.txt")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"[linkedin_publisher] Could not write temp file: {e}")
            return None

        try:
            script_name = os.path.basename(self.script_path)
            print(f"[linkedin_publisher]   Running: node {script_name}")
            result = subprocess.run(
                ["node", self.script_path, temp_file],
                capture_output=True, text=True, timeout=180
            )

            # Print output
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    print(f"[puppeteer] {line}")
            if result.stderr:
                for line in result.stderr.strip().split("\n"):
                    print(f"[puppeteer:err] {line}")

            if result.returncode == 0:
                print(f"[linkedin_publisher] Published successfully!")
                return f"published-{post_id or int(time.time())}"
            else:
                print(f"[linkedin_publisher] Puppeteer exited with code {result.returncode}")
                return None

        except subprocess.TimeoutExpired:
            print(f"[linkedin_publisher] Puppeteer timed out after 180s")
            return None
        except FileNotFoundError:
            print(f"[linkedin_publisher] Node.js not found")
            return None
        except Exception as e:
            print(f"[linkedin_publisher] Error: {e}")
            return None
        finally:
            try:
                os.remove(temp_file)
            except:
                pass

    def publish_post_by_record(self, record):
        """
        Publish a single post based on its approval record.

        Uses Puppeteer to type the content into LinkedIn's editor.

        Args:
            record: Approval record dict from approval_data.json

        Returns:
            str: Reference string on success, None on failure
        """
        post_id = record.get("post_id", "unknown")
        content = record.get("content", "")
        post_type = record.get("post_type", "text")

        print(f"\n{'='*60}")
        print(f"  PUBLISHING: {post_id} ({post_type})")
        print(f"{'='*60}")

        fp = record.get("file_path")
        if fp and os.path.exists(fp):
            print(f"[linkedin_publisher]   Media attached: {fp}")

        return self.publish_text_via_puppeteer(content, post_id)

    def publish_batch(self, post_records, send_summary=True):
        """
        Publish a batch of approved posts sequentially.

        Args:
            post_records: Dict of {post_id: record} from get_approved_content()
            send_summary: Whether to send a Slack summary after completion

        Returns:
            dict: {"published": [post_ids], "failed": [post_ids], "skipped": [post_ids]}
        """
        if not post_records:
            print("[linkedin_publisher] No posts to publish.")
            return {"published": [], "failed": [], "skipped": []}

        published = []
        failed = []
        skipped = []

        records_list = list(post_records.items())
        total = len(records_list)

        print(f"\n{'='*60}")
        print(f"  BATCH PUBLISH: {total} post(s)")
        print(f"{'='*60}\n")

        for idx, (post_id, record) in enumerate(records_list, 1):
            print(f"\n[{idx}/{total}] Processing {post_id}...")

            if record.get("status") == "published":
                print(f"  Already published ({record.get('published_at')})")
                skipped.append(post_id)
                continue

            try:
                reference = self.publish_post_by_record(record)
                if reference:
                    published.append(post_id)
                    self._mark_published(post_id, reference)
                else:
                    failed.append(post_id)
            except Exception as e:
                print(f"  Error publishing {post_id}: {e}")
                failed.append(post_id)

            if idx < total:
                delay = 5
                print(f"  Waiting {delay}s before next post...")
                time.sleep(delay)

        print(f"\n{'='*60}")
        print(f"  BATCH PUBLISH COMPLETE")
        print(f"{'='*60}")
        print(f"  Published: {len(published)}")
        print(f"  Failed:    {len(failed)}")
        print(f"  Skipped:   {len(skipped)}")
        print(f"{'='*60}")

        if send_summary and slack_api:
            self._send_slack_summary(published, failed, skipped)

        return {"published": published, "failed": failed, "skipped": skipped}

    def _mark_published(self, post_id, reference):
        """Mark a post as published in the approval system."""
        if ApprovalManager is None:
            return
        try:
            mgr = ApprovalManager()
            mgr.mark_published(post_id)
            if post_id in mgr.approvals:
                mgr.approvals[post_id]["publish_reference"] = reference
                mgr._save()
        except Exception as e:
            print(f"[linkedin_publisher] Could not mark published: {e}")

    def _send_slack_summary(self, published, failed, skipped):
        """Send final Slack summary after batch publish."""
        if slack_api is None or CHANNEL is None:
            return

        lines = [
            f"{EMOJI_PUBLISHED} *Review Complete!* I have processed the batch:",
            f"- **{len(published)}** Posts published to LinkedIn.",
            f"- **{len(skipped) + len(failed)}** Posts skipped.",
            "",
            "All set!",
        ]
        if published:
            lines.append(f"\nPublished:")
            for pid in published:
                lines.append(f"  - `{pid}`")
        if failed:
            lines.append(f"\nFailed:")
            for pid in failed:
                lines.append(f"  - `{pid}`")
        if skipped:
            lines.append(f"\nSkipped:")
            for pid in skipped:
                lines.append(f"  - `{pid}`")

        try:
            slack_api("chat.postMessage", {
                "channel": CHANNEL,
                "text": "\n".join(lines),
            })
            print(f"[linkedin_publisher] Summary sent to Slack")
        except Exception as e:
            print(f"[linkedin_publisher] Could not send Slack summary: {e}")


# ── CLI Entry Point ────────────────────────────────────────────────────────

def get_approved_content():
    """Get all approved posts ready for publishing from approval_data.json."""
    if ApprovalManager is None:
        print("[linkedin_publisher] ERROR: approval_lib not available")
        return {}
    mgr = ApprovalManager()
    mgr.cleanup_expired()
    approved = {}
    for pid, record in mgr.approvals.items():
        if record.get("status") == "approved":
            approved[pid] = record
    return approved


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "--publish":
        if len(sys.argv) < 3:
            print("Usage: --publish <post_id>")
            return
        post_id = sys.argv[2]
        if ApprovalManager is None:
            print("approval_lib not available")
            return
        mgr = ApprovalManager()
        record = mgr.get_post(post_id)
        if not record:
            print(f"Post '{post_id}' not found")
            return
        if record.get("status") != "approved":
            print(f"Post '{post_id}' is not approved (status: {record.get('status')})")
            return
        publisher = LinkedInPublisher()
        publisher.publish_post_by_record(record)

    elif cmd == "--publish-batch":
        publisher = LinkedInPublisher()
        if not publisher.available:
            print("\nCannot publish. Fix prerequisites and try again.")
            return
        approved = get_approved_content()
        if not approved:
            print("No approved posts to publish.")
            return
        results = publisher.publish_batch(approved)
        print(f"\nResults: {json.dumps(results, indent=2)}")

    elif cmd == "--queue":
        if ApprovalManager is None:
            print("approval_lib not available")
            return
        mgr = ApprovalManager()
        stats = mgr.get_summary_stats()
        print(f"Approval Queue:")
        print(f"  Total:     {stats.get('total', 0)}")
        print(f"  Pending:   {stats.get('pending', 0)}")
        print(f"  Approved:  {stats.get('approved', 0)}")
        print(f"  Rejected:  {stats.get('rejected', 0)}")
        print(f"  Published: {stats.get('published', 0)}")
        approved = mgr.get_approved_posts()
        if approved:
            print(f"\nApproved posts ready:")
            for pid, rec in approved.items():
                ptype = rec.get("post_type", "text")
                preview = (rec.get("content", "") or "")[:80].replace("\n", " ")
                print(f"  - `{pid}` ({ptype}): {preview}...")

    elif cmd == "--check":
        publisher = LinkedInPublisher()
        if publisher.available:
            print("\nAll prerequisites met. Ready to publish.")
        else:
            print("\nSome prerequisites missing.")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
