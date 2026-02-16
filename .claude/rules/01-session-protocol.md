# Session Protocol

## Startup Checklist

Every session begins with these reads (in order):

1. `CLAUDE.md` — project identity, safety rules, coding standards
2. `PROJECT_MASTER_PLAN.md` — current phase, next steps, blockers
3. Last 3 entries of `PROGRESS_LOG.md` — what happened recently

Then: `git pull origin main` to ensure you have the latest state.

## Completion Checklist

Before ending any session that modified files:

1. **PROGRESS_LOG.md** — Append a timestamped entry. Format:
   ```
   ## YYYY-MM-DD HH:MM [Topic]
   - What was done
   - Key decisions or findings
   - What's next
   ```
2. **PROJECT_MASTER_PLAN.md** — Update the current status marker if the phase changed
3. **Git commit + push** — Stage changed files, commit with a descriptive message, push to origin

## Append-Only Rule (CRITICAL)

PROGRESS_LOG.md is append-only. If an entry already exists for today, add new content below it. Never overwrite or edit previous entries.

## Commit Discipline

Commit and push immediately after every meaningful file change. Do not batch changes across multiple operations. Sessions on other devices or future sessions cannot see uncommitted work.

Commit messages should describe what changed and why — not generic "update files" messages.
