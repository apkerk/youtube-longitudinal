# PROJECT MASTER PLAN: YouTube Longitudinal Data Collection

**Purpose:** Comprehensive project context and roadmap
**Last Updated:** Feb 16, 2026
**Current Status:** AI Design Integration + Production Launch

---

## How to Use This File

**At the start of each new chat:**
1. Open this roadmap to understand project context and current status
2. Check `PROGRESS_LOG.md` for recent activity
3. Identify the **Current Marker** (below) and pick one deliverable to work on

**At the end of each chat:**
1. Update `PROGRESS_LOG.md` with timestamped entry
2. Update the **Current Marker** below if roadmap progress was made
3. Update `DECISION_LOG.md` if analytical decisions were made

---

## Current Marker

**Now:** Production launch in progress. Video enumeration running on laptop (checkpoint/resume). Mac Mini deployment documented, ready for next agent.
**Last Session:** Feb 16, 2026 — Launched enumeration, built dual-cadence infrastructure, wrote Mac Mini deployment guide
**Next:** 1) Enumeration completes (~12M videos). 2) Deploy to Mac Mini per `docs/MAC_MINI_DEPLOYMENT.md`. 3) First full collection + verify launchd.

### Session Achievements (Feb 16, 2026 — Night)
- ✅ Panel filtered to 9,760 coded channels (from 14,169). channel_ids.csv + channel_metadata.csv regenerated.
- ✅ daily_stats.py updated with --mode flag (channel/video/both) for dual-cadence collection
- ✅ Video enumeration launched (9,760 channels, ~12M videos, checkpoint/resume)
- ✅ docs/PANEL_SCHEMA.md written (dual-cadence schema, joins, storage projections)
- ✅ docs/MAC_MINI_DEPLOYMENT.md written (9-step guide, EDEADLK workaround, local-first I/O)
- ✅ launchd plists created (daily channel + weekly video), unloaded from laptop pending Mac Mini deploy

### Session Achievements (Feb 16, 2026 — Late Evening)
- ✅ Built 10-slide Beamer infrastructure deck with custom theme, TikZ diagrams, progressive reveal
- ✅ Full deck-compile protocol: 3 passes, narrative review, graphics audit, 0 warnings
- ✅ Output: `output/youtube-longitudinal-infrastructure-deck.{tex,pdf}`

### Session Achievements (Feb 16, 2026 — Evening)
- ✅ Built all gender gap panel infrastructure via 4-agent parallel strategy
- ✅ Cleaned Bailey's xlsx → 14,169 unique channels (515 dupes removed, race typos fixed)
- ✅ Produced canonical channel lists (channel_ids.csv, channel_metadata.csv, gender_gap_panel_clean.csv)
- ✅ Added get_all_video_ids(), get_video_stats_batch(), quota tracking to youtube_api.py
- ✅ Built enumerate_videos.py (video inventory builder with checkpoint/resume)
- ✅ Built daily_stats.py (core daily panel engine with 4-step pipeline)
- ✅ Built discover_ai_creators.py (AI census: 17 terms, 12-month windows)
- ✅ Updated config.py (9 new paths, AI_SEARCH_TERMS, 4 schemas, helpers)
- ✅ All scripts test-verified with real API calls
- ✅ Backward compatibility confirmed for existing scripts

### Prior Session (Feb 16, 2026 — Late Afternoon)
- ✅ Evaluated 3 research designs from YOUTUBE_DATASET_DESIGN.md — all approved for implementation
- ✅ Expanded project scope to include gender gap longitudinal panel (Katie-approved)
- ✅ Updated CLAUDE.md with expanded scope, new directory layout, new sampling tables
- ✅ Corrected Bailey's data quality misdiagnosis (blank fields, not misaligned)
- ✅ Resolved all 9 methodological decisions with Katie
- ✅ Created new directory structure for AI designs (panels/, enrichment/, analysis/, etc.)
- ✅ Wrote full implementation plan (`.claude/plans/cached-knitting-puffin.md`)
- ✅ Wrote agent handoff document (`docs/AGENT_HANDOFF.md`)

