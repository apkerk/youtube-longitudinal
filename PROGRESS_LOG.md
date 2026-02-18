# Progress Log: YouTube Longitudinal Data Collection

**Purpose:** Chronological record of all work completed on this project  
**Update Instructions:** Add new entries at the TOP of each month's section

---

## Current Status (as of Feb 18, 2026 — Morning)

**Phase:** STREAM A AUDIT COMPLETE. Language bias identified — sample needs keyword expansion in missing languages before it can claim population representativeness.
**Roadmap Position:** Stream A RE-RUN COMPLETE (26,327 unique, 24h windows). Stream A' RE-RUN IN PROGRESS on Mac Mini (~5,300+ and growing, 24h windows, excluding Stream A channels). Stream B COMPLETE (18,208). Stream D COMPLETE (3,933). Stream C not started.
**Key Finding This Session:** Stream A quality audit against McGrady et al. (2023) benchmarks reveals severe language skew. Japanese 7.6x overrepresented, Korean 11.9x over, Portuguese 3.4x over. Arabic, Russian, Indonesian, Thai, Turkish completely missing. Spanish 4.1x underrepresented. Decision: ADD KEYWORDS in missing languages to approach population-representative sample. Referee evaluation requested.
**Sample Size vs Targets:**
- Stream A (Intent): 26,327 / 200K target (13.2%) — audit done, needs language keyword expansion
- Stream B (Algorithm Favorites): 18,208 / 25K target (72.8%) — search space exhausted
- Stream D (Casual): 3,933 / 25K target (15.7%) — search space exhausted
- Stream A' (Non-Intent): ~5,300+ / 200K target — running on Mac Mini with 24h windows + A exclusion list
- Stream C (Random): not started / 50K target
**What's Running:**
- Stream A' re-run on Mac Mini (screen `stream_a_prime`, 24h windows, excluding 26,327 Stream A channels, ~269K quota used)
- Gender gap daily channel stats (Mac Mini, 8:00 UTC) — active
- AI census daily channel stats (Mac Mini, 9:00 UTC) — active
**Next Steps:**
1. Referee evaluation of Stream A sample quality vs. McGrady benchmarks
2. Add intent keywords in Arabic, Russian, Indonesian, Thai, Turkish, Bengali, Vietnamese + more Spanish
3. Re-run Stream A with expanded keyword set
4. Launch Stream C (random baseline)
5. Merge all channel lists, create new cohort daily stats launchd service
4. Re-run Stream A' with 24h windows + exclude list
5. Launch Stream C
6. Merge all channel lists, create new cohort daily stats launchd service

---

### Feb 17, 2026 — Late Evening [Time Window Optimization — 3.5x More Channels]

- **Ran time window experiment** testing 3 configurations on 3 keywords (my first video, welcome to my channel, gameplay):
  - Current (48h windows, 30-day lookback): baseline
  - Extended (48h windows, full Jan 1 to now): +81% channels
  - **Narrow (24h windows, full period): +248% channels (3.5x improvement)**
- **Root cause of low yield:** Two independent bottlenecks. (1) 30-day lookback missed all of early January (channels uploading Jan 1-17 were invisible). (2) 48h windows hit the API's per-query result cap (~500 results), so half the videos in each window were never returned.
- **Updated both `discover_intent.py` and `discover_non_intent.py`:** `generate_time_windows()` now defaults to 24h non-overlapping windows covering the full period from COHORT_CUTOFF_DATE to now. Added `--window-hours` CLI arg (default 24). Backward-compatible — old behavior available via `--window-hours 48`.
- **Projected re-run yields:** If 3.5x multiplier holds across all 46 intent keywords × 8 languages, Stream A could grow from 19K to ~50-70K unique channels. Stream A' similarly.
- **Quota estimate for re-runs:** ~2.5-3M units total (both streams), ~2.5-3 days of dedicated quota. Daily stats (~10K/day) unaffected.
- **Updated charter** with current dataset sizes, phase, and milestones.
- **Key finding for all cohort streams:** Only Streams A and A' filter by 2026 creation date. B, C, D and all future streams capture any-age channels.

### Feb 17, 2026 — Evening [Mac Mini Recovery — B Complete, A' Restarted]

- **Stream B was NOT stalled — it COMPLETED.** Previous handoff misdiagnosed B as stalled at 73/122 queries. Log shows it finished all 122 queries (18,208 unique channels) and cleared its checkpoint. The screen session exited cleanly after completion.
- **Stream A' genuinely stalled** at keyword 13/47 (`haul`) with `Connection reset by peer` error. Recovered briefly (collected through 2,594 channels) then python process exited. Checkpoint had 12 completed keywords (2,502 channels).
- **Killed dead screen session + zombie python3 process.** Old python3 (PID 71510) was still alive from the stalled session despite the screen being dead. Killed it to prevent duplicate writes.
- **Restarted A' from checkpoint.** New screen session `stream_a_prime` launched, resumed at keyword 13/47. Progressing well — at 19/47 keywords, ~3,400 channels by end of session.
- **Extracted channel_ids.csv for Stream B** (18,208 unique) and **Stream D** (3,933 unique). Both now have canonical ID files alongside Stream A's existing one.
- **All 5 launchd services healthy.** Gender gap (689 KB) and AI census (3.4 MB) daily stats both ran today. Exit status 0 across the board.
- **Lesson:** `screen -X quit` kills the screen process but does NOT always kill child processes (login, bash, python). When restarting after a stall, always `ps aux | grep` to find and kill orphaned processes before launching a new instance.

### Feb 18, 2026 — Morning [Stream A Audit + Language Bias Discovery]

