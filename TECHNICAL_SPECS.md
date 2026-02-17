# Technical Specifications — YouTube Longitudinal Project

**Purpose:** Centralized technical details for replication and onboarding  
**Last Updated:** Feb 02, 2026 (Late Evening - Production Implementation)  
**Use:** Reference when running collection scripts or analyzing data

---

## PROJECT OVERVIEW

- **Project:** YouTube Longitudinal Study (New Creator Virality)
- **Type:** Quantitative / Big Data
- **Primary Software:** Python 3.12 (EXTREMELY STRICT RULES)
- **API:** YouTube Data API v3 (Quota: 1,010,000 units/day)

---

## SAMPLING SPECIFICATIONS (5-Stream Production Design)

### Stream A: Intent Creators (Treatment) — MULTILINGUAL
*   **Target:** 200,000 new creators signaling entrepreneurial intent across 8 languages
*   **Method:** `search.list(q=INTENT_KEYWORDS, type='video', order='date')` -> Filter by channel creation date
*   **Script:** `src/collection/discover_intent.py`
*   **Languages (by yield rate):**
    1. Hindi (35.3% yield) — highest!
    2. English (30.9%)
    3. Spanish (29.3%)
    4. Japanese (24.5%)
    5. German (24.0%)
    6. Portuguese (23.1%)
    7. Korean (22.5%)
    8. French (18.3%)
*   **Intent Keywords (46 total across 8 languages):**
    - English: "Welcome to my channel", "My first video", "Introduction", "Intro", etc.
    - Hindi: "Mere channel mein aapka swagat hai", "Mera pehla video", etc.
    - Plus 6 more languages
*   **Key Finding (EXP-006):** English-only misses 86% of findable new creators. Multilingual expands by 7.1x.
*   **Filter Logic:**
    *   Search for videos with intent keywords
    *   Extract channel IDs
    *   **KEEP IF:** Channel `published_at` >= 2026-01-01
*   **Expected English Yield:** 50k-80k channels (25-40% of total)
*   **Collection Cost:** ~404,000 units (initial)
*   **Sweep Cost:** ~4,000 units (weekly)

### Stream A': Non-Intent Creators (Comparison Group) — MULTILINGUAL
*   **Target:** 200,000 new creators who start with content (not intros)
*   **Method:** `search.list(q=CONTENT_KEYWORDS, type='video', order='date')` -> Same date filter
*   **Script:** `src/collection/discover_non_intent.py`
*   **Content Keywords (48 total across 8 languages):**
    - English: "gameplay", "let's play", "tutorial", "recipe", "review", "unboxing", etc.
    - Hindi: "gameplay hindi", "tutorial hindi", "recipe hindi", etc.
    - Plus 6 more languages
*   **Use Case:** Causal inference comparison for effect of intentional launching strategies
*   **Collection Cost:** ~404,000 units (initial)
*   **Sweep Cost:** ~4,000 units (weekly)

### Stream B: Algorithm Favorites (Benchmark)
*   **Target:** 2,000 channels that YouTube's algorithm surfaces
*   **Method:** `search.list(q=VOWELS, type='video', order='relevance')`
*   **Script:** `src/collection/discover_benchmark.py`
*   **Keywords:** `a`, `e`, `i`, `o`, `u`, `video`
*   **⚠️ CRITICAL FINDING (EXP-003):**
    *   Median Views: **1,161,938** (extremely biased toward popular content)
    *   94.4% are "big channels" (>1k subs)
    *   This is the TOP 0.01% of YouTube, not the "market"
*   **Use Case:** Benchmark what new creators compete against for visibility
*   **Collection Cost:** ~12,000 units (initial)
*   **Sweep Cost:** ~40 units (monthly)

### Stream C: Searchable Random (Population Baseline)
*   **Target:** 50,000 channels via random prefix sampling
*   **Method:** Random Prefix Sampling (Zhou et al., 2011)
*   **Script:** `src/collection/discover_random.py`
*   **Keywords:** Randomly generated 3-character alphanumeric strings (e.g., `x7z`, `1a2`, `k9m`)
*   **Bias Profile (EXP-003):**
    *   Median Views: 305 (5,400x lower than vowel search)
    *   39.3% big channels (lowest of all strategies)
*   **Use Case:** True population baseline for survivorship analysis
*   **Collection Cost:** ~300,000 units (initial)
*   **Sweep Cost:** ~1,000 units (monthly)

