# YouTube Longitudinal — CLAUDE.md

> **Methodology type:** data-gathering-pipeline (API collection, validation, longitudinal panel engineering — methodology-type rules in `RESEARCH/CLAUDE.md` apply)
> **Canonical Open Brain domain tag:** `YouTube Longitudinal`
> **Decision domain tag:** `YouTube Longitudinal Decisions`
> **Project charter:** `SECOND_BRAIN/03-research/youtube-longitudinal/PROJECT_CHARTER.md` — read at session start for goals, milestones, and delegation boundaries.

Universal rules (safety, communication, approval boundaries) live in the global
`~/.claude/CLAUDE.md` kernel. This file carries ONLY project-specific content.

## Project Identity

This project collects longitudinal YouTube data via the YouTube Data API v3 for two research programs:

1. **New Creator Cohort** — Discovers and tracks new YouTube channels created in 2026 to study early-stage creator behavior. Uses a 5-stream sampling design (Intent, Non-Intent, Benchmark, Random, Casual).

2. **Gender Gap Longitudinal Panel** — Daily video-level and channel-level statistics for 14,169 established channels from the Infludata/Bailey's dataset. Supports three research designs: AI Creator Census (gender dynamics in AI content creation), AI Adoption Diffusion Panel (staggered DiD), and Audience Response to AI Content (matching + DiD). The gender gap paper's analysis of *why* the gap exists lives in the dissertation CH2 directory; this repo owns the longitudinal data collection on those channels.

**Tech stack:** Python 3.14, YouTube Data API v3, pandas, pathlib

**API quota:** ~1,010,000 units/day (YouTube Researcher Program tier)

## Directory Layout

```
├── src/                  Production source code
│   ├── config.py         Centralized config (keywords, topics, paths, schemas)
│   ├── youtube_api.py    API module (auth, search, extraction, validation)
│   ├── collection/       Discovery scripts (5 streams + AI census + video enumeration)
│   ├── panels/           Daily statistics collection engine
│   ├── sweeps/           Channel polling + new video detection
│   ├── enrichment/       Comments + transcripts (future)
│   ├── analysis/         AI adoption detection (future)
│   └── validation/       Data quality checks
├── config/config.yaml    API key + quota config (NOT in git)
├── data/
│   ├── raw/              Original research-provided data (Infludata, Bailey) — NEVER modify
│   ├── processed/        Cleaned/transformed data
│   ├── channels/         Channel lists by study (stream_a-d, gender_gap, ai_census)
│   ├── video_inventory/  Full video ID lists per channel
│   ├── daily_panels/     Daily stats output (video_stats/, channel_stats/)
│   ├── videos/           Video-level metadata
│   ├── transcripts/      Transcript text (future)
│   ├── comments/         Comment data (future)
│   └── logs/             Collection run logs
├── docs/                 Reference material (API docs, experiments, quota analysis)
├── output/               Tables and figures
├── temp/                 Intermediate files (deletable)
├── drafts/               Writing
└── archive/              Retired files (never deleted)
```

## Session Protocol

### On Startup

**HOOK CHECK:** A `[SESSION CONTEXT — YouTube Longitudinal]` block is injected automatically at session start. Verify it appeared. If absent, run `search_thoughts` with query "YouTube Longitudinal" manually.

1. Read this file (CLAUDE.md)
2. Read the project charter at `SECOND_BRAIN/03-research/youtube-longitudinal/PROJECT_CHARTER.md`. Print 3-line summary: current milestone, days until next deadline, blockers from last session. Verify work aligns with charter milestones.
3. Read PROJECT_MASTER_PLAN.md — understand current phase and next steps
4. Read the last 3 entries of PROGRESS_LOG.md — understand recent work
5. Check `git status` — ensure working tree is clean

**Recovery:** If the session opened at RESEARCH/ root instead of this workspace, read the Project Index in `RESEARCH/CLAUDE.md` to identify the active project. Log root-level sessions to `RESEARCH/PROGRESS_LOG.md`.

