#!/usr/bin/env python3
"""
convert_to_approval_workflow.py — Convert existing delivery scripts to use the approval workflow.

This script patches existing delivery scripts so they post content with approval markers.
It backs up originals before modifying.

Usage:
  python convert_to_approval_workflow.py
"""

import os
import sys
import shutil
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Files to convert (add patterns here as needed)
DELIVERY_SCRIPTS = [
    "slack_deliver_614.py",
    "send_to_slack.py",
    "slack_send_brandstory.py",
    "send_fable_to_slack.py",
]

# The import we want to add
APPROVAL_IMPORT = """
# ── Approval Workflow Integration ──────────────────────────────
from approval_lib import (
    post_text_with_approval,
    upload_with_approval,
    ApprovalManager,
)
# ───────────────────────────────────────────────────────────────

"""


def convert_slack_deliver_style(filepath):
    """
    Convert scripts like slack_deliver_614.py and slack_deliver.py
    that have post() and upload() functions.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if already converted
    if "from approval_lib import" in content:
        print(f"  ⏭️  Already converted: {filepath}")
        return False
    
    # 1. Add import after existing imports
    # Find the last import line
    import_end = -1
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            import_end = i
    
    if import_end >= 0:
        # Insert after last import
        indent = ""
        lines.insert(import_end + 1, APPROVAL_IMPORT.strip())
        content = "\n".join(lines)
    
    # 2. Replace post() function body with approval version
    # Find the post function definition
    old_post = """def post(label, text):
    r = api("chat.postMessage", {"channel": CHANNEL, "text": text, "unfurl_links": False, "unfurl_media": False})
    print(f"  [{label}] {'OK' if r.get('ok') else 'ERR ' + str(r.get('error'))}"); time.sleep(0.7)
    return r.get("ok")"""
    
    new_post = """def post(label, text):
    post_id, ts = post_text_with_approval(label, text)
    if ts:
        time.sleep(0.7)
        return True
    print(f"  [{label}] ERR"); return False"""
    
    content = content.replace(old_post, new_post)
    
    # 3. Replace upload() function body with approval version
    old_upload = """def upload(label, path, title, comment):
    if not os.path.exists(path): print(f"  [{label}] MISSING {path}"); return
    g = api("files.getUploadURLExternal", {"filename": os.path.basename(path), "length": os.path.getsize(path)}, json_body=False)
    if not g.get("ok"): print(f"  [{label}] getURL ERR {g.get('error')}"); return
    subprocess.run(["curl", "-s", "-F", f"file=@{path}", g["upload_url"]], stdout=subprocess.DEVNULL)
    c = api("files.completeUploadExternal", {"files": [{"id": g["file_id"], "title": title}], "channel_id": CHANNEL, "initial_comment": comment})
    print(f"  [{label}] {os.path.basename(path)} {'OK' if c.get('ok') else 'ERR ' + str(c.get('error'))}"); time.sleep(0.7)
    return c.get("ok")"""
    
    new_upload = """def upload(label, path, title, comment):
    post_id, file_id, ts = upload_with_approval(label, path, title, comment)
    if ts:
        time.sleep(0.7)
        return True
    print(f"  [{label}] ERR"); return False"""
    
    content = content.replace(old_upload, new_upload)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return True


def convert_send_to_slack_style(filepath):
    """
    Convert send_to_slack.py style scripts.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if already converted
    if "from approval_lib import" in content:
        print(f"  ⏭️  Already converted: {filepath}")
        return False
    
    # 1. Add import
    lines = content.split("\n")
    import_end = -1
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            import_end = i
    
    if import_end >= 0:
        lines.insert(import_end + 1, APPROVAL_IMPORT.strip())
        content = "\n".join(lines)
    
    # 2. Replace send_slack_message function
    old_send = """def send_slack_message(text):
    print(f"Sending message (length: {len(text)})...")
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "channel": channel,
        "text": text,
        "unfurl_links": False,
        "unfurl_media": False
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode("utf-8"), 
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            resp = json.loads(res.read().decode("utf-8"))
            if not resp.get("ok"):
                print(f"Error sending message: {resp.get('error')}")
            else:
                print("Message sent successfully.")
    except Exception as e:
        print(f"Exception sending message: {e}")"""
    
    new_send = """def send_slack_message(text, label="message"):
    print(f"Sending approval-marked message (length: {len(text)})...")
    post_id, ts = post_text_with_approval(label, text)
    if ts:
        print("Message sent with approval markers.")
    else:
        print("Failed to send message.")"""
    
    content = content.replace(old_send, new_send)
    
    # 3. Replace upload_slack_file function
    old_upload = """def upload_slack_file(file_path, file_name, initial_comment):
    if not file_path or not os.path.exists(file_path):
        print(f"Error: file not found: {file_path}")
        return

    print(f"Uploading file: {file_name} ({os.path.getsize(file_path)} bytes)...")
    
    # 1. Get upload URL
    url = "https://slack.com/api/files.getUploadURLExternal"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = urllib.parse.urlencode({
        "filename": file_name,
        "length": os.path.getsize(file_path)
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as res:
            resp = json.loads(res.read().decode("utf-8"))
            if not resp.get("ok"):
                print(f"Error getting upload URL: {resp.get('error')}")
                return
            upload_url = resp.get("upload_url")
            file_id = resp.get("file_id")
    except Exception as e:
        print(f"Exception getting upload URL: {e}")
        return

    # 2. Upload file data
    print("Uploading file data to URL...")
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        req = urllib.request.Request(
            upload_url,
            data=file_data,
            method="POST"
        )
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                print("Error uploading raw file data")
                return
            print("File data uploaded successfully.")
    except Exception as e:
        print(f"Exception uploading file data: {e}")
        return

    # 3. Complete upload
    print("Completing upload...")
    url = "https://slack.com/api/files.completeUploadExternal"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "files": [{"id": file_id, "title": file_name}],
        "channel_id": channel,
        "initial_comment": initial_comment
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            resp = json.loads(res.read().decode("utf-8"))
            if not resp.get("ok"):
                print(f"Error completing upload: {resp.get('error')}")
            else:
                print(f"File upload completed: {file_name}")
    except Exception as e:
        print(f"Exception completing upload: {e}")"""
    
    new_upload = """def upload_slack_file(file_path, file_name, initial_comment, label="file"):
    if not file_path or not os.path.exists(file_path):
        print(f"Error: file not found: {file_path}")
        return
    print(f"Uploading file with approval: {file_name}")
    post_id, file_id, ts = upload_with_approval(label, file_path, file_name, initial_comment)
    if ts:
        print(f"File upload completed: {file_name}")
    else:
        print(f"File upload failed: {file_name}")"""
    
    content = content.replace(old_upload, new_upload)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return True


