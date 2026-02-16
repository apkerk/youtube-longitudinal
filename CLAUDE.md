# New Creator Cohort — YouTube Longitudinal Data Collection

## Project Identity

This project discovers and tracks new YouTube channels created in 2026 to study early-stage creator behavior at scale. It uses a 5-stream sampling design (Intent, Non-Intent, Benchmark, Random, Casual) to collect channel-level panel data via the YouTube Data API v3.

**Scope:** Data collection and tracking infrastructure only. This is NOT the gender gap longitudinal panel — that lives in the dissertation CH2 directory.

**Tech stack:** Python 3.12, YouTube Data API v3, pandas, pathlib

**API quota:** ~1,010,000 units/day (YouTube Researcher Program tier)

## Directory Layout

```
├── src/                  Production source code
│   ├── config.py         Centralized config (keywords, topics, paths, schemas)
│   ├── youtube_api.py    API module (auth, search, extraction, validation)
│   ├── collection/       5 stream discovery scripts
│   ├── sweeps/           Channel polling + new video detection
│   └── validation/       Data quality checks
├── config/config.yaml    API key + quota config (NOT in git)
├── data/
│   ├── raw/              Original research-provided data (Infludata, Bailey)
│   ├── processed/        Cleaned/transformed data
│   ├── channels/         Stream output (stream_a through stream_d)
│   ├── videos/           Video-level data
│   └── logs/             Collection run logs
├── docs/                 Reference material (API docs, experiments, quota analysis)
├── output/               Tables and figures
├── temp/                 Intermediate files (deletable)
├── drafts/               Writing
└── archive/              Retired files (never deleted)
```

## Session Protocol

### On Startup
1. Read this file (CLAUDE.md)
2. Read PROJECT_MASTER_PLAN.md — understand current phase and next steps
3. Read the last 3 entries of PROGRESS_LOG.md — understand recent work
4. Check `git status` — ensure working tree is clean

### On Completion
1. Append timestamped entry to PROGRESS_LOG.md (append-only, never overwrite)
2. Update current status marker in PROJECT_MASTER_PLAN.md if phase changed
3. `git add` changed files, commit with descriptive message, push to origin

## Safety Rules

Inherits all global safety rules from `~/.claude/CLAUDE.md`. Additional project-specific rules:

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
- Starting production collection runs
- Sample size or target changes
- Adding or modifying stream definitions
- Methodological decisions (filtering criteria, cohort cutoff dates)
- Any operation that consumes >10,000 API quota units
- Causal claims or analytical interpretations

## Allow Autonomous Execution For
- Reading and analyzing existing data files
- Running validation scripts
- Generating diagnostic plots and descriptive statistics
- Updating tracking documents (PROGRESS_LOG, PROJECT_MASTER_PLAN)
- Running `--test` mode on any collection script
- Git commit and push of documentation updates

## 5-Stream Sampling Design (Reference)

| Stream | Target | Purpose | Script |
|--------|--------|---------|--------|
| A (Intent) | 200k | Channels explicitly starting creator journeys | `discover_intent.py` |
| A' (Non-Intent) | 200k | Content-first channels (no intent signals) | `discover_non_intent.py` |
| B (Benchmark) | 2k | Algorithm-favored channels (bias baseline) | `discover_benchmark.py` |
| C (Random) | 50k | Random prefix search (population baseline) | `discover_random.py` |
| D (Casual) | 25k | Raw-filename uploaders (casual baseline) | `discover_casual.py` |
