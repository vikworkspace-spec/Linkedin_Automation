"""Publish all approved posts."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from linkedin_publisher import LinkedInPublisher, get_approved_content

print("=" * 60)
print("  CHECKING FOR APPROVED POSTS")
print("=" * 60)

approved = get_approved_content()
if not approved:
    print("❌ No approved posts found.")
    sys.exit(0)

print(f"\n✅ Found {len(approved)} approved post(s) ready for publishing:\n")
for pid, rec in approved.items():
    ptype = rec.get("post_type", "text")
    preview = (rec.get("content", "") or "")[:100].replace("\n", " ")
    print(f"  • `{pid}` ({ptype}): {preview}...")

print(f"\n{'='*60}")
print(f"  STARTING PUBLISH...")
print(f"{'='*60}")

publisher = LinkedInPublisher()

if not publisher.available:
    print("\n⚠️  Prerequisites not met. Cannot publish.")
    sys.exit(1)

results = publisher.publish_batch(approved, send_summary=True)

print(f"\nResults: {results}")
print(f"✅ Published: {len(results['published'])}")
print(f"❌ Failed: {len(results['failed'])}")
print(f"⏭️  Skipped: {len(results['skipped'])}")