### Stream D: Casual Uploaders (Amateur Control)
*   **Target:** 25,000 channels with raw/default file names
*   **Method:** `search.list(q=RAW_FILE_PATTERNS, type='video', order='date')`
*   **Script:** `src/collection/discover_casual.py`
*   **Keywords (15 patterns):** `IMG_`, `MVI_`, `DSC_`, `MOV_`, `VID_`, `DSCF`, `GOPR`, `DJI_`, `P_`, `Screen Recording`, `Untitled`, `New Recording`, `20260`, `video_2026`, `Video 2026`
*   **Bias Profile (EXP-003):**
    *   Median Views: 214
    *   59% big channels
*   **Use Case:** Contrast strategic vs casual uploading behavior
*   **Collection Cost:** ~150,000 units (initial)
*   **Sweep Cost:** ~500 units (weekly)

---

## EXPERIMENTAL VALIDATION (Feb 02, 2026)

All sampling strategies have been empirically tested. See `SAMPLING_EXPERIMENTS.md` for full details.

### Key Findings

| Finding | Evidence | Implication |
|---------|----------|-------------|
| Vowel search is MASSIVELY biased | Median 1.16M views, 94% big channels | Stream B = algorithm favorites only |
| Random prefix is least biased | Median 305 views, 39% big channels | Best for unbiased baseline |
| English misses 86% of new creators | 38 vs 271 across 8 languages | MUST use multilingual |
| Hindi has highest yield (35.3%) | Higher than English (30.9%) | Prioritize Hindi sampling |
| Pagination doesn't reduce bias | Page 2 had higher views than Page 1 | Abandon pagination strategy |
| Channel ID enumeration not viable | 0/100 hits | ID space too sparse |

---

## DATA STRUCTURES

### Channel Initial Collection (28 fields)
| Variable | Type | Source | Definition |
|----------|------|--------|------------|
| `channel_id` | String | API | Unique YouTube Channel ID (UC...) |
| `title` | String | API | Channel Display Name |
| `description` | String | API | Channel description (truncated to 5000 chars) |
| `custom_url` | String | API | Custom URL (if set) |
| `published_at` | DateTime | API | Channel creation timestamp |
| `view_count` | Int | API | Total channel views |
| `subscriber_count` | Int | API | Subscriber count |
| `video_count` | Int | API | Total uploaded videos |
| `hidden_subscriber_count` | Boolean | API | Whether subs are hidden |
| `country` | String | API | Channel country (if set) |
| `default_language` | String | API | Primary language (e.g., 'en', 'hi', 'es') |
| `topic_categories_raw` | String | API | Pipe-delimited Wikipedia topic URLs |
| `topic_ids` | String | API | Pipe-delimited YouTube topic IDs |
| `topic_1` | String | Derived | Primary topic (decoded) |
| `topic_2` | String | Derived | Secondary topic (decoded) |
| `topic_3` | String | Derived | Tertiary topic (decoded) |
| `topic_count` | Int | Derived | Number of topics assigned |
| `made_for_kids` | Boolean | API | Made for kids flag (policy-relevant) |
| `privacy_status` | String | API | Privacy status |
| `long_uploads_status` | String | API | Long upload capability |
| `is_linked` | Boolean | API | Linked to external account |
| `keywords` | String | API | Channel keywords |
| `localization_count` | Int | API | Number of language localizations |
| `localizations_available` | String | Derived | Pipe-delimited language codes |
| `profile_picture_url` | String | API | Profile picture URL |
| `uploads_playlist_id` | String | API | Uploads playlist ID (UU...) |
| `first_video_date` | DateTime | API | Date of first video (if enriched) |
| `first_video_id` | String | API | ID of first video (if enriched) |
| `first_video_title` | String | API | Title of first video (if enriched) |
| `stream_type` | String | System | Stream identifier (stream_a, stream_b, etc.) |
| `discovery_language` | String | System | Language of discovery keyword |
| `discovery_keyword` | String | System | Specific keyword that found this channel |
| `scraped_at` | DateTime | System | Collection timestamp |

### Channel Sweep (8 fields - streamlined)
| Variable | Type | Definition |
|----------|------|------------|
| `channel_id` | String | Channel ID |
| `view_count` | Int | Current view count |
| `subscriber_count` | Int | Current subscriber count |
| `video_count` | Int | Current video count |
| `made_for_kids` | Boolean | Current made_for_kids status |
| `status` | String | 'active' or 'not_found' |
| `made_for_kids_changed` | Boolean | Whether MFK flag changed since last sweep |
| `scraped_at` | DateTime | Sweep timestamp |

