# Agent Handoff: YouTube Longitudinal — AI Design Integration

**Created:** Feb 16, 2026
**Context:** This handoff captures all decisions, analysis, and implementation plans from the current session for continuation by new agents.

---

## What Was Done This Session

1. **Read and evaluated** the design document (`SECOND_BRAIN/03-research/YOUTUBE_DATASET_DESIGN.md`) containing three new research designs
2. **Audited every Python script** in the repo against the design doc's proposed architecture
3. **Analyzed both raw data files** (Infludata CSV + Bailey's xlsx) — confirmed 14,169 unique channels, 100% overlap
4. **Corrected a data quality misdiagnosis**: Bailey's xlsx does NOT have 4,097 misaligned rows. It has ~4,098 channels with blank gender and ~4,106 with blank race (uncoded, not misaligned). Minor typos in race coding need cleaning. The "misalignment" was a parsing artifact from reading xlsx cells positionally instead of by cell reference.
5. **Expanded project scope**: CLAUDE.md updated to include gender gap longitudinal panel alongside the new creator cohort study
6. **Created new directory structure**: `src/panels/`, `src/enrichment/`, `src/analysis/`, `data/channels/gender_gap/`, `data/channels/ai_census/`, `data/video_inventory/`, `data/daily_panels/{video_stats,channel_stats}/`, `data/transcripts/`, `data/comments/`, `logs/`
7. **Resolved all 9 methodological decisions** with Katie (see below)
8. **Wrote detailed implementation plan**: `.claude/plans/cached-knitting-puffin.md`

## All Decisions Made (Katie-approved)

| # | Decision | Answer |
|---|----------|--------|
| 1 | Repo scope | EXPANDED — this repo owns gender gap panel data collection |
| 2 | Panel composition | ALL 14,169 channels |
| 3 | AI search terms | BROAD — include "agentic AI", "Claude Code", both programming-AI and generative-AI |
| 4 | Gender coding | DEFERRED — code gender after gathering AI creators |
| 5 | AI adoption detection | Three-layer: keyword matching → transcript analysis → production discontinuity. Start with keywords, validate against 200 human-coded videos |
| 6 | Comment depth | RANDOMIZED SAMPLE per video |
| 7 | Transcript language | Decide later |
| 8 | Management Science paper | Katie will find it; could inform AI adoption measurement |
| 9 | Database vs CSVs | Start with partitioned CSVs; migrate to SQLite when 30+ daily files |

---

## What Needs To Be Built

### Full Plan Reference
`.claude/plans/cached-knitting-puffin.md` — contains the complete implementation plan with phases, script specs, and verification steps.

### Critical Files to Read Before Coding

| File | Why |
|------|-----|
| `CLAUDE.md` | Project identity, safety rules, coding standards |
| `src/youtube_api.py` | 926-line API wrapper — all new scripts call this. Has `execute_request()`, `chunks()`, `get_video_details_batch()`, `get_channel_stats_only()`, `search_videos_paginated()`, etc. |
| `src/config.py` | 675-line config — paths, schemas, keywords, topic decoding. New scripts need new entries here. |
| `src/collection/discover_intent.py` | Template for discover_ai_creators.py — proven video-first search pattern |
| `src/sweeps/sweep_channels.py` | Checkpoint/resume pattern (ChannelSweeper class) — daily_stats.py should follow this pattern |
| `config/config.yaml` | API key + quota config (18 lines) |
| `.claude/rules/02-data-collection.md` | Test-before-production protocol |

### Phase 0: Data Preparation (remaining tasks)

**Task 0.1: Clean Bailey's xlsx → clean CSV**
- Parse `data/raw/BAILEYS FULL CHANNEL LIST WITH GENDER AND RACE.xlsx` using cell references (NOT positional)
- Fix race typos: "blakc"→"black", "undetermiend"→"undetermined", "whitee"→"white", "wht"→"white", "asain"→"asian", "wihte"→"white"
- Strip trailing spaces from all string fields
- Output: `data/processed/gender_gap_panel_clean.csv`
- CRITICAL: Use column letter references when parsing xlsx. The XML skips empty cells, so positional reading misaligns sparse rows.

**Task 0.2: Produce canonical channel list**
- Extract unique channel_ids from the cleaned Bailey's CSV
- Output: `data/channels/gender_gap/channel_ids.csv` (single column: channel_id, 14,169 rows)
- Also produce `data/channels/gender_gap/channel_metadata.csv` with channel_id, perceivedGender, race, runBy, subscriberCount, viewCount

**Task 0.3: Update config.py**
- Add new directory paths: GENDER_GAP_DIR, AI_CENSUS_DIR, VIDEO_INVENTORY_DIR, DAILY_PANELS_DIR, TRANSCRIPTS_DIR, COMMENTS_DIR
- Add new schemas: VIDEO_STATS_FIELDS, COMMENT_FIELDS, VIDEO_INVENTORY_FIELDS
- Add AI_SEARCH_TERMS list (broad: "AI tutorial", "artificial intelligence", "ChatGPT", "AI tools", "agentic AI", "AI automation", "prompt engineering", "generative AI", "Midjourney tutorial", "Claude Code", "AI video editing", "AI voice", "DALL-E", "Sora AI", "ElevenLabs", "Cursor AI", "Copilot tutorial")
- Follow existing patterns in config.py for path construction and ensure_directories()

### Phase 1: Core Collection Infrastructure

**Task 1.1: Add `get_all_video_ids()` to youtube_api.py**
- Adapts from existing `get_oldest_video()` (same playlist pagination logic, lines ~547-621)
- Remove the 10-page cap → paginate to completion
- Keep ALL video IDs (not just the last page)
- Support checkpoint via `nextPageToken` parameter
- Returns: list of dicts `{video_id, channel_id, published_at, title}`
- ~60 lines of new code

**Task 1.2: Add quota tracking to `execute_request()` in youtube_api.py**
- `execute_request()` at lines ~92-118 is the single chokepoint for all API calls
- Add parameters: `quota_cost=1`, `endpoint_name="unknown"`
- After successful execution, append to a daily CSV log: `logs/quota_YYYYMMDD.csv`
- Columns: timestamp, endpoint_name, quota_cost, cumulative_daily_total
- ~50 lines of new code

**Task 1.3: Build `src/collection/enumerate_videos.py`**
- Input: CSV with `channel_id` column
- For each channel: convert UC→UU for uploads playlist ID, call `get_all_video_ids()`, save video inventory
- Output: `data/video_inventory/gender_gap_inventory.csv` with video_id, channel_id, published_at, title, scraped_at
- Must support checkpoint/resume (JSON file tracking which channels are done)
- Must support `--test` and `--limit` flags
- CLI: `python -m src.collection.enumerate_videos --channel-list data/channels/gender_gap/channel_ids.csv [--test] [--limit N]`
- ~200 lines

**Task 1.4: Build `src/panels/daily_stats.py`**
- THE core panel engine. This is the most complex new script.
- Input: video inventory CSV (from enumerate_videos.py)
- Action: batch `videos.list(part=statistics)` for all video IDs in groups of 50, plus `channels.list(part=statistics)` for all channel IDs
- Output: `data/daily_panels/video_stats/YYYY-MM-DD.csv` and `data/daily_panels/channel_stats/YYYY-MM-DD.csv`
- Video stats fields: video_id, view_count, like_count, comment_count, scraped_at
- Channel stats fields: channel_id, view_count, subscriber_count, video_count, scraped_at
- Must support checkpoint/resume (track which video batches processed today)
- Must support `--test` and `--limit` flags
- Must detect new videos (call `detect_new_videos()` for channels with video_count increase) and append to inventory
- CLI: `python -m src.panels.daily_stats --video-inventory data/video_inventory/gender_gap_inventory.csv [--test] [--limit N]`
- ~300 lines
- Can reuse `get_video_details_batch()` from youtube_api.py (or add leaner `get_video_stats_only()` that requests only `part="statistics"`)

**Task 1.5: Create `__init__.py` files**
- `src/panels/__init__.py`
- `src/enrichment/__init__.py`
- `src/analysis/__init__.py`

**Task 1.6: Set up launchd automation**
- Create `~/Library/LaunchAgents/com.youtube-longitudinal.daily-stats.plist`
- Run daily_stats.py at 3 AM EST
- Log stdout/stderr to `logs/`

### Phase 2: AI Creator Census (after Phase 1 is running)

**Task 2.1: Build `src/collection/discover_ai_creators.py`**
- Follow `discover_intent.py` pattern exactly (video-first search → extract channels → get details → save)
- Use AI_SEARCH_TERMS from config.py instead of intent keywords
- NO date filter (we want all AI creators, not just 2026)
- Output: `data/channels/ai_census/initial_YYYYMMDD.csv`
- CLI: `python -m src.collection.discover_ai_creators [--test] [--limit N]`
- ~200 lines (mostly following the proven discover_intent.py pattern)

### Phase 3: Enrichment Infrastructure (after Phases 1-2)

**Task 3.1: Add `get_comment_threads()` to youtube_api.py**
- New method calling `commentThreads.list(part="snippet")`
- Must catch 403 with `commentsDisabled` reason and return empty list gracefully
- Support pagination via `pageToken`
- Returns: list of dicts `{comment_id, video_id, author_display_name, text_display, like_count, published_at}`
- ~60 lines

**Task 3.2: Build `src/enrichment/pull_comments.py`**
- Input: CSV with video_id column
- For each video: call `get_comment_threads()`, take a RANDOM SAMPLE of comments (not top-N)
- Output: `data/comments/comments_YYYYMMDD.csv`
- Handle disabled comments gracefully (log and skip)
- ~200 lines

**Task 3.3: Build `src/enrichment/pull_transcripts.py`**
- Uses `youtube-transcript-api` (unofficial, NO API quota cost)
- Add `youtube-transcript-api` to requirements.txt
- Input: CSV with video_id column
- Output: `data/transcripts/transcripts_YYYYMMDD.csv` with video_id, language, text, scraped_at
- Handle missing transcripts gracefully
- ~150 lines

### Phase 4: Analysis (after weeks of data accumulation)

**Task 4.1: Build `src/analysis/detect_ai_adoption.py`**
- Input: video metadata (titles, descriptions, tags) + transcript text
- Layer 1: keyword matching (tool names + process phrases)
- Output: `data/processed/ai_adoption_flags.csv` with video_id, channel_id, ai_keyword_score, ai_transcript_score, ai_composite_flag, published_at
- Per-channel: first_ai_adoption_date
- ~200-300 lines

---

## Parallel Agent Strategy

These tasks have clear independence boundaries:

**Agent A (Data Prep):** Tasks 0.1, 0.2, 0.3 — can run immediately, no API calls needed

**Agent B (API Infrastructure):** Tasks 1.1, 1.2, 1.5 — youtube_api.py and config changes. Must complete before Tasks 1.3, 1.4.

**Agent C (Collection Scripts):** Tasks 1.3, 1.4 — depends on Agent B completing. This is the critical path.

**Agent D (AI Census):** Task 2.1 — independent of Agents B/C, only depends on Agent A (for config.py updates)

Tasks 1.6, 3.1-3.3, 4.1 are lower priority and can be done sequentially after the above complete.

---

## Coding Standards (from CLAUDE.md)

- pathlib for all paths, logging module (not print), type hints on all signatures
- Checkpoint/resume for operations >5 minutes
- Every script supports `--test` and `--limit` flags
- All paths derive from `Path(__file__)` relative resolution
- Run as modules: `python -m src.panels.daily_stats [--test] [--limit N]`
- Test before production: `--test --limit 5` first, then validate output, then request Katie's approval

## Safety Rules (from CLAUDE.md)

- Never start collection >1000 channels without Katie's approval
- Never modify files in `data/raw/`
- Check quota before large API operations
- Validate data after every collection run
- config/config.yaml must never be committed to git