### Prior Session (Feb 16, 2026 — Afternoon)
- ✅ Flattened project from triple-nested to clean root-level layout
- ✅ Created CLAUDE.md, `.claude/rules/`, `.claude/skills/log-update`
- ✅ All Python paths verified working after restructuring
- ✅ Committed and pushed to GitHub

### Prior Session (Feb 02, 2026 - Late Evening)
- ✅ Built complete production-grade modular architecture (15 new files)
- ✅ Created comprehensive config system with 8-language keywords + full YouTube topic hierarchy
- ✅ Implemented all 5 collection scripts (A, A', B, C, D)
- ✅ Built sweep system with new video detection and checkpoint/resume
- ✅ Created validation module for data quality checks
- ✅ Successfully tested Stream A (62 channels) and Stream D (15 channels)
- ✅ Scaled sample targets: Stream A and A' → 200k each (to handle attrition)
- ✅ All systems tested and operational

---

# PART 1: PROJECT CONTEXT

## Research Question and Objectives

**Primary Research Question:**  
What are the early-stage drivers of distinctiveness and virality for new cultural producers?

**Objectives:**
1.  **Capture Phase:** Track a cohort of "New Intentional Creators" (Jan 2026) from Day 0.
2.  **Compare Phase:** Contrast their trajectory with a "Visible Market" baseline and a "Deep Random" survivorship control.
3.  **Analyze Phase:** Measure distinctiveness (text/visual) and strategic choices (frequency, categories) over time.

## Data Infrastructure (5-Stream Design — PRODUCTION READY Feb 02, 2026)

**Stream A: Intent Creators (Treatment) — MULTILINGUAL**
- **Target:** 200,000 new entrepreneurs across 8 languages
- **Languages:** Hindi, English, Spanish, Japanese, German, Portuguese, Korean, French
- **Method:** Intent Keywords ("Welcome to my channel", "My first video") -> Filter Creation Date >= Jan 1, 2026
- **Key Finding:** English-only captures only 14% of findable creators. Multilingual = 7.1x expansion.
- **Yield:** 12.7-35.3% (varies by language; Hindi highest at 35.3%)
- **Script:** `src/collection/discover_intent.py`
- **Expected English Yield:** 50k-80k channels

**Stream A': Non-Intent Creators (Comparison Group) — MULTILINGUAL**
- **Target:** 200,000 new creators who start with content (not intros)
- **Languages:** Same 8 languages
- **Method:** Content Keywords ("gameplay", "tutorial", "recipe") -> Same date filter
- **Use:** Causal inference comparison for effect of intentional launching
- **Script:** `src/collection/discover_non_intent.py`

**Stream B: Algorithm Favorites (Benchmark)**
- **Target:** 2,000 channels that YouTube's algorithm surfaces
- **Method:** Vowel search (`a`, `e`, `i`, `o`, `u`) with relevance order
- **⚠️ BIAS WARNING:** Median views = 1.16M, 94% big channels. This is top 0.01%.
- **Use:** Benchmark for competitive landscape
- **Script:** `src/collection/discover_benchmark.py`

**Stream C: Searchable Random (Population Baseline)**
- **Target:** 50,000 channels via random prefix sampling
- **Method:** Random 3-char prefixes -> Unfiltered collection
- **Bias Profile:** Median views = 305, 39% big channels (least biased)
- **Script:** `src/collection/discover_random.py`

**Stream D: Casual Uploaders (Amateur Control)**
- **Target:** 25,000 channels with raw/default file names
- **Method:** Raw file queries (`IMG_`, `MVI_`, `DSC_`, `Screen Recording`)
- **Bias Profile:** Median views = 214, 59% big channels
- **Use:** Contrast strategic vs casual uploading behavior
- **Script:** `src/collection/discover_casual.py`

## Key Findings (Validated Feb 02, 2026)

| Finding | Evidence | Interpretation |
|---------|----------|----------------|
| **Massive Algorithm Bias** | Vowel search median = 1.16M views, 94% big channels | "Random" vowel searches find TOP 0.01% of YouTube |
| **Dark Matter Exists** | Random prefix median = 305 views, 39% big channels | True random sampling finds invisible long-tail |
| **Intent Keywords Work** | 12.7% yield (vs 1.9% non-intent) | 6.6x more efficient at finding new entrepreneurs |
| **Language Bias Critical** | English captures only 14% of new creators | Multilingual expands population by 7.1x |
| **Hindi Outperforms English** | 35.3% yield vs 30.9% | Hindi-speaking YouTube creator ecosystem is booming |
| **Pagination Doesn't Help** | Page 2 has higher views than Page 1 | Cannot reduce bias through pagination |
| **Channel ID Enumeration Infeasible** | 0/100 hits | ID space too sparse; not cost-effective |

---

# PART 2: ROADMAP

## Roadmap Overview
**[Phase 1: Planning] → [Phase 2: Implementation] → [Phase 3: Validation] → [Phase 4: Longitudinal Tracking]**

---

## Phase 1: Planning (Completed) ☑
- **1.1:** Research Design Evaluation (Done)
- **1.2:** Bias Diagnostic & Sampling Strategy (Done)
- **1.3:** Tech/File Structure Setup (Done)

## Phase 2: Implementation (Completed) ✅
- **2.1:** Configuration System (`config.py`) with keywords, topics, schemas [Done]
- **2.2:** Enhanced API Module (`youtube_api.py`) with topic extraction [Done]
- **2.3:** All Collection Scripts (A, A', B, C, D) [Done]
- **2.4:** Sweep System with new video detection [Done]
- **2.5:** Validation Module [Done]
- **2.6:** Data Storage & Schema (CSV with partitioning) [Done]

## Phase 3: Validation & Testing (Completed) ✅
- **3.1:** Sampling experiments (6 experiments documented)
- **3.2:** Test runs (Stream A: 62 channels, Stream D: 15 channels)
- **3.3:** Validation (0 errors, all checks passed)

## Phase 4: Production Collection (Ready) ☐
- **4.1:** Stream A Collection (200k channels) [Tomorrow]
- **4.2:** Stream A' Collection (200k channels) [Tomorrow]
- **4.3:** Remaining Streams (B, C, D) [Week 1]
- **4.4:** Begin Weekly Sweeps [Week 2]

## Phase 5: Longitudinal Tracking ☐
- **5.1:** Automated Sweep Scheduling
- **5.2:** Video-level Data Collection
- **5.3:** Comment Collection (Secondary)

---

# PART 3: KEY REFERENCE FILES

## Documentation
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project AI instructions, session protocol, safety rules |
| `PROGRESS_LOG.md` | Dated chronicle of all work |
| `DECISION_LOG.md` | Analytical decisions with rationale |
| `TECHNICAL_SPECS.md` | Technical specifications (Sampling details) |
| `docs/SAMPLING_EXPERIMENTS.md` | Full experiment log with methodology validation |
| `docs/QUOTA_ANALYSIS.md` | Sample size & polling frequency trade-offs |
| `docs/YOUTUBE_API_VARIABLE_REFERENCE.md` | Full YouTube API field documentation |

---

# PART 4: OPEN QUESTIONS

## Methodological
1.  **Quota Sustainability:** Will 700k units/day trigger any secondary rate limits?
2.  **Storage:** Do we need a database (SQL) immediately, or can we stick to partitioned CSVs for the first month?

## Conceptual
1.  **"Intent" definition:** Are keywords like "Welcome" sufficient proxy for entrepreneurial intent? (Validated by visual inspection so far).