- **Stream A re-run with 24h windows COMPLETE:** 26,327 unique channels (up from 19,016 with old 48h settings — 1.38x improvement, less than the 3.5x on test keywords, likely because many intent keywords were already near-saturated).
- **Stream A' re-run launched:** 24h windows + excluding 26,327 Stream A channel_ids. Running healthy on Mac Mini, ~5,300 unique channels after ~30 min, ~269K quota used.
- **Full quality audit of Stream A (26,327 channels):**
  - 100% created >= 2026-01-01 (zero leakage)
  - 80.4% have 2+ videos (active creators, not one-off uploaders)
  - Only 1.5% completely dead (0 subs AND 0 views)
  - Only 7 channels (0.03%) with 2+ bot risk flags — negligible contamination
  - Median: 8 subscribers, 1,070 views (30x McGrady's random-sample median views — intent keywords select for active creators)
  - Top topics: Lifestyle (18.8%), Gaming (10.0%), Entertainment (7.0%)
- **Language bias identified (critical finding):**
  - English 33.9% (vs 20.1% on platform — 1.7x over)
  - Japanese 16.8% (vs 2.2% — 7.6x over)
  - Portuguese 16.8% (vs 4.9% — 3.4x over)
  - Korean 8.9% (vs 0.75% — 11.9x over)
  - Arabic, Russian, Indonesian, Thai, Turkish, Bengali, Vietnamese: COMPLETELY MISSING despite being top-10 YouTube languages
  - Spanish: 1.5% (vs 6.2% — 4.1x under)
  - Cause: keyword set only covers 8 languages, and cultural specificity of keywords (e.g., Japanese 初投稿) drives overrepresentation
- **Decision: Expand keyword set** to include missing languages and add more Spanish keywords, aiming for population-representative sample
- **Audit script:** `temp/stream_a_audit.py` — reusable for future stream audits
- **Reference paper:** McGrady et al. (2023) "Dialing for Videos" — random sample of ~10K YouTube videos, key benchmarks for language (English=20.1%), views (median=35), categories (People & Blogs=55.8%), subscribers (median=61)
- **Quota consumed:** ~269K units for A' re-run (still running). Stream A re-run consumed ~2 days of quota on prior session.

### Feb 18, 2026 — Night [5 Future Stream Scripts Built + Mac Mini Status Check]

- **Built 5 new discovery scripts** for future expansion streams (all in `src/collection/`):
  - `discover_livestream.py` — `eventType=completed`, 25K target, 12 time windows
  - `discover_shorts.py` — `videoDuration=short`, 50K target, 24 time windows
  - `discover_creative_commons.py` — `videoLicense=creativeCommon`, 15K target
  - `discover_topic_stratified.py` — cycles through 62 topic IDs from YOUTUBE_PARENT_TOPICS, 40K target
  - `discover_trending.py` — `videos.list(chart=mostPopular)` across 51 region codes, daily append-only log (fundamentally different architecture: two outputs — trending sighting log + cumulative channel details)
- **All scripts** have checkpoint/resume, `--test`/`--limit` flags, incremental CSV writes, CHANNEL_INITIAL_FIELDS schema, logging to `data/logs/`.
- **Updated `config.py`:** 5 new STREAM_DIRS, 5 new SAMPLE_TARGETS, TRENDING_REGION_CODES (51 countries), TRENDING_LOG_FIELDS schema.
- **Updated `youtube_api.py`:** `search_videos_paginated` now accepts `**extra_params` for topicId/eventType/videoDuration/videoLicense passthrough (backward-compatible). New `get_trending_videos()` function for chart=mostPopular.
- **Checked Mac Mini production status:**
  - Stream D: COMPLETE (3,933 unique, 22,158 CSV rows with duplication)
  - Stream A': STALLED at 2,036 unique (7/47 keywords). Checkpoint intact.
  - Stream B: STALLED at 10,993 unique (73/122 queries). Checkpoint intact.
  - Both A' and B stopped at exact same second (23:32:30 UTC Feb 17). Python processes exited, bash wrappers hanging in screen sessions. Root cause: system-level event on Mac Mini.
  - Screen sessions still exist but are dead (bash at 0% CPU, no python3 child processes).
- **All changes committed and pushed** (eec40de).
- What's next: Kill dead screens, restart A'/B from checkpoints. Then assess quota before launching C or future streams.

### Feb 17, 2026 — Evening [Video Enumeration Status Check + Bug Fix]

- **Checked video enumeration progress** for both panels running on laptop:
  - **Gender gap:** 96.4% complete — 9,413/9,760 channels processed, 9,030 with video rows in inventory CSV, 11,008,240 total video rows (~1.5 GB). Should finish soon.
  - **AI census:** 22.6% complete — 11,326/50,010 channels processed, 7,340 with video rows, 6,060,363 total video rows. Estimated ~2 more days at current pace.
- **Fixed shared checkpoint bug in `enumerate_videos.py`:** Both enumeration runs were writing to the same `.enumerate_checkpoint.json` file. Risk: when gender gap finishes, it calls `unlink()` on the checkpoint, which could briefly erase AI census progress. Fixed by deriving checkpoint filename from the output file stem (e.g., `.enumerate_gender_gap_inventory_checkpoint.json`). Fix is safe — running processes use old code in memory and are unaffected.
- Both processes confirmed alive via `ps aux` (PIDs 5155 and 24118).

### Feb 18, 2026 — Night [Production Launches — 3 Streams on Mac Mini]

- **Tested all 4 remaining discovery scripts** on laptop with `--test --limit 5`: A' (Non-Intent), B (Algorithm Favorites), D (Casual Uploaders), C (Random Baseline). All passed. Stream C has a trivial edge case where `--limit <15` yields 0 prefixes due to integer division; not a production issue.
- **Launched 3 production collections on Mac Mini** in detached screen sessions:
  - **Stream A' (Non-Intent):** `stream_a_prime` screen, `--limit 200000 --skip-first-video --exclude-list data/channels/stream_a/channel_ids.csv`. Cross-dedup loaded 19,016 Stream A channels. At 3/47 keywords with ~1,135 channels found. Estimated runtime 1-2 hours.
  - **Stream B (Algorithm Favorites):** `stream_b` screen, `--limit 25000`, 122 expanded queries. At 30/122 queries with ~4,315 channels. Strong yield (~150 unique per query).
  - **Stream D (Casual Uploaders):** `stream_d` screen, `--limit 50000` (high ceiling to exhaust search space). **COMPLETED** — 3,933 unique channels across 37 filename patterns. Within the 3-5K realistic ceiling. Top yielders: IMG_ (231), Screen Recording, Untitled.
- **Stream C (Random Baseline)** held for tomorrow — combined A'+B+D quota is ~600-700K units today, adding C's ~600-800K would exceed daily limit.
- **Quota budget:** ~1.2-1.6M total across 3 days. Well within daily capacity.
- **Decision from Katie:** Stream D limit set high to "get what you can get, audit later."
- **Decision from Katie:** All production collection runs happen on Mac Mini (always-on), not laptop.
- What's next: 1) Check A'/B completion. 2) Launch Stream C. 3) Write scripts for 5 future streams. 4) Extract channel_ids.csv for completed streams. 5) Create new cohort daily stats launchd service on Mac Mini.

### Feb 18, 2026 — Evening [Architecture Document Evaluated — 3-Round Expert Panel]

- **Ran `/plan-eval` on `docs/SAMPLING_ARCHITECTURE.md`** — 10-expert panel, 3 rounds of evaluation + fixes
- **Round 1 (62/100):** Found critical factual errors: Stream A count wrong (83,825 stated vs 19,016 unique), gender percentages summed to 103.4% (wrong denominator), schema field counts wrong (8 vs 5 for daily stats), "natural experiment" language for A vs A' comparison wouldn't survive peer review
- **Round 1 fixes applied:** Corrected Stream A to 19,016 unique, recomputed gender/race on actual 9,760 panel (man=6,345/65%, woman=3,383/34.7%, NB=32/0.3%), fixed all schemas. Added 5 new sections: staggered DiD estimation specification (parallel trends, no-anticipation, treatment heterogeneity, 60-day minimum pre-treatment window), deduplication protocol, Infludata sampling frame discussion, gender coding methodology, deployment constraints (EDEADLK warning). Added pagination cap and safeSearch notes. Added source-of-truth hierarchy (config.py is authoritative).
- **Round 2 (72.3/100):** Sub-agent had miscounted keyword lists — 4 of 6 counts were wrong. Manually verified against config.py: 46 intent, 47 non-intent, 45 AI search, 101 AI flag, 122 benchmark, 37 casual. Fixed all. Removed surviving "natural experiment" from Decision 4.
- **Round 3 (79.4/100):** All numbers verified correct. Panel said doc is at realistic ceiling without Katie's input on 5 methodological decisions: power analysis, ethics/IRB, panel attrition protocol, Design 4 assumptions, gender coding method for new populations.
- **Key lesson:** Sub-agents can miscount list items in code files. When factual accuracy matters, read the source code directly and count manually.
- What's next: production runs — A' first (contemporaneity matters), then B, D, C