def create_approval_integrated_614_template():
    """
    Create a template for the slack_deliver_614.py file showing how the
    script should look with approval markers integrated.
    """
    template_path = os.path.join(BASE_DIR, "slack_deliver_approval_template.py")
    
    content = '''#!/usr/bin/env python3
"""
slack_deliver_approval_template.py — TEMPLATE with Slack Approval Workflow integration.

This template shows how to convert any date-specific delivery script
(slack_deliver_614.py, slack_deliver.py, etc.) to use approval markers.

Key changes from original:
  - post() posts with approval markers (Post ID, reaction buttons, status)
  - upload() uploads with approval markers
  - All posts tracked in approval_data.json
  - No post goes to LinkedIn without ✅ approval

Usage:
  Copy this template and fill in your date-specific content,
  OR run: python convert_to_approval_workflow.py
"""
import json, os, subprocess, urllib.request, urllib.parse, time

BASE = os.path.dirname(os.path.abspath(__file__)); os.chdir(BASE)
TOKEN = subprocess.check_output("grep '^SLACK_BOT_TOKEN=' .env | cut -d'=' -f2", shell=True).decode().strip()
CHANNEL = "C0BDL4V7VT4"

# ── Approval Workflow Integration ──────────────────────────────
from approval_lib import (
    post_text_with_approval,
    upload_with_approval,
    ApprovalManager,
)
# ───────────────────────────────────────────────────────────────

def api(method, payload, json_body=True):
    if json_body:
        data = json.dumps(payload).encode("utf-8"); ct = "application/json; charset=utf-8"
    else:
        data = urllib.parse.urlencode(payload).encode("utf-8"); ct = "application/x-www-form-urlencoded"
    req = urllib.request.Request(f"https://slack.com/api/{method}", data=data,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": ct})
    return json.loads(urllib.request.urlopen(req).read().decode("utf-8"))

def post(label, text):
    """Post text with approval markers instead of plain message."""
    post_id, ts = post_text_with_approval(label, text)
    if ts:
        time.sleep(0.7)
        return True
    print(f"  [{label}] ERR"); return False

def upload(label, path, title, comment):
    """Upload file with approval markers."""
    post_id, file_id, ts = upload_with_approval(label, path, title, comment)
    if ts:
        time.sleep(0.7)
        return True
    print(f"  [{label}] ERR"); return False

# ================================================================
# PASTE YOUR DATE-SPECIFIC POST CONTENT BELOW
# ================================================================

def main():
    """
    Example main() structure — replace with your actual posts.
    Each post() and upload() call now includes approval markers.
    """
    print("== Posting content with approval markers ==")
    
    # Text posts get approval markers automatically
    post("header", "📅 *Your Content Drop*\\nPosts with approval workflow enabled.")
    post("post-1", "Your first post content here...")
    
    # File uploads also get approval markers
    upload("carousel", "path/to/carousel.pdf", "carousel-title.pdf", "Carousel caption here")
    upload("infographic", "path/to/infographic.png", "infographic.png", "Infographic caption here")
    
    print("== DONE — Posts waiting for approval in #linkedin-content ==")
    print("== Approve with: ✅ reaction or /approve_post <post_id> ==")

if __name__ == "__main__":
    main()
'''
    
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return template_path


