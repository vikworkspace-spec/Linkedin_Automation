/**
 * schedule_with_approval.cjs — Approval-gated scheduling wrapper.
 *
 * This script wraps the existing schedule_all_posts.cjs and enforces
 * that only approved posts are scheduled on LinkedIn.
 *
 * Usage:
 *   node schedule_with_approval.cjs [--dry-run] [--publish-unapproved]
 *
 * Options:
 *   --dry-run             Show what would be scheduled without doing it
 *   --publish-unapproved  Bypass approval check (use with caution)
 *
 * Exit codes:
 *   0 = All approved posts scheduled successfully
 *   1 = No approved posts to schedule
 *   2 = Approval check failed
 *   3 = Scheduling error
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const BASE_DIR = __dirname;

// ──────────────────────────────────────────────
//  APPROVAL SYSTEM INTEGRATION
// ──────────────────────────────────────────────

/**
 * Run a Python approval_lib command and return parsed JSON.
 */
function runApprovalCommand(args) {
  const cmd = `python "${path.join(BASE_DIR, 'approval_publish_gate.py')}" ${args}`;
  try {
    const output = execSync(cmd, { encoding: 'utf8', cwd: BASE_DIR });
    return output.trim();
  } catch (err) {
    console.error(`[approval-gate] Error running: ${cmd}`);
    console.error(err.stderr || err.message);
    return null;
  }
}

/**
 * Get approved posts ready for publishing.
 * Returns a Map of post_id -> metadata.
 */
function getApprovedPosts() {
  const output = runApprovalCommand('--export');
  if (!output) return new Map();
  
  try {
    const data = JSON.parse(output);
    return new Map(Object.entries(data));
  } catch (err) {
    console.error('[approval-gate] Failed to parse approved posts:', err.message);
    return new Map();
  }
}

/**
 * Verify if a specific post is approved for scheduling.
 */
function isPostApproved(postId) {
  const output = runApprovalCommand(`--verify ${postId}`);
  if (!output) return false;
  return output.includes('APPROVED');
}

/**
 * Mark a post as published after successful scheduling.
 */
function markPostPublished(postId, scheduledTime) {
  const cmd = scheduledTime 
    ? `--published "${postId}" "${scheduledTime}"`
    : `--published "${postId}"`;
  const output = runApprovalCommand(cmd);
  return output && output.includes('marked as published');
}

/**
 * Mark multiple posts as published (batch).
 */
function markPostsPublished(postIds, scheduledTime) {
  let success = 0;
  let fail = 0;
  for (const pid of postIds) {
    if (markPostPublished(pid, scheduledTime)) {
      success++;
    } else {
      fail++;
    }
  }
  return { success, fail };
}

// ──────────────────────────────────────────────
//  SCHEDULING INTEGRATION
// ──────────────────────────────────────────────

/**
 * Generate the approved_post_ids.json file that scheduling scripts
 * can read to know which posts are approved.
 */
function generateApprovedIdsFile() {
  const approved = getApprovedPosts();
  const ids = Array.from(approved.keys());
  
  const filePath = path.join(BASE_DIR, 'approved_post_ids.json');
  fs.writeFileSync(filePath, JSON.stringify(ids, null, 2));
  console.log(`[approval-gate] ✅ Generated approved post IDs: ${ids.length} posts`);
  return ids;
}

/**
 * Filter a posts array to only include approved posts.
 * Each post must have an 'id' field matching an approved post_id.
 */
function filterApprovedPosts(postsArray) {
  const approvedIds = new Set(generateApprovedIdsFile());
  
  const approved = postsArray.filter(post => {
    const postId = `post_${post.id}`;
    const isApproved = approvedIds.has(postId) || approvedIds.has(String(post.id));
    if (!isApproved) {
      console.log(`[approval-gate] ⏭️  Skipping unapproved post #${post.id}`);
    }
    return isApproved;
  });
  
  console.log(`[approval-gate] ${approved.length}/${postsArray.length} posts approved for scheduling`);
  return approved;
}

// ──────────────────────────────────────────────
//  MAIN
// ──────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const publishUnapproved = args.includes('--publish-unapproved');
  
  console.log('');
  console.log('='.repeat(60));
  console.log('  APPROVAL-GATED SCHEDULING');
  console.log('='.repeat(60));
  console.log('');
  
  // Step 1: Check if approval system is available
  if (!fs.existsSync(path.join(BASE_DIR, 'approval_lib.py'))) {
    console.error('[approval-gate] ❌ Approval system not found (approval_lib.py missing)');
    console.error('[approval-gate]    Run: python setup_approval_workflow.py');
    process.exit(2);
  }
  
  // Step 2: Get approved posts
  const approvedPosts = getApprovedPosts();
  
  if (approvedPosts.size === 0) {
    if (publishUnapproved) {
      console.log('[approval-gate] ⚠️  --publish-unapproved flag set. Bypassing approval gate...');
      console.log('[approval-gate]    Proceeding with original scheduler...');
    } else {
      console.log('[approval-gate] ❌ No approved posts found.');
      console.log('[approval-gate]    Approve posts in Slack with ✅ reaction, or run:');
      console.log('[approval-gate]    python slack_approval_handler.py approve-all');
      console.log('[approval-gate]    --- OR ---');
      console.log('[approval-gate]    Use --publish-unapproved to bypass (not recommended)');
      process.exit(1);
    }
  } else {
    console.log(`[approval-gate] ✅ ${approvedPosts.size} approved post(s) ready:`);
    for (const [pid, rec] of approvedPosts) {
      const preview = (rec.content || '').substring(0, 80).replace(/\n/g, ' ');
      console.log(`  • ${pid}: ${preview}...`);
    }
    
    // Generate the IDs file for reference
    generateApprovedIdsFile();
  }
  
  if (dryRun) {
    console.log('\n[approval-gate] 🏁 Dry run complete. No scheduling performed.');
    console.log('[approval-gate]    To schedule, run without --dry-run');
    process.exit(0);
  }
  
  // Step 3: Generate scheduler-friendly files
  // Creates approved_for_publishing.json that scheduling scripts can reference
  execSync(
    `python "${path.join(BASE_DIR, 'approval_publish_gate.py')}" --generate-files`,
    { cwd: BASE_DIR, stdio: 'inherit' }
  );
  
  // Step 4: Run the actual scheduler with a post-scheduling hook
  console.log('\n[approval-gate] 🚀 Running LinkedIn scheduler for approved posts...');
  console.log('[approval-gate]    (Note: Modify your schedule_* scripts to check approved_post_ids.json)');
  console.log('');
  
  // Run the original scheduler
  try {
    execSync(`node "${path.join(BASE_DIR, 'schedule_all_posts.cjs')}"`, {
      cwd: BASE_DIR,
      stdio: 'inherit',
      env: { ...process.env, APPROVAL_MODE: 'true' }
    });
    
    // After successful scheduling, mark posts as published
    console.log('\n[approval-gate] ✅ Scheduling complete. Marking posts as published...');
    
    const approvedIds = Array.from(approvedPosts.keys());
    const { success, fail } = markPostsPublished(approvedIds, new Date().toISOString());
    
    console.log(`[approval-gate] 📢 ${success} posts marked as published`);
    if (fail > 0) {
      console.log(`[approval-gate] ⚠️  ${fail} posts could not be marked`);
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('  ✅ SCHEDULING COMPLETE');
    console.log('='.repeat(60));
    process.exit(0);
    
  } catch (err) {
    console.error('\n[approval-gate] ❌ Scheduling error:', err.message);
    process.exit(3);
  }
}

main();