### Feb 18, 2026 — Morning [Consolidated Sampling Architecture Document]

- **Created `docs/SAMPLING_ARCHITECTURE.md`** — single canonical reference for all 12 streams, sampling methodologies, experimental justifications, AI research designs, and key design decisions. ~500 lines consolidating content from 7 source documents (TECHNICAL_SPECS, DECISION_LOG, SAMPLING_EXPERIMENTS, PROJECT_MASTER_PLAN, YOUTUBE_DATASET_DESIGN, PROGRESS_LOG, CLAUDE.md).
- **Contents:** Stream-by-stream write-ups (what it captures, why it exists, sampling method, empirical validation, status), 5-stream comparison logic diagram, gender gap panel composition + filtering rationale, all 4 AI research designs with identification strategies, 5 proposed future streams, full experimental evidence tables, quota budget summary, 9 key design decisions with alternatives rejected, known limitations and open questions.
- **Added references** to the new doc from: PROJECT_MASTER_PLAN.md (Key Reference Files), TECHNICAL_SPECS.md (Reference Documents), CLAUDE.md (Sampling Design section), and PROJECT_CHARTER.md (Quality Bar section).
- **Purpose:** Katie needs a single evaluable document for assessing the full stream architecture before resuming production runs.
- What's next: Katie evaluates the architecture doc, provides feedback, then production runs resume.

### Feb 18, 2026 — Early Morning [Launch Prep Complete — Paused for Evaluation]

- **Mac Mini bug fixes deployed:** SSH to 192.168.86.48, `git pull` pulled all 8 fixes (M4-M8, m1-m3). All 5 launchd services confirmed running (exit 0).
- **Stream A channel_ids.csv extracted:** Raw CSV had 83,825 rows but only **19,016 unique channel IDs**. Heavy duplication across keyword batches (same channels found by multiple intent keywords). Previous "83,825 channels" count was misleading — the dedup happened at extraction, not during incremental collection.
- **Stream B (Algorithm Favorites) expanded:** BENCHMARK_QUERIES in config.py grew from 6 entries (vowels + "video") to 100+ common search terms across 12 categories. discover_benchmark.py rewritten with checkpoint/resume and incremental CSV writes. Default target updated to 25,000.
- **Stream D (Casual Uploaders) expanded:** CASUAL_QUERIES grew from 16 to 40+ patterns (Samsung, Pixel, WhatsApp, OBS, Zoom, Loom, Snapchat, TikTok, timestamp defaults). discover_casual.py rewritten with checkpoint/resume. Default target updated to 5,000.
- **Stream A' cross-dedup built:** Added `--exclude-list` flag to discover_non_intent.py. Loads channel_ids.csv and adds those IDs to seen-set before discovery. Stream A's 19,016 channels will be excluded.
- **Channel_ids.csv copied to laptop** via SCP for cross-dedup use in Stream A'.
- **New cohort daily stats service MISSING:** No launchd plist for new cohort on Mac Mini. Charter listed it at 8:30 UTC but it was never created. Needs setup after expanded streams are collected.
- **PAUSED:** Katie running stream evaluation before production. Next agent integrates evaluation results with this prep work.
- What's next: integrate evaluation feedback, then execute production runs

### Feb 17, 2026 — Night [Audit Bug Fixes + Architecture Table]

- **Fixed all 8 code bugs from audit (M4-M8, m1-m3):**
  - M4: `get_channel_stats_only` batch 404 handler — now compares requested vs returned IDs instead of marking all 50 channels in a batch as not_found
  - M5: `detect_new_videos` deletion masking — now checks playlist when known_video_ids available, even if count decreased (deletions masking new uploads)
  - M6: Shorts threshold updated 60s → 180s (YouTube expanded Shorts to 3 min in Oct 2024)
  - M7: Duration regex now handles day-level ISO 8601 durations (P1DT2H3M4S for long livestreams)
  - M8: `get_oldest_video` pagination cap raised from 10 pages (500 videos) to 200 pages (10,000 videos) with warning for larger channels
  - m1: Fixed empty log files across 9 scripts — moved FileHandler setup into `setup_logging()` function called after `config.ensure_directories()` in `main()`
  - m2: Added `endpoint_name` to all `execute_request()` callers in youtube_api.py (was always "unknown"). Also added `quota_cost=100` to search API calls.
  - m3: AI census `discovery_language` no longer hardcoded to "English" — added `AI_SEARCH_TERM_LANGUAGES` mapping in config.py for Spanish, Chinese, German terms
- **Presented unified stream architecture table** — 12 streams total (7 existing + 5 new). Filled in target sizes and cadence for new streams: Topic-Stratified (~30-40K), Trending Tracker (accumulating daily), Livestream Creators (~25K), Shorts-First (~50K), Creative Commons (~10-15K). Pending Katie's approval.
- **Comment sampling strategy discussed:** AI Census gets full pull on AI-flagged videos (highest research value), Algorithm Favorites gets randomized sample, new creator panels deferred (too sparse for now).
- **No production runs.** All changes are to code and documentation only.
- What's next: Katie approves architecture table, then build expanded Stream B + D, run Stream C + A'

### Feb 17, 2026 — Evening [Strategic Design Review + Stream Architecture Overhaul]

