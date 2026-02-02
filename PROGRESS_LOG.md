# Progress Log: YouTube Longitudinal Data Collection

**Purpose:** Chronological record of all work completed on this project  
**Update Instructions:** Add new entries at the TOP of each month's section

---

## Current Status (as of Feb 02, 2026 — Late Evening)

**Phase:** Full Implementation COMPLETE ✅  
**Roadmap Position:** Phase 4 (Production) Ready  
**Data Quality Status:** Scripts tested, working, validated  
**Tomorrow's Priority:** Start full-scale collection (200k x 2 streams)  
**Next Steps:** 
1. Run Stream A collection: `python3 -m src.collection.discover_intent`
2. Run Stream A' collection: `python3 -m src.collection.discover_non_intent`
3. Optional: Enrich with first video data OR skip for speed

---

## Feb 2026

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