### On Completion
1. Append timestamped entry to PROGRESS_LOG.md (append-only, never overwrite)
2. Update current status marker in PROJECT_MASTER_PLAN.md if phase changed
3. `git add` changed files, commit with descriptive message, push to origin
4. **Open Brain captures** (required for substantive sessions — actually call `capture_thought`, do NOT just write out what captures "would" say):
   - Session (always if significant): content = "[Date] YT Longitudinal: [1-2 sentence summary]", domain = "YouTube Longitudinal"
   - Decision (if a meaningful technical/design decision was made): content = "Decision: [what] — because [rationale]", domain = "YouTube Longitudinal Decisions"
   - Learning (if a technical insight emerged): content = "Learning: [insight]. Context: [trigger]", domain = "YouTube Longitudinal"
   Skip if session was purely mechanical (status check, minor config edit, no decisions made).

## Pipeline Health Checks

Binary-testable at any check-in:
- Daily collection pipeline runs without errors and produces validated output
- No quota overruns or unexpected API failures in the last 7 days
- Current collection phase matches the milestone in PROJECT_CHARTER.md

## Safety Rules (project-specific; global rules apply on top)

- **Always run `--test` mode first** before any production collection
- **Never start a full collection run** (>1000 channels) without Katie's explicit approval
- **Check quota** before any large API operation: verify units available vs. units required
- **Validate data after every collection run** using `src/validation/validate_sweep.py`
- **Never modify raw data files** in `data/raw/` — those are research-provided originals
- **Config contains API key** — `config/config.yaml` must never be committed to git

## Coding Standards

- **pathlib, not string concatenation** for all file paths
- **logging module, not print()** for all output
- **Type hints** on all function signatures
- **Checkpoint/resume** for any operation that takes >5 minutes
- **Every script supports `--test` and `--limit` flags** for validation
- All paths derive from `Path(__file__)` relative resolution — no hardcoded absolute paths
- Run scripts as modules: `python -m src.collection.discover_intent [--test] [--limit N]`

## Require Katie's Approval For
- Starting production collection runs (any run >1000 channels)
- Sample size or target changes
- Adding or modifying stream definitions
- Methodological decisions (filtering criteria, cohort cutoff dates)
- Any operation that consumes >10,000 API quota units

## Allow Autonomous Execution For
- Reading and analyzing existing data files
- Running validation scripts
- Generating diagnostic plots and descriptive statistics
- Updating tracking documents (PROGRESS_LOG, PROJECT_MASTER_PLAN)
- Running `--test` mode on any collection script
- Git commit and push of documentation updates

## Sampling Design (Reference)

> **Full architecture doc:** `docs/SAMPLING_ARCHITECTURE.md` — all 12 streams, methodologies, justifications, research designs, and design decisions in one place.

### New Creator Cohort (5 streams)

| Stream | Target | Purpose | Script |
|--------|--------|---------|--------|
| A (Intent) | 200k | Channels explicitly starting creator journeys | `discover_intent.py` |
| A' (Non-Intent) | 200k | Content-first channels (no intent signals) | `discover_non_intent.py` |
| B (Benchmark) | 2k | Algorithm-favored channels (bias baseline) | `discover_benchmark.py` |
| C (Random) | 50k | Random prefix search (population baseline) | `discover_random.py` |
| D (Casual) | 25k | Raw-filename uploaders (casual baseline) | `discover_casual.py` |

### Gender Gap Longitudinal Panel

| Component | Size | Purpose | Script |
|-----------|------|---------|--------|
| Gender gap channels | 14,169 | Established panel from Infludata/Bailey's | `daily_stats.py` |
| AI Creator Census | ~2-5k (TBD) | AI content creators for gender dynamics study | `discover_ai_creators.py` |

### Three AI Research Designs (built on gender gap panel)

1. **AI Creator Census** — Descriptive + cross-sectional regression on AI content creators
2. **AI Adoption Diffusion Panel** — Staggered DiD tracking AI tool adoption among established creators
3. **Audience Response** — Matching + DiD for audience engagement with AI-produced content