- **Full design review session** — Katie reviewed every audit finding (F1-F4, M1-M3) and made decisions:
  - F1 (Stream C / random baseline): **RUN IT** — just hasn't been executed yet
  - F2 (Pre-analysis plan): **DOWNGRADED to INFO** — not applicable to data infrastructure projects; pre-registration is for experiments
  - F3 (Stream A'): **COLLECT ASAP** — contemporaneity concern acknowledged
  - F4 (AI Census validation): **Claude agent will validate** — Katie pushes back on audit framing; "found in search" IS relevant from user perspective. Distinction needed: "talking about AI" vs "producing with AI"
  - M1 (Expand panel to 14,169): **KEEP 9,760** — data confirms exclusion is substantively correct (uncoded channels are 51% organizations, 13% teams, 13% broken, 9% AI bots; 0% overlap with individual entrepreneurs)
  - M2 (Stream D): **ADD ~20 MORE PATTERNS**, target 3-5K channels, multi-signal filtering post-hoc
  - M3 (Stream B): **EXPAND TO 25K** via expanded keyword searches (NOT category stratification). Standalone dataset for "who wins" research questions.
- **Critical framing correction from Katie:** This is NOT one research project. It's automated data infrastructure producing multiple datasets for multiple papers. The audit's single-paper framing was wrong.
- **Coded vs uncoded channel analysis:** Confirmed Katie's instinct. runBy field shows 100% of coded channels are individual creators. Uncoded are organizations (51%), teams (13%), broken (13%), AI bots (9%), and uncoded individuals (14%). Median observables nearly identical, but construct validity demands individual-only panel.
- **5 new sampling methods proposed and approved in principle:**
  1. Topic-Stratified Discovery (topicId parameter, 26 topic categories)
  2. Trending Tracker (chart=mostPopular, 51 region codes)
  3. Livestream Creators (eventType=completed)
  4. Shorts-First Creators (videoDuration=short)
  5. Creative Commons Educators (videoLicense=creativeCommon)
- **Storage/cadence decisions:**
  - Katie has 2 TB Google Drive — 19+ years of headroom
  - Weekly video stats on ALL panels: ~96-104 GB/year — approved
  - Channel stats daily: ~8.4 GB/year — trivial
  - Comment data: decision pending (full initial pull vs sampled)
- **Katie wants descriptive stream labels** replacing letter codes (e.g., "Intent Creators" not "Stream A")
- **No code written this session** — pure strategic design review
- What's next: next agent finalizes unified stream architecture, then implements code fixes (M4-M8) and new stream scripts

### Feb 17, 2026 — Afternoon [Charter Review + Corrections]

- **Reviewed new PROJECT_CHARTER.md** (created in Second Brain session). Verified framing: this project is data infrastructure, not a single paper.
- **Fixed charter inaccuracies:**
  - "First milestone" → "Current milestone" with clearer language separating charter (done) from outstanding stream/AI decisions (not done)
  - Added 3 missing Mac Mini services to automated services table (weekly video stats, sync-to-drive, health check — was only showing the 3 collection jobs)
  - Rewrote next actions to put actual decisions (A', C, AI flagger) first instead of buried
  - Added concrete enumeration progress to video enumeration milestone (gender gap ~5M+ rows, AI census ~8%)
- **Confirmed charter accuracy on:** dataset sizes, 3 collection service schedules, autonomy boundaries, relationship to gender gap paper repo
- **No phase change.** Approach audit still IN PROGRESS — charter is established but decisions on A', C, and AI designs remain.
- What's next: Katie makes audit decisions on remaining streams and AI research designs

### Feb 17, 2026 — Late Morning [Status Audit + Stream A Complete]

- **Verified Mac Mini deployment:** AI census daily stats already live, first run produced 50,005 rows (2026-02-17.csv). All 5 launchd services healthy.
- **Stream A COMPLETED overnight on Mac Mini:** 83,825 channels discovered across 46 keywords x 8 languages. Ran to full exhaustion of search space (short of 200K target — that was the actual yield ceiling). Screen session exited cleanly, no checkpoint = full completion.
- **Stream A channel_ids.csv NOT yet extracted** — needs processing before merge.
- **AI census video enumeration progressing:** 4,175/50,010 channels (8.3%), 85,454 video rows. ~3 days remaining at current rate.
- **Gender gap video enumeration still running:** 5M+ rows written.
- **PAUSED further production runs:** Katie auditing overall approach before Streams A', C, AI flagger, or new cohort merge. Existing automated services (gender gap + AI census daily stats) continue running.

### Feb 17, 2026 — Morning [AI Census Deployment COMPLETE + Video Enumeration Running]

- **AI census collection COMPLETE:** 50,010 channels in 34 min (45 terms x 2 sort orders x 18 months). Top yielders: artificial intelligence (2,859), AI tools (2,815), prompt engineering (2,786).
- **Mac Mini deployment COMPLETE:** launchd plist created (`com.youtube.ai-census-daily-channel-stats`), scheduled 9:00 UTC. SCP'd channel_ids.csv to Mac Mini, loaded service. Test run returned stats for 50,005 of 50,010 channels (5 likely terminated/private).
- **Video enumeration launched:** 50K channels, ~183K API units, checkpoint/resume. Running on laptop in background.
- **Handoff report written:** `HANDOFF_AI_CENSUS_DEPLOY.md` for agent continuity.
- **Three launchd services now active on Mac Mini:**
  1. Gender gap daily channel stats (8:00 UTC)
  2. New cohort daily channel stats (8:30 UTC)
  3. AI census daily channel stats (9:00 UTC)
- Next: verify first automated AI census run (Feb 18 after 9:00 UTC), monitor video enumeration, run AI flagger on completed inventory.

### Feb 16, 2026 — 10:55 PM [AI Census Scaled to 50K + Multi-Design Architecture]

- **Expanded AI_SEARCH_TERMS** from 17 → 45 terms (video/image gen, audio/music, coding, non-English, domain-specific)
- **Added AI_FLAG_KEYWORDS** to config.py: 101 keywords across 6 categories for video title matching (treatment variable for adoption diffusion design)
- **Updated discover_ai_creators.py**: `--months-back` (default 18, was 12), `--sort-orders` (default relevance,date), `--limit` (default 50K), safe append to existing output
- **Created extract_ai_channel_list.py**: extracts channel_ids.csv + channel_metadata.csv from census output for daily tracking
- **Created flag_ai_videos.py**: offline AI keyword flagger for video titles — flags ai_flag, ai_keywords_matched, ai_category per video
- **Launched scaled census**: 45 terms x 2 sort orders x 18-month lookback = 90 work units. 31K+ channels found in first 18 minutes. Running in background with checkpoint/resume.
- **Bug fix**: discover_ai_creators now always loads existing output before writing (prevents overwriting prior results when no checkpoint exists)
- Remaining after census completes: extract channel lists, deploy daily AI census tracking to Mac Mini, start video enumeration for census channels

### Feb 16, 2026 — 10:37 PM [Streams B+D Collected, Stream A Launched]
- **Ran Stream B (Benchmark) on Mac Mini:** 1,539 channels discovered across 6 vowel/generic queries. Heavy algorithm bias as expected: 742 channels >1M subs, 483 at 100K-1M. Median is top 0.01% of YouTube.
- **Ran Stream D (Casual) on Mac Mini:** 1,862 channels from 15 raw-filename queries. Top queries: Screen Recording (536), Untitled (384), IMG_ (232). Well under 25K target — that's the ceiling of what the API surfaces for these patterns.
- **Extracted channel_ids.csv** for both streams using Python csv module. Fixed `extract_channel_ids.sh` — the awk-based extraction broke on multiline descriptions in quoted CSV fields. Replaced with Python csv.DictReader.
- **Launched Stream A (Intent) in screen session** on Mac Mini: `screen -S stream_a`, `--limit 200000 --skip-first-video`. Running across 46 keywords in 8 languages. Checkpoint/resume enabled. ~765K API units.
- **Quota check:** ~648 units consumed today before Stream A launch. 1M+ remaining.
- **Note:** tmux not installed on Mac Mini; using `screen` instead for detached sessions.
- Stream D yielded far fewer than 25K target. The raw-filename search space is limited by what YouTube's API surfaces. 1,862 is a realistic population for this query strategy.
- What's next: Monitor Stream A. After completion, run A' and C on subsequent days. Then merge all channel lists and deploy cohort daily stats.

### Feb 16, 2026 — 09:30 PM [AI Census Audit + 50K Scaling Plan]
- **Audited AI census output (5,026 channels):** Median views = 897K (heavy algorithm bias, similar to Stream B). 30% have AI keywords in channel title/description (dedicated AI creators), 70% are general creators who made AI-adjacent videos. Top countries: India (1,093), US (1,053). Huge 2025 spike (1,150 channels = 23%).
- **Designed telescoping multi-design collection architecture:** 4 layers — (1) daily channel stats for 50K AI channels + 9.7K gender gap, (2) video inventory + AI flagging, (3) weekly video engagement on AI-flagged subset, (4) sampled comments. All three AI research designs (census, adoption diffusion, audience response) served by one data structure.
- **Approved plan for 50K scaling:** Expand search terms from 17 to ~47 (add specific tools: Runway, HeyGen, Pika, Suno, Stable Diffusion + non-English terms + domain-specific). Add sort order cycling (relevance + date). Extend time windows to 18 months. Estimated cost ~1.5M units over 1-2 days.
- **Plan file:** `.claude/plans/cached-baking-glade.md` — 7-step implementation plan with parallelization strategy for agents.
- What's next: Execute the 50K scaling plan (expand config, update script, run collection, build AI flagger, deploy to Mac Mini).

### Feb 16, 2026 — 09:15 PM [New Creator Cohort Streams A-D — Infrastructure Ready]
- **Added `--panel-name` flag to `daily_stats.py`**: output goes to `channel_stats/{panel_name}/YYYY-MM-DD.csv` when set, flat default when not (backwards compatible). Also adds panel-specific checkpoint files to avoid collisions.
- **Added checkpoint/resume to 3 large discovery scripts**: `discover_intent.py` (A), `discover_non_intent.py` (A'), `discover_random.py` (C). Saves progress after each keyword/prefix batch. Channels written incrementally to CSV. Interrupted runs resume from last checkpoint.
- **`config.get_daily_panel_path()`** now accepts `panel_name` param for subdirectory routing.
- Streams B and D are small enough to not need checkpoint/resume.
- All 5 syntax-checked, `--panel-name` tested end-to-end (subdirectory creation verified).
- **Plan file:** `.claude/plans/sharded-skipping-pie.md` — full 4-phase deployment plan with quota scheduling.
- What's next: Run Streams B+D (same day, ~35K units), then A/A'/C one per day.

### Feb 16, 2026 — 08:30 PM [AI Creator Census — COMPLETE]
- **Ran production AI Creator Census:** 5,026 unique channels discovered across 14 of 17 search terms (hit target before exhausting all terms).
- Output: `data/channels/ai_census/initial_20260217.csv` (33 columns, 5,026 rows, 0 nulls, 0 duplicates)
- Added **checkpoint/resume** to `discover_ai_creators.py`: incremental CSV writes + JSON checkpoint after each term. Fixed `datetime.utcnow()` deprecation warning.
- Quota consumed: estimated ~100K units (under 10% of daily limit). Ran in under 3 minutes.
- **Discovery keyword distribution:** AI voice (454), artificial intelligence (389), AI tutorial (388), prompt engineering (387), AI video editing (379), Sora AI (373), DALL-E (370), AI tools (366), agentic AI (342), generative AI (335), Claude Code (317), ChatGPT (316), AI automation (307), Midjourney tutorial (303)
- **Country distribution:** India (1,093), US (1,053), Unknown (1,345), GB (145), IT (140), PK (113), CA (98)
- **Overlap with gender gap panel:** 41 channels appear in both datasets
- What's next: Gender coding for AI census channels, AI adoption detection layer (keyword matching on video titles/descriptions)



## Feb 2026

### Feb 16, 2026 — 08:42 PM [Shell Script for Channel ID Extraction]
- **Built `scripts/extract_channel_ids.sh`** — utility script to extract channel_id column from any discovery output CSV and write clean channel list suitable for `daily_stats.py --channel-list`
- Features: automatic column detection, deduplication, sorted output, error handling (file checks, column validation), usage message
- Takes 2 args: INPUT_CSV and OUTPUT_CSV
- Output format: CSV with single "channel_id" column, sorted unique IDs
- Example usage: `./scripts/extract_channel_ids.sh data/channels/stream_b/initial_20260217.csv data/channels/stream_b/channel_ids.csv`
- Tested: usage message displays correctly when called with no args
- What's next: Use this script for Streams A-D channel list prep after discovery runs complete

### Feb 16, 2026 — 08:15 PM [Channel Stats Decoupled from Video Inventory]
- **Added `--channel-list` CLI arg to `daily_stats.py`** so channel-only mode reads from `channel_ids.csv` directly, bypassing the video inventory entirely. This unblocks daily channel stats collection while video enumeration is still in progress.
- New `load_channel_list()` method reads any CSV with a `channel_id` column. Falls back to inventory-based loading when `--channel-list` not provided (backward compatible).
- Validation logic updated: `--video-inventory` no longer required when `--mode channel` + `--channel-list` are both set. Still required for `--mode video` and `--mode both`.
- Guard added to `detect_and_add_new_videos()`: skips cleanly when no inventory path is set.
- **Tested on laptop:** 9,760 channels loaded, 9,672 stats collected (~50s). 88 channels returned not_found (terminated/deleted accounts).
- **Deployed to Mac Mini via SSH (192.168.86.48):**
  - `git pull` brought code up to date
  - Updated launchd plist: replaced `--video-inventory` with `--channel-list data/channels/gender_gap/channel_ids.csv`
  - Unloaded/reloaded plist, verified all 4 services in `launchctl list`
  - **Tested on Mac Mini:** 9,760 channels loaded, 9,672 stats collected (~100s). Output: `data/daily_panels/channel_stats/2026-02-17.csv`
- **Mac Mini now collecting full panel daily** (was only 2 channels before from partial inventory)
- What's next: Verify 3 AM launchd run produces 2026-02-18.csv. Continue video enumeration on laptop.

### Feb 16, 2026 — 07:55 PM [Mac Mini Deployed + Health Monitoring Built]
- **Deployed to Mac Mini via SSH** (192.168.86.48) — full Steps 1-7 from deployment guide
  - Cloned repo, installed deps (Python 3.9.6 on Mac Mini, not 3.14), copied config + data
  - Created and loaded 4 launchd services: daily-channel-stats, weekly-video-stats, sync-to-drive, health-check
  - Ran test collection: 2 channel stats collected (partial inventory on Mac Mini)
- **Built health check system** (`src/validation/health_check.py`) — 9 checks:
  channel freshness, channel completeness, video freshness, video completeness,
  log errors, inventory integrity, disk space, quota usage, stale checkpoints.
  Outputs HEALTHY/DEGRADED/FAILING. Supports --json. Runs daily at 12:00 UTC via launchd.
- **Built weekly digest** (`src/validation/weekly_digest.py`) — markdown summary of
  collection coverage, growth trends, data volume. Run manually or schedulable.
- **Fixed Mac Mini details:** IP was .41 (wrong), corrected to .48. Python is 3.9.6 not 3.14.
  Drive sync from laptop to Mac Mini can be stale — use scp for critical files.
- **Discovered Drive sync issue:** Files copied from Drive mount on Mac Mini had stale data
  (channel_ids.csv had 14,170 rows instead of 9,761). Used scp from laptop to push correct files.
- **Enumeration status:** 143/9760 channels done (~1.5%), still running on laptop.
  Once complete, scp inventory to Mac Mini for full production.
- Health check ran on Mac Mini: DEGRADED (expected — partial inventory, no video stats yet).
  All infrastructure checks pass (disk 37.6%, no errors, no stale checkpoints).
- What's next: Wait for enumeration, scp inventory, run full collection, verify 3 AM automation.

### Feb 16, 2026 — 09:45 PM [Production Launch + Mac Mini Handoff]
- **Regenerated channel_ids.csv** to 9,760 coded channels (filtered from 14,169 to only those with both gender + race)
- **Regenerated channel_metadata.csv** to match (9,760 rows with channel_id, perceivedGender, race, runBy, subscriberCount, viewCount)
- **Updated daily_stats.py** with `--mode channel|video|both` flag for dual-cadence collection
- **Launched video enumeration** on 9,760 channels (background, checkpoint/resume). ~80/9760 channels done at session end. Expected ~12M videos, ~245K API units total.
- **Created two launchd plists** (daily channel stats + weekly video stats). Created on laptop then unloaded — will be recreated with local paths on Mac Mini.
- **Wrote docs/PANEL_SCHEMA.md** — full dual-cadence schema documentation with field definitions, join examples, and storage projections
- **Wrote docs/MAC_MINI_DEPLOYMENT.md** — 9-step deployment guide for next agent. Covers: local-first I/O (EDEADLK avoidance), git clone, deps, config, data copy, plists with local paths, sync-to-drive script, testing, and troubleshooting.
- **Key insight from Second Brain:** Google Drive FUSE + launchd = deadlock. Must use local I/O on Mac Mini with rsync/osascript sync to Drive. Same pattern as Pat bot.
- Storage projection: ~40 GB/year (was 416 GB with daily + full panel). Quota: ~3.5% of daily limit average.
- What's next: Enumeration finishes (resume if interrupted). Next agent deploys to Mac Mini per docs/MAC_MINI_DEPLOYMENT.md.

### Feb 16, 2026 — 08:00 PM [Panel Design Decisions + Provenance]
- **DECISION: Panel restricted to 9,760 channels** with both gender AND race coded (excludes blank + undetermined). Uncoded channels lack identifiable creators, less analytically useful.
- **DECISION: Dual-cadence collection** — daily channel stats (tiny: ~195 API units/day, 1.1 MB/day), weekly video stats (~240K units, ~756 MB). daily_stats.py updated with `--mode channel|video|both` flag.
- Storage projections for coded panel: 269 GB/year (was 416 GB for full panel). Daily quota ~24% (was 37%).
- Added `source` column to `clean_baileys.py` — all channels tagged `source="infludata"` for provenance tracking
- Re-ran clean_baileys.py: all validations pass, 14,169 rows, 515 dupes removed
- What's next: regenerate channel_ids.csv for 9,760 coded subset, run enumeration, set up launchd

### Feb 16, 2026 — 07:21 PM [Infrastructure Slide Deck — Complete]
- Built 10-slide LaTeX Beamer deck (`output/youtube-longitudinal-infrastructure-deck.tex`) documenting the full data collection infrastructure
- Custom theme: navy/amber/slate palette, 16:9 aspect ratio, progressive reveal overlays
- Covers: two research programs, panel composition (14,169 channels with gender/race breakdown), three-dataset architecture (TikZ flow diagram), schemas with sample data rows, 5-stream sampling design, AI Creator Census (17 terms + 3 research designs), future enrichment pipeline, quota budget (29,300 units/day = 2.9%)
- Full deck-compile protocol: 3 compilation passes, second-agent narrative review, third-agent graphics audit
- Final PDF: 19 pages (with overlays), 0 overfull hbox/vbox warnings
- Fixes applied from reviews: woman % 24.4→24.5 (rounding), "parallel"→"same run" on TikZ arrow, clarified 7-field schema label
- What's next: Katie reviews deck; production runs still awaiting approval

### Feb 16, 2026 — 07:15 PM [Status Review + Slide Deck Prompt]
- Confirmed all 4 agents completed and all scripts test-verified
- Wrote agent prompt for infrastructure overview slide deck (Beamer, 10-12 slides)
- Identified next session priorities: (1) full video enumeration, (2) first daily stats run, (3) launchd automation, (4) AI Creator Census
- What's next: Run enumeration in new session, then set up daily automation

### Feb 16, 2026 — 06:41 PM [Gender Gap Panel — Full Infrastructure Build]
- Built complete gender gap panel infrastructure via 4-agent parallel strategy (A: data prep, B: API infra, C: collection scripts, D: AI census)
- **Data prep (Agent A):**
  - Created `src/collection/clean_baileys.py` — parses Bailey's xlsx with openpyxl header-based lookup, fixes 6 race typos, deduplicates 515 duplicate rows → 14,169 unique channels
  - Produced 3 output files: `data/processed/gender_gap_panel_clean.csv` (30 cols), `data/channels/gender_gap/channel_ids.csv`, `data/channels/gender_gap/channel_metadata.csv`
  - Updated `src/config.py` with 9 new paths, AI_SEARCH_TERMS (17 terms), 4 new schemas, get_daily_panel_path() helper
- **API infrastructure (Agent B):**
  - Added `get_all_video_ids()` to youtube_api.py — full playlist pagination with checkpoint/resume
  - Added `get_video_stats_batch()` — lean video stats fetch (part="statistics" only)
  - Added quota tracking to `execute_request()` — logs to data/logs/quota_YYYYMMDD.csv (backward compatible)
  - Created `__init__.py` for panels/, enrichment/, analysis/ modules
- **Collection scripts (Agent C):**
  - Created `src/collection/enumerate_videos.py` — builds video inventory with checkpoint/resume, UC→UU playlist conversion
  - Created `src/panels/daily_stats.py` — DailyStatsCollector class with 4-step pipeline (video stats → channel stats → save → new video detection)
- **AI census (Agent D):**
  - Created `src/collection/discover_ai_creators.py` — video-first search across 17 AI terms, 12-month time windows, order="relevance"
- **Test verification results (all passing):**
  - clean_baileys: 14,169 rows, all validations pass, race typos corrected
  - enumerate_videos --test --limit 2: 1,038 videos from 2 channels, correct 5-col schema
  - daily_stats --test: 250 video stats + 2 channel stats, daily panel files correct
  - discover_ai_creators --test --limit 5: 107 AI channels found
  - Backward compatibility: discover_intent.py and sweep_channels.py still import correctly
  - Quota tracking: data/logs/quota_20260216.csv being written
- Installed all Python deps for Python 3.14: openpyxl, pyyaml, pandas, tqdm, isodate, google-api-python-client
- What's next: Katie approves full video enumeration run, then start daily panel collection

### Feb 16, 2026 — 04:30 PM [AI Design Integration — Planning & Scope Expansion]
- Read and evaluated design document (`SECOND_BRAIN/03-research/YOUTUBE_DATASET_DESIGN.md`) — three new research designs: AI Creator Census, AI Adoption Diffusion Panel, Audience Response
- Audited all existing Python scripts against proposed architecture. Mapped reusable code vs. gaps.
- Analyzed both raw data files: confirmed 14,169 unique channels, 100% overlap between Infludata and Bailey's lists
- **Corrected misdiagnosis:** Bailey's xlsx does NOT have 4,097 misaligned rows. Those channels have BLANK gender/race (uncoded). Apparent misalignment was from parsing xlsx cells positionally instead of by cell reference.
- **SCOPE EXPANSION (Katie-approved):** This repo now owns longitudinal data collection on the 14,169 gender gap channels. Gender gap paper analysis stays in CH2. Updated CLAUDE.md.
- Resolved all 9 methodological decisions with Katie: all 14,169 channels, broad AI search terms, keyword-first AI detection, randomized comment sampling, partitioned CSVs to start
- Created new directory structure: `src/panels/`, `src/enrichment/`, `src/analysis/`, `data/channels/gender_gap/`, `data/channels/ai_census/`, `data/video_inventory/`, `data/daily_panels/{video_stats,channel_stats}/`, `data/transcripts/`, `data/comments/`, `logs/`
- Wrote full implementation plan: `.claude/plans/cached-knitting-puffin.md`
- Wrote agent handoff document: `docs/AGENT_HANDOFF.md`
- What's next: Hand off to parallel agents for implementation (data prep, API infrastructure, collection scripts, AI census)

### Feb 16, 2026 — 02:15 PM [Project Restructuring]
- Flattened project from triple-nested `youtube-longitudinal/youtube-longitudinal/youtube-longitudinal/` to root-level layout
- Production code (`src/`) moved from Level 3 to root; all `Path(__file__)` relative paths verified working
- Created project CLAUDE.md with session protocol, safety rules, coding standards
- Added `.claude/rules/` (01-session-protocol, 02-data-collection)
- Added `.claude/skills/log-update/` for session-end commit+push workflow
- Moved 4 existing analysis skills (stata-regression, r-econometrics, python-panel-data, referee-audit) to root `.claude/skills/`
- Detailed docs from Level 2 promoted to root (PROJECT_MASTER_PLAN, PROGRESS_LOG, TECHNICAL_SPECS, DECISION_LOG)
- Reference docs (API variable ref, sampling experiments, quota analysis) moved to `docs/`
- Updated `.gitignore` (comprehensive: data, secrets, artifacts, archive, output)
- Archived: v1 legacy scripts, superseded rule files (AI_RULES, ANTIGRAVITY_RULES, MY_WORKFLOW), loose conversation/template files, stray 656MB .dta file (confirmed duplicate of dissertation copy)
- Removed nested `.git/` repository (history captured in commit message)
- Resolved merge conflict with remote (b527cb0 production commit)
- What's next: install Python deps, then start production collection

### Feb 02, 2026 — 05:30 PM (Late Evening Session)
**Session Focus:** Full Production Pipeline Implementation

**Work Completed:**
- **Complete Rewrite:** Built production-grade modular architecture with 15 new files
- **Configuration System:** Created `config.py` with comprehensive constants:
  - 8-language keyword mappings (Intent + Non-Intent)
  - Full YouTube topic hierarchy (200+ topics with decoding)
  - Stream-specific directories and targets
  - Data schemas for channels, videos, sweeps
- **Enhanced API Module:** Upgraded `youtube_api.py` with:
  - Full topic extraction and decoding (hierarchical topics)
  - Comprehensive channel details (28 fields for initial, 8 for sweeps)
  - Video batch fetching with Shorts classification
  - New video detection for longitudinal tracking
  - Search helpers with pagination
- **Collection Scripts (5):**
  - `discover_intent.py` — Stream A: Intent creators (200k target)
  - `discover_non_intent.py` — Stream A': Non-intent creators (200k target)
  - `discover_benchmark.py` — Stream B: Algorithm favorites (2k)
  - `discover_random.py` — Stream C: Random prefix (50k)
  - `discover_casual.py` — Stream D: Casual uploaders (25k)
- **Sweep System:**
  - `sweep_channels.py` — Main sweep with checkpoint/resume
  - `detect_new_videos.py` — New video detection logic
- **Validation:**
  - `validate_sweep.py` — Data quality checks (duplicates, anomalies, policy changes)
- **Testing:** 
  - Stream A test: 62 Hindi channels collected successfully
  - Stream D test: 15 casual channels collected successfully
  - Validation: 0 errors, all systems operational

**Sample Size Decision:**
- Updated Stream A and A' from 25k → **200k each** to handle attrition
- Rationale: Early-stage creator dropout is 50-70%; need huge buffer
- Expected English channels: 50k-80k per stream (sufficient for analysis)

**Quota Impact:**
- Initial collection (2 streams, 400k channels): ~808k units (fits in 1 day)
- Recommendation: Use `--skip-first-video` flag for speed
- Can enrich with first video data later if needed

**Directory Structure Created:**
```
youtube-longitudinal/
├── src/
│   ├── config.py
│   ├── youtube_api.py
│   ├── collection/
│   │   ├── discover_intent.py
│   │   ├── discover_non_intent.py
│   │   ├── discover_benchmark.py
│   │   ├── discover_random.py
│   │   └── discover_casual.py
│   ├── sweeps/
│   │   ├── sweep_channels.py
│   │   └── detect_new_videos.py
│   └── validation/
│       └── validate_sweep.py
└── data/
    ├── channels/
    │   ├── stream_a/
    │   ├── stream_a_prime/
    │   ├── stream_b/
    │   ├── stream_c/
    │   └── stream_d/
    ├── videos/
    └── logs/
```

**Files Created:**
- `src/config.py` (700+ lines)
- `src/youtube_api.py` (rewritten, 1000+ lines)
- `src/collection/discover_intent.py`
- `src/collection/discover_non_intent.py`
- `src/collection/discover_benchmark.py`
- `src/collection/discover_random.py`
- `src/collection/discover_casual.py`
- `src/sweeps/sweep_channels.py`
- `src/sweeps/detect_new_videos.py`
- `src/validation/validate_sweep.py`
- Module `__init__.py` files (3)

**Key Design Features:**
- **Topic Support:** Full YouTube hierarchical topics (not just categories)
- **Language Tracking:** `discovery_language` field tracks which language found each channel
- **Shock Readiness:** All policy-relevant fields included (made_for_kids, privacy_status, etc.)
- **Checkpoint/Resume:** Sweeps can be interrupted and resumed
- **Validation:** Automated quality checks for data integrity

**Next Steps (Tomorrow):**
1. Start Stream A collection (200k channels, ~404k units)
2. Start Stream A' collection (200k channels, ~404k units)
3. Consider using `--skip-first-video` for initial speed
4. Set up sweep schedule once initial collection complete

---

### Feb 02, 2026 — 04:30 PM (Evening Session)
**Session Focus:** Comprehensive Sampling Methodology Validation & Quad-Stream Design

**Work Completed:**
- **Experiment Battery:** Ran 6 systematic experiments testing sampling strategies:
  - EXP-001/003: Bias Profile Comparison (Vowels vs Raw vs Random Prefix)
  - EXP-002/010: New Creator Yield Rates (Intent vs Non-Intent keywords)
  - EXP-005: Channel ID Enumeration (result: not viable)
  - EXP-006: Language Bias Detection (8 languages tested)
  - EXP-007: Region Code Impact
  - EXP-008: Pagination Depth Bias
- **Critical Discovery:** English-only keywords miss 86% of findable new creators. Hindi has highest yield (35.3%).
- **Design Evolution:** Upgraded from Triple-Stream to Quad-Stream design with Stream D (Amateur Baseline).
- **Documentation Created:**
  - `SAMPLING_EXPERIMENTS.md` — Full experiment log with results
  - `QUOTA_ANALYSIS.md` — Sample size and polling frequency analysis
  - `test_sampling_battery.py` — Comprehensive test script
  - `test_language_pagination.py` — Language and pagination experiments
  - `discover_amateur.py` — Stream D collection script
  - `discover_cohort_multilingual.py` — Enhanced 8-language cohort discovery

**Key Findings:**
| Finding | Evidence | Implication |
|---------|----------|-------------|
| Vowel search massively biased | 1.16M median views, 94% big channels | Relabeled as "Algorithm Favorites" |
| English misses 86% of creators | 38 vs 271 across 8 languages | MUST use multilingual |
| Hindi highest yield | 35.3% vs 30.9% English | Prioritize Hindi |
| Pagination doesn't help | Page 2 higher views than Page 1 | Abandon strategy |
| Polling is cheap | 130k channels = 2,600 units/day | Daily polling feasible |

**Quota Analysis Summary:**
- Recommended panel: 130,000 channels (50k A + 10k B + 50k C + 20k D)
- Daily polling cost: 2,600 units (0.26% of quota)
- Collection budget: 500,000 units/day
- 80%+ quota remains for flexibility/experiments

**Files Created/Modified:**
- `SAMPLING_EXPERIMENTS.md` (Created)
- `QUOTA_ANALYSIS.md` (Created)
- `TECHNICAL_SPECS.md` (Major update — Quad-Stream)
- `PROJECT_MASTER_PLAN.md` (Updated findings & design)
- `src/test_sampling_battery.py` (Created)
- `src/test_language_pagination.py` (Created)
- `src/discover_amateur.py` (Created)
- `src/discover_cohort_multilingual.py` (Created)
- `config/config.yaml` (Created with API key)

**Next Steps (Production Ramp-Up):**
1. Run 24-hour multilingual cohort collection
2. Run amateur baseline collection
3. Set up automated daily polling
4. Design hybrid polling tiers (hot/warm/cold)

---

### Feb 02, 2026 — 03:00 PM
**Session Focus:** Methodological Pivot to Triple-Stream Design

**Work Completed:**
- **Bias Diagnostics:** Ran empirical tests comparing "Vowel Search" (Median Views 652k) vs "Random Prefix" (Median Views 22).
- **Sampling Strategy:** Validated that a single "Random" sample is insufficient.
- **Design Pivot:** Adopted "Triple-Stream" approach (Intentional A + Visible B + Deep Random C).
- **Scripting:** Created `discover_cohort.py` (Stream A) and `discover_random.py` (Stream B initial version).
- **Documentation:** Consolidated artifacts into `PROJECT_MASTER_PLAN.md` and `TECHNICAL_SPECS.md`.

**Key Findings:**
- **"Filing for Videos" (Zhou et al.):** Confirmed as reference for Random Prefix Sampling.
- **Quota Capacity:** We have effectively infinite quota (1M/day) for this scale, allowing us to run all three streams simultaneously.

**Decisions Made:**
- **Triple-Stream Design:** (See `DECISION_LOG.md` entry 001). Chosen to control for survivorship bias while checking market competitiveness.
- **Vowel Rotation:** Used for Stream B to ensure linguistic coverage of the "Visible" market.

**Files Created/Modified:**
- `PROJECT_MASTER_PLAN.md`: Created (Canonical roadmap).
- `TECHNICAL_SPECS.md`: Created (Canonical specs).
- `DECISION_LOG.md`: Created (Canonical decision record).
- `src/test_bias_deep_dive.py`: Created (Diagnostic tool).

**Next Steps (Immediate):**
1. Clean up redundant documentation (`implementation_plan.md`, `sampling_methodology.md`).
2. Finalize script names.

### Feb 02, 2026 — 03:15 PM
**Session Focus:** Deep Review of Sampling Strategy & Script Logic

**Work Completed:**
- **Strategy Deep Dive:** Conducted literature review on "Snowball Sampling" vs "Random Prefix" vs "External Lists." Created `sampling_strategy_review.md`.
- **Code Audit:** Analyzed `discover_cohort.py` and `discover_visible.py` to document exact search keywords and query logic (`q` searches snippets, not just titles).
- **Validation:** Confirmed "Stream C" (Deep Random) logic: inherently captures 99% nonsense to prove the 1% signal is distinct.
- **Cleanup:** Renamed `discover_random.py` -> `discover_visible.py` to clarify its role as "Market Baseline."
- **Deleted:** Redundant artifacts (`task.md`, `implementation_plan.md`, etc.) after consolidation.

### Feb 02, 2026 — 03:30 PM
**Session Focus:** Project Setup & Git Initialization

**Work Completed:**
- **Git Initialization:** Initialized local repository and created `.gitignore` to exclude sensitive/large files.
- **GitHub Link:** Successfully linked local repo to `apkerk/youtube-longitudinal` and pushed `main` branch.
- **Documentation Audit:** Created missing standard files (`MY_WORKFLOW.md`, `writing-patterns.md`, `deck.md`) from templates to ensure full compliance with the research system.
- **Folder Structure:** created `drafts/` and `archive/` directories.

**Files Created/Modified:**
- `.gitignore`: Created.
- `MY_WORKFLOW.md`: Created.
- `writing-patterns.md`: Created.
- `deck.md`: Created.

**Next Steps (Immediate):**
1. 🛑 USER ACTION REQUIRED: Run the 3-step validation suite to confirm network access.
2. Set up `launchd` for daily automation.

**Key Findings:**
- **Stream A Keywords:** Validated list (`Welcome`, `Intro`, `Vlog 1`) targets intentionality.
- **Stream C Logic:** Confirmed that "Nonsense" results are a *feature*, not a bug, providing a true Zero Baseline.
- **Alternatives Rejected:** "Snowball Sampling" rejected due to Homophily Bias (echo chambers).

**Files Created/Modified:**
- `sampling_strategy_review.md`: Created (Comparative analysis).
- `src/discover_visible.py`: Renamed and updated docstrings.
- `src/discover_deep_random.py`: Created.

**Next Steps (Immediate):**
1. 🛑 USER ACTION REQUIRED: Run the 3-step validation suite to confirm network access.
2. Set up `launchd` for daily automation.