### Video Details (24 fields)
| Variable | Type | Definition |
|----------|------|------------|
| `video_id` | String | Video ID |
| `channel_id` | String | Parent channel ID |
| `title` | String | Video title |
| `description` | String | Video description (truncated) |
| `published_at` | DateTime | Upload timestamp |
| `view_count` | Int | View count |
| `like_count` | Int | Like count |
| `comment_count` | Int | Comment count |
| `duration` | String | ISO 8601 duration |
| `duration_seconds` | Int | Duration in seconds |
| `is_short` | Boolean | Whether video is a Short (≤60s) |
| `category_id` | Int | Video category ID |
| `category_name` | String | Video category name (decoded) |
| `tags` | String | Pipe-delimited tags |
| `hashtags` | String | Pipe-delimited hashtags |
| `hashtag_count` | Int | Number of hashtags |
| `definition` | String | Video quality (hd/sd) |
| `dimension` | String | 2d/3d |
| `caption` | Boolean | Whether captions available |
| `licensed_content` | Boolean | Licensed content flag |
| `content_rating_yt` | String | YouTube content rating |
| `region_restriction_blocked` | String | Blocked countries (pipe-delimited) |
| `region_restriction_allowed` | String | Allowed countries (pipe-delimited) |
| `trigger_type` | String | Why video was collected |
| `scraped_at` | DateTime | Collection timestamp |

---

## FILE LOCATIONS

### Collection Scripts (Production)
| Script | Stream | Purpose | Target |
|--------|--------|---------|--------|
| `src/collection/discover_intent.py` | A | Intent creators (8 languages) | 200k |
| `src/collection/discover_non_intent.py` | A' | Non-intent creators (8 languages) | 200k |
| `src/collection/discover_benchmark.py` | B | Algorithm favorites | 2k |
| `src/collection/discover_random.py` | C | Random prefix sampling | 50k |
| `src/collection/discover_casual.py` | D | Casual uploaders | 25k |

### Sweep & Validation Scripts
| Script | Purpose |
|--------|---------|
| `src/sweeps/sweep_channels.py` | Longitudinal data collection with new video detection |
| `src/sweeps/detect_new_videos.py` | New video detection logic |
| `src/validation/validate_sweep.py` | Data quality checks and validation |

### Legacy/Experiment Scripts
| Script | Purpose |
|--------|---------|
| `src/test_sampling_battery.py` | Comprehensive bias profiling (experiments) |
| `src/test_language_pagination.py` | Language + pagination experiments |
| `src/discover_cohort_multilingual.py` | Original multilingual prototype |
| `src/discover_amateur.py` | Original amateur prototype |

### Data Structure
```
data/
├── channels/
│   ├── stream_a/          # Intent creators
│   │   ├── initial_YYYYMMDD.csv
│   │   └── sweep_YYYYMMDD.csv
│   ├── stream_a_prime/    # Non-intent creators
│   ├── stream_b/          # Benchmark
│   ├── stream_c/          # Random
│   └── stream_d/          # Casual
├── videos/
│   └── new_videos_YYYYMMDD.csv
└── logs/
    └── discover_*_YYYYMMDD.log
```

---

## QUOTA ALLOCATION

### Initial Collection (Production)
| Activity | Units | Notes |
|----------|-------|-------|
| Stream A (200k) | ~404,000 | Can be done in 1 day |
| Stream A' (200k) | ~404,000 | Can be done in 1 day |
| Stream B (2k) | ~12,000 | Quick |
| Stream C (50k) | ~300,000 | 1 day |
| Stream D (25k) | ~150,000 | 1 day |
| **TOTAL** | **~1,270,000** | Requires 2 days |

**Recommended Schedule:**
- **Day 1:** Stream A (404k) + Stream A' (404k) = 808k units ✅
- **Day 2:** Stream C (300k) + Stream D (150k) + Stream B (12k) = 462k units ✅

### Sweep Costs (Steady-State)
| Stream | Channels | Weekly | Monthly |
|--------|----------|--------|---------|
| A | 200,000 | 4,000 units | ~1,000 units |
| A' | 200,000 | 4,000 units | ~1,000 units |
| B | 2,000 | - | 40 units |
| C | 50,000 | - | 1,000 units |
| D | 25,000 | 500 units | ~150 units |
| **TOTAL** | **477,000** | **8,500/week** | **3,190/month** |

**Key Insight:** Sweeps are extremely cheap. Even weekly sweeps of 400k channels = <1% of daily quota.

---

## REFERENCE DOCUMENTS

| Document | Purpose |
|----------|---------|
| `docs/SAMPLING_ARCHITECTURE.md` | **Canonical architecture doc: all 12 streams, justifications, research designs** |
| `SAMPLING_EXPERIMENTS.md` | Full experiment log with results |
| `QUOTA_ANALYSIS.md` | Sample size & polling frequency analysis |
| `DECISION_LOG.md` | Methodological decisions with rationale |
| `PROJECT_MASTER_PLAN.md` | Roadmap and research questions |
