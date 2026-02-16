---
name: log-update
description: End-of-session protocol — update tracking docs, commit, and push
user-invocable: true
---

# /log-update

End-of-session workflow. Updates all tracking files and pushes to git.

## Steps

1. **Read current state** of PROGRESS_LOG.md and PROJECT_MASTER_PLAN.md

2. **Append to PROGRESS_LOG.md** — Add a timestamped entry:
   ```
   ## YYYY-MM-DD HH:MM [Topic]
   - What was accomplished this session
   - Key decisions, findings, or blockers
   - What's next
   ```
   CRITICAL: Append only. Never overwrite existing entries.

3. **Update PROJECT_MASTER_PLAN.md** — If the current phase or status changed, update the status marker. If not, leave it alone.

4. **Git add + commit + push**:
   ```bash
   git add PROGRESS_LOG.md PROJECT_MASTER_PLAN.md DECISION_LOG.md TECHNICAL_SPECS.md
   git commit -m "Log: [brief description of session work]"
   git push origin main
   ```
   Only stage files that actually changed. Commit message starts with "Log:" followed by a concise summary.

5. **Confirm** — Report back what was logged and the git push status.

## Arguments

- `$ARGUMENTS` — Optional: a brief description of what was done this session. If provided, use it as the basis for the log entry. If not provided, summarize based on the conversation history.