def main():
    print(f"{'='*60}")
    print(f"  CONVERT DELIVERY SCRIPTS TO APPROVAL WORKFLOW")
    print(f"  {datetime.datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    # Back up originals first
    backup_dir = os.path.join(BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    for script_name in DELIVERY_SCRIPTS:
        script_path = os.path.join(BASE_DIR, script_name)
        if not os.path.exists(script_path):
            print(f"  ⏭️  Skipping (not found): {script_name}")
            continue
        
        # Back up
        backup_path = os.path.join(backup_dir, f"{script_name}.bak")
        shutil.copy2(script_path, backup_path)
        print(f"  💾 Backed up: {script_name} -> {backup_path}")
        
        # Convert
        print(f"  🔄 Converting: {script_name}...")
        
        if script_name == "send_to_slack.py":
            success = convert_send_to_slack_style(script_path)
        else:
            success = convert_slack_deliver_style(script_path)
        
        if success:
            print(f"  ✅ Converted: {script_name}")
        else:
            print(f"  ⚠️  No changes needed for: {script_name}")
    
    # Create template
    template = create_approval_integrated_614_template()
    print(f"\n  📄 Created approval template: {template}")
    
    print(f"\n{'='*60}")
    print(f"  CONVERSION COMPLETE")
    print(f"{'='*60}")
    print(f"""
  Backups saved in: {backup_dir}/
  
  Converted scripts:
    - slack_deliver_614.py  ✅ Uses approval markers
    - send_to_slack.py      ✅ Uses approval markers
  
  NOTE: If any script wasn't converted correctly, restore from backup:
    cp backups/<script>.bak <script>
  
  NEXT: Run setup_approval_workflow.py to test the system:
    python setup_approval_workflow.py
""")


if __name__ == "__main__":
    main()
