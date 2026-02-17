# Agent Handoff: Post-Audit Round 2

**Date:** February 17, 2026
**From:** Audit session (Referee 2 design audit)
**To:** Next agent session (implement fixes from audit)
**Status:** Audit COMPLETE. Fixes PENDING Katie's review and prioritization.

---

## What Just Happened

A comprehensive Referee 2 design audit was conducted on the entire YouTube Longitudinal project. The audit evaluated every dataset, every sampling script, every research design, the full codebase, all documentation, and data storage/sync architecture. The report is at:

**`output/REFEREE_AUDIT_REPORT.md`** — read this first. It is the source of truth for this handoff.

## Project Identity (from new charter)

**Read the charter:** `SECOND_BRAIN/03-research/youtube-longitudinal/PROJECT_CHARTER.md`

Critical framing: this project is **data infrastructure**, not a single paper. Its job is to build and maintain longitudinal databases with defensible sampling for causal inference across multiple future papers. The gender gap paper is a separate project in a separate repo (`RESEARCH/DISSERTATION/.../YT_v1/`). This repo owns the data collection.

**Current charter milestone:** Approach audit — confirm or redirect remaining streams (A', C) and AI research designs before resuming collection. The charter is established; decisions on outstanding streams remain.

## What's Running Right Now (Do Not Interrupt)

1. **Gender gap daily channel stats** — Mac Mini, 8:00 UTC, 9,760 channels (producing daily CSVs)
2. **New cohort daily channel stats** — Mac Mini, 8:30 UTC, Streams A (83,825) + B (1,539) + D (1,862)
3. **AI census daily channel stats** — Mac Mini, 9:00 UTC, 50,010 channels
4. **Gender gap video enumeration** — laptop, ~5M+ rows, still running with checkpoint/resume
5. **AI census video enumeration** — laptop, 4,175/50,010 channels (~8.3%), ~3 days remaining
6. **Sync to Drive** — Mac Mini, every 6 hours via rsync

These continue regardless of audit outcomes. Do not stop them.

## Audit Findings Summary (4 FATAL | 10 MAJOR | 6 MINOR | 5 INFO)

### FATAL — Must address before any analysis

**F1. Stream C (random baseline) does not exist.**
The external validity anchor for the entire New Creator Cohort is uncollected. Script exists (`discover_random.py`), design is sound. Needs Katie's approval to run (expected ~100-200K API units over 2-3 days, target 50K channels).

**F2. No pre-analysis plan exists.**
Five research designs, zero pre-registration. Enormous specification degrees of freedom. Need at minimum a document specifying: primary outcomes, sample restrictions, estimator choices, treatment definitions, subgroup analyses — per design. This is a writing task, not a coding task.

**F3. Streams A and A' must be collected contemporaneously for valid comparison.**
Stream A is COMPLETE (83,825 channels). Stream A' has NOT been collected. The intent vs. non-intent comparison is confounded if collected at different times. This is a design question for Katie: is the A vs. A' comparison still desired? If yes, A' needs to run ASAP and cross-deduplicate against A.

**F4. AI Census is unvalidated.**
50,010 channels found by keyword search. No human coding confirms they actually produce AI content. Need a 200-300 channel hand-coded validation sample stratified by match intensity and content category. This is a human task (Katie or RA).

### MAJOR — Fix soon (top 5 of 10)

**M1. Expand gender gap panel from 9,760 → all 14,169 channels.** Collect stats on everyone, filter at analysis. Marginal cost: 89 API units/day (~0.009% of quota). Requires updating `data/channels/gender_gap/channel_ids.csv` and SCP-ing to Mac Mini.

**M2. Expand Stream D + tighten "casual" construct.** Add ~20 more filename patterns, apply multi-signal filtering post-hoc. Realistic ceiling: 3,000-5,000 (not 25K).

**M3. Clarify Stream B's role.** Document it as descriptive benchmark only (NOT a comparison group for causal inference). 1,539 is adequate for that purpose.

**M4. Fix `get_channel_stats_only` batch 404 handler** (`src/youtube_api.py`). Currently marks all 50 channels in a batch as not_found on HttpError. Should compare requested vs. returned IDs.

**M5. Fix `detect_new_videos` deletion masking** (`src/youtube_api.py`). Trigger on any video_count change, not just increases.

### CODE BUGS (from audit Section 5)

| ID | Bug | File | Severity |
|----|-----|------|----------|
| M4 | Batch 404 handler marks all 50 channels as not_found | `src/youtube_api.py` ~line 397-411 | MAJOR |
| M5 | detect_new_videos misses uploads when deletions mask count increase | `src/youtube_api.py` | MAJOR |
| M6 | Shorts threshold = 60s (should be 180s or use #shorts tag) | `src/config.py:32` | MAJOR |
| M7 | Duration regex doesn't handle day-level durations | `src/youtube_api.py` | MAJOR |
| M8 | get_oldest_video capped at 500 videos (wrong for large channels) | `src/youtube_api.py` | MAJOR |
| m1 | 10 of 14 log files are empty (FileHandler misconfigured) | Various scripts | MINOR |
| m2 | Quota log endpoint_name always "unknown" | `src/youtube_api.py` | MINOR |
| m3 | discovery_language hardcoded to "English" for non-English AI terms | `src/collection/discover_ai_creators.py` | MINOR |

### DOCUMENTATION DRIFT (from audit Section 6)

Most outdated document: `TECHNICAL_SPECS.md` (frozen at Feb 2, missing everything from Feb 16+). Also stale: `QUOTA_ANALYSIS.md`, `PROJECT_MASTER_PLAN.md` body, `MAC_MINI_DEPLOYMENT.md`.

## Data State

| Dataset | Rows | Size | Location |
|---------|------|------|----------|
| Gender gap inventory | 4.95M videos | 706 MB | `data/video_inventory/gender_gap_inventory.csv` |
| AI census initial | 357K rows (50,010 unique) | 53 MB | `data/channels/ai_census/initial_20260217.csv` |
| AI census IDs | 50,010 | 1.2 MB | `data/channels/ai_census/channel_ids.csv` |
| AI census metadata | 50,118 (108 extra — investigate) | 5.6 MB | `data/channels/ai_census/channel_metadata.csv` |
| Gender gap panel IDs | 9,760 | 248 KB | `data/channels/gender_gap/channel_ids.csv` |
| Stream A | 83,825 channels | (on Mac Mini; channel_ids.csv not yet extracted) | Mac Mini |
| Daily channel stats | 2 files (Feb 16 test, Feb 17 production) | 673 KB | `data/daily_panels/channel_stats/` |
| Total project | — | 1.4 GB | Laptop Drive + Mac Mini local |

**Annual storage projection:** ~19 GB without AI census video stats, ~97 GB with full pipeline.

## What the Next Agent Should Do

**Step 0:** Follow session protocol. Read CLAUDE.md, charter, PROJECT_MASTER_PLAN.md, last 3 PROGRESS_LOG entries.

**Step 1:** Read `output/REFEREE_AUDIT_REPORT.md` in full. This is the audit that prompted this session.

**Step 2:** Ask Katie which findings she wants to tackle. The audit distinguishes:
- **Design decisions** (F1-F4, M1-M3) — require Katie's input
- **Code fixes** (M4-M8, m1-m3) — can be implemented autonomously after Katie approves the approach
- **Documentation updates** — can be done autonomously

**Step 3:** Implement whatever Katie prioritizes. Likely candidates:
- Expanding gender gap panel to 14,169 (M1) — update channel list, SCP to Mac Mini
- Code bug fixes (M4-M8) — these are pure engineering, no methodological judgment required
- Stream C collection (F1) — needs Katie's approval, then run `discover_random.py`
- Stream A' collection (F3) — needs design decision first (contemporaneity concern)

**Step 4:** After fixes, re-run audit lens. The report says "Round 2 scheduled for later today."

## Important Constraints

- **Do NOT stop running services.** The Mac Mini is collecting daily data. Interrupting loses panel continuity.
- **Stream A channel_ids.csv has NOT been extracted yet.** The 83,825 channels are in the Mac Mini's raw output but haven't been processed through `extract_channel_ids.sh` or equivalent.
- **AI census metadata has 108 extra rows vs. the ID file.** Investigate before relying on metadata counts.
- **The 75,020 rows in `gender_gap_panel_clean.csv`** (for 14,169 channels) are unexplained. Could be duplicates from the merge. Investigate.
- **Video enumerations are still running on the laptop.** Let them finish. They have checkpoint/resume.

## Key File Paths

| Purpose | Path |
|---------|------|
| Audit report | `output/REFEREE_AUDIT_REPORT.md` |
| Project charter | `SECOND_BRAIN/03-research/youtube-longitudinal/PROJECT_CHARTER.md` |
| CLAUDE.md | Root `CLAUDE.md` |
| Master plan | `PROJECT_MASTER_PLAN.md` |
| Decision log | `DECISION_LOG.md` |
| Progress log | `PROGRESS_LOG.md` |
| Config (API key) | `config/config.yaml` |
| Core API module | `src/youtube_api.py` |
| Central config | `src/config.py` |
| Daily stats engine | `src/panels/daily_stats.py` |
| All discovery scripts | `src/collection/discover_*.py` |
| Validation | `src/validation/validate_sweep.py`, `health_check.py`, `weekly_digest.py` |
| Mac Mini sync | `scripts/sync-to-drive.sh` |
| Launchd plists | `config/launchd/` |
