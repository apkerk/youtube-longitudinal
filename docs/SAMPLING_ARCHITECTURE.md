# Sampling Architecture: YouTube Longitudinal Data Collection

**Purpose:** Single canonical reference for all streams, sampling methodologies, justifications, and research designs
**Last Updated:** Feb 17, 2026
**Use:** Evaluate each stream's design rigor, identify gaps, and guide production decisions

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [New Creator Cohort (5 Core Streams)](#2-new-creator-cohort-5-core-streams)
3. [Gender Gap Longitudinal Panel](#3-gender-gap-longitudinal-panel)
4. [AI Research Infrastructure (4 Designs)](#4-ai-research-infrastructure-4-designs)
5. [Proposed Future Streams (5 Expansion Streams)](#5-proposed-future-streams-5-expansion-streams)
6. [Experimental Validation Evidence](#6-experimental-validation-evidence)
7. [Quota Budget Summary](#7-quota-budget-summary)
8. [Collection Cadence and Data Schemas](#8-collection-cadence-and-data-schemas)
9. [Key Design Decisions and Rationale](#9-key-design-decisions-and-rationale)
10. [Known Limitations and Open Questions](#10-known-limitations-and-open-questions)

---

## 1. Architecture Overview

This project collects longitudinal YouTube data for two research programs through 12 data streams (7 active/ready, 5 proposed).

**Research Program 1: New Creator Cohort**
Five streams designed to capture the full distribution of new YouTube channels created in 2026. Enables causal inference about early-stage creator strategy by comparing intentional launchers against multiple baselines with known bias profiles.

**Research Program 2: Gender Gap Longitudinal Panel**
Daily tracking of 9,760 established channels from the Infludata/Bailey's dataset, plus an AI Creator Census of 50,010 channels. Supports four AI research designs that exploit within-creator variation and staggered adoption timing.

**Unifying Logic:** Each stream in Program 1 captures a different slice of the new-creator population. Each design in Program 2 answers a different causal question about AI adoption and gender dynamics. The streams are standalone datasets that can be analyzed independently or combined.

### Stream Summary Table

| # | Stream Name | Population | Target N | Status | Collection Cadence |
|---|-------------|-----------|----------|--------|-------------------|
| 1 | Intent Creators | New channels with entrepreneurial launch signals | 200K (actual: 83,825) | COLLECTED | Daily channel stats |
| 2 | Non-Intent Creators | New channels that start with content, no intro | 200K | APPROVED, not yet run | Daily channel stats |
| 3 | Algorithm Favorites | Channels YouTube's search algorithm surfaces | 25K (actual: 1,539) | COLLECTED (expansion approved) | Monthly sweep |
| 4 | Searchable Random | Channels found via random prefix search | 50K | APPROVED, not yet run | Monthly sweep |
| 5 | Casual Uploaders | Channels with raw/default filenames | 3-5K (actual: 1,862) | COLLECTED (expansion approved) | Weekly sweep |
| 6 | Gender Gap Panel | Established channels with coded gender + race | 9,760 | LIVE (daily tracking) | Daily channel, weekly video |
| 7 | AI Creator Census | Channels producing AI-related content | 50,010 | LIVE (daily tracking) | Daily channel, weekly video |
| 8 | Topic-Stratified Discovery | Channels sampled across 26 YouTube topic categories | ~30-40K | PROPOSED | TBD |
| 9 | Trending Tracker | Channels appearing on trending charts | Accumulating daily | PROPOSED | Daily discovery |
| 10 | Livestream Creators | Channels with completed livestreams | ~25K | PROPOSED | TBD |
| 11 | Shorts-First Creators | Channels primarily producing Shorts content | ~50K | PROPOSED | TBD |
| 12 | Creative Commons Educators | Channels publishing under CC license | ~10-15K | PROPOSED | TBD |

---

## 2. New Creator Cohort (5 Core Streams)

### 2.1 Intent Creators (Stream A)

**What it captures:** New YouTube channels created on or after January 1, 2026 that signal entrepreneurial intent through their early videos ("Welcome to my channel," "My first video," etc.).

**Why this stream exists:** This is the treatment group. These creators deliberately announce themselves as starting a channel. They represent the population of interest for studying early-stage creator strategy: people who treat YouTube as a project, not an accident.

**Sampling method:**
- `search.list(q=INTENT_KEYWORDS, type='video', order='date')` across 8 languages
- Extract channel IDs from search results
- Keep only channels with `published_at >= 2026-01-01`
- 46 intent keywords across English, Hindi, Spanish, Japanese, German, Portuguese, Korean, French

**Key design parameters:**
- Languages ordered by yield rate: Hindi (35.3%), English (30.9%), Spanish (29.3%), Japanese (24.5%), German (24.0%), Portuguese (23.1%), Korean (22.5%), French (18.3%)
- `order=date` (not relevance) to minimize popularity bias
- No region filter on search (global), but `regionCode=US` available and validated as non-biasing

**Empirical validation:**
- EXP-002/010: 12.7% yield rate for intent keywords (vs. 1.9% for non-intent). 6.6x more efficient.
- EXP-006: English alone captures only 14% of findable new creators. Multilingual expands by 7.1x.

**What it collected:** 83,825 channels across 46 keywords x 8 languages. Ran to full exhaustion of the search space (below 200K target because that was the actual yield ceiling of the API).

**Script:** `src/collection/discover_intent.py`
**Quota cost:** ~404,000 units (initial); ~4,000 units (weekly sweep)

---

### 2.2 Non-Intent Creators (Stream A')

**What it captures:** New channels (created 2026+) whose first videos are content (gameplay, tutorials, recipes, reviews) rather than channel introductions. Same entry cohort as Stream A, different launch strategy.

**Why this stream exists:** Causal inference comparison for the effect of intentional launching. If Stream A creators are people who "announce" their channel, Stream A' creators are people who "just start making things." Comparing their trajectories isolates whether the intent signal (and the strategic behavior it proxies) predicts different outcomes.

**Sampling method:**
- `search.list(q=CONTENT_KEYWORDS, type='video', order='date')` across 8 languages
- Same date filter (channel created >= 2026-01-01)
- 48 content keywords: "gameplay," "let's play," "tutorial," "recipe," "review," "unboxing," "haul," etc., translated across all 8 languages

**Key design parameters:**
- Same language set and date filter as Stream A for comparability
- Content keywords chosen to be orthogonal to intent signals (no overlap with "welcome"/"intro" language)
- Lower yield rate (1.9%) means more API calls per channel found

**Empirical validation:**
- EXP-002/010: 1.92% yield rate. Viable but 6.6x less efficient than intent keywords.

**What it collected:** Not yet run. Approved for collection.

**Contemporaneity concern:** Stream A was collected in mid-February 2026. Stream A' should be collected soon to draw from the same temporal window. The longer the gap, the less comparable the two cohorts are (seasonality, trending topics, platform changes).

**Script:** `src/collection/discover_non_intent.py`
**Quota cost:** ~404,000 units (initial); ~4,000 units (weekly sweep)

---

### 2.3 Algorithm Favorites (Stream B)

**What it captures:** Channels that YouTube's search algorithm surfaces when given maximally generic queries (vowels: a, e, i, o, u, "video"). These are the channels the platform actively promotes.

**Why this stream exists:** Benchmark for what new creators compete against for visibility. If you search YouTube using the broadest possible queries, you get the top 0.01% of the platform. This stream quantifies the competitive landscape — the ceiling of success that new entrants see when they arrive.

**Sampling method:**
- `search.list(q=VOWELS, type='video', order='relevance')`
- Keywords: `a`, `e`, `i`, `o`, `u`, `video`
- No date filter (captures established channels)

**Key design parameters:**
- `order=relevance` (not date) — this intentionally maximizes algorithm bias. The bias IS the signal.
- Expanded from 2K target to 25K via additional keyword searches (approved Feb 17)
- Expansion will use keyword searches (not category stratification) to build a standalone "who wins on YouTube" dataset

**Empirical validation:**
- EXP-001/003: Median views = 1,161,938. 94.4% are "big channels" (>1K subs). This is catastrophic popularity bias.
- This finding is why the stream was relabeled from "Market Baseline" to "Algorithm Favorites" — it does not represent the market, it represents what the algorithm promotes.

**What it collected:** 1,539 channels. 742 have >1M subscribers, 483 at 100K-1M. Far below the expanded 25K target.

**Script:** `src/collection/discover_benchmark.py`
**Quota cost:** ~12,000 units (initial at 2K); expansion TBD

---

### 2.4 Searchable Random (Stream C)

**What it captures:** Channels discovered through random 3-character alphanumeric prefix searches. This is the closest approximation to a random sample of YouTube's searchable content.

**Why this stream exists:** Population baseline for survivorship analysis. Streams A and A' capture people who are trying. Stream B captures winners. Stream C captures what a randomly selected piece of YouTube actually looks like — including the vast "dark matter" of low-view, low-subscriber content that never appears in any curated or algorithmic list. Without this baseline, any statement about "new creators perform X" has no denominator.

**Sampling method:**
- Random Prefix Sampling (cf. Zhou et al., 2011)
- Generate random 3-character alphanumeric strings (e.g., `x7z`, `1a2`, `k9m`)
- `search.list(q=RANDOM_PREFIX, type='video')` with no date filter
- Unfiltered collection — captures channels of all ages and sizes

**Key design parameters:**
- Does NOT filter by channel creation date (captures the full YouTube population, not just new channels)
- Random prefixes avoid keyword bias entirely
- Lowest big-channel percentage of any strategy tested

**Empirical validation:**
- EXP-001/003: Median views = 305 (5,400x lower than vowel search). 39.3% big channels (vs. 94.4% for Algorithm Favorites). This is the least biased sampling strategy tested.

**What it collected:** Not yet run. Approved for collection.

**Script:** `src/collection/discover_random.py`
**Quota cost:** ~300,000 units (initial); ~1,000 units (monthly sweep)

---

### 2.5 Casual Uploaders (Stream D)

**What it captures:** Channels whose videos have raw or default filenames (IMG_0001.MOV, Screen Recording, Untitled, etc.). These are people who uploaded content without even renaming the file.

**Why this stream exists:** Behavioral contrast to intentional creators. Stream A creators write "Welcome to my channel." Stream D creators upload "IMG_4582.MOV." The difference in launch strategy could not be starker. Comparing their trajectories tests whether intentionality and professionalism at entry predict long-term outcomes — or whether content quality and audience fit matter more than first impressions.

**Sampling method:**
- `search.list(q=RAW_FILE_PATTERNS, type='video', order='date')`
- 15 filename patterns: `IMG_`, `MVI_`, `DSC_`, `MOV_`, `VID_`, `DSCF`, `GOPR`, `DJI_`, `P_`, `Screen Recording`, `Untitled`, `New Recording`, `20260`, `video_2026`, `Video 2026`

**Key design parameters:**
- `order=date` to capture recent uploads
- Expansion approved: add ~20 more filename patterns (e.g., phone-specific patterns, screen recorder defaults) to target 3-5K channels
- Multi-signal filtering post-hoc: use filename + channel metadata to identify truly casual uploaders vs. creators who occasionally upload raw files

**Empirical validation:**
- EXP-001/003: Median views = 214 (lowest of all strategies). 59% big channels (higher than Random Prefix, because even raw filenames from popular channels get indexed).

**What it collected:** 1,862 channels from 15 queries. Top patterns: Screen Recording (536), Untitled (384), IMG_ (232). The raw-filename search space is inherently limited.

**Script:** `src/collection/discover_casual.py`
**Quota cost:** ~150,000 units (initial); ~500 units (weekly sweep)

---

### New Creator Cohort: Design Logic

The five streams form a complete picture:

```
               HIGH INTENT                    LOW INTENT
            ┌──────────────┐              ┌──────────────┐
  NEW       │  Stream A:   │              │  Stream A':  │
  (2026+)   │  Intent      │              │  Non-Intent  │
            │  Creators    │              │  Creators    │
            └──────────────┘              └──────────────┘
                                                │
                    │                           │
               COMPARISON ──────────────────────┘

            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  BASELINE  │  Stream B:   │    │  Stream C:   │    │  Stream D:   │
            │  Algorithm   │    │  Searchable  │    │  Casual      │
            │  Favorites   │    │  Random      │    │  Uploaders   │
            └──────────────┘    └──────────────┘    └──────────────┘
              (ceiling)           (population)         (floor)
```

- **A vs. A'**: Effect of intentional launch strategy (same cohort, different entry behavior)
- **A vs. B**: How new creators compare to what the algorithm promotes (distance from ceiling)
- **A vs. C**: How new creators compare to the random YouTube population (representativeness)
- **A vs. D**: Effect of professionalism vs. casualness at entry (strategic vs. accidental)
- **C alone**: Unbiased population baseline for any survivorship or selection analysis

---

## 3. Gender Gap Longitudinal Panel

### 3.1 Panel Composition

**What it captures:** Daily channel-level statistics and weekly video-level statistics for 9,760 established US-based YouTube channels with human-coded gender and race data.

**Source:** Infludata commercial dataset (14,704 rows, 14,169 unique channels after dedup) enriched by Bailey (research assistant) with perceivedGender, race, and runBy coding.

**Why this panel exists:** The gender gap paper (dissertation CH2) established the existence of a subscriber gap between male and female YouTube creators. This longitudinal panel provides the time-series data needed to test causal mechanisms: Does the gap widen or narrow over time? Does AI adoption differentially affect male vs. female creators? Do audience engagement patterns differ by gender in ways that accumulate into the subscriber gap?

### 3.2 Panel Filtering Decision

**Decision:** Restrict to channels with BOTH gender AND race coded (9,760 of 14,169). Drops 31% of channels.

**Justification:**
- The 4,100+ uncoded channels are not missing at random. Analysis of the `runBy` field shows they are: organizations (51%), teams (13%), broken/inactive (13%), AI bots (9%), uncoded individuals (14%).
- Zero overlap with the target population (individual human entrepreneurs)
- Gender and race are the key independent variables — channels missing both contribute nothing to any regression
- Intersectional analysis (gender x race) is a core design goal, which requires both variables
- Saves 35% on quota and storage
- Uncoded channels can be added back if coding is later completed

**Gender distribution:** man=6,590 (67.5%), woman=3,465 (35.5%), non-binary=37 (0.4%)
**Race distribution:** white=7,113 (72.9%), Black=1,718 (17.6%), Asian=814 (8.3%), Hispanic=124 (1.3%)

### 3.3 Collection Design

**Daily channel stats (running):**
- `channels.list(part=statistics)` for all 9,760 channels
- Captures: subscriber count, total views, video count
- Cost: ~195 units/day, ~1.1 MB/day
- Running on Mac Mini via launchd (8:00 UTC)

**Weekly video stats (running):**
- Full video inventory enumeration (one-time, in progress: 5M+ rows)
- `videos.list(part=statistics)` for all enumerated videos
- Captures: per-video views, likes, comments
- Cost: ~240K units/week, ~756 MB/week

**Dual-cadence rationale:** Channel metrics are primary outcome variables and change meaningfully day-to-day. Video metrics change slowly for most videos — weekly snapshots capture sufficient variation for the staggered DiD design at 7x lower cost than daily.

**Script:** `src/panels/daily_stats.py --panel-name gender_gap`

---

## 4. AI Research Infrastructure (4 Designs)

### 4.1 AI Creator Census (Design 1)

**Research question:** Who are the people making content about AI? What patterns emerge in their coverage, audience, and gender dynamics?

**Identification strategy:** Descriptive census + cross-sectional regression + longitudinal panel
- DV: Engagement metrics (views, likes, comments)
- Key IV: Creator gender
- Controls: Subscriber count, upload frequency, content category, channel age
- Can exploit within-creator variation (AI vs. non-AI videos from the same creator) via fixed effects

**Why this design:**
- We don't know the basic demographics of the AI creator space yet
- Descriptive work is publishable and foundational (cf. Pew's YouTube studies)
- The gender gap framework from CH2 extends directly to this population
- Within-creator variation provides natural controls for unobserved channel quality

**What was collected:** 50,010 unique channels via keyword search across 45 AI-related terms, 2 sort orders (relevance + date), 18-month lookback window. Top terms: artificial intelligence (2,859), AI tools (2,815), prompt engineering (2,786).

**Sampling method:**
- `search.list(q=AI_SEARCH_TERMS, type='video')` across 45 terms
- Sort by relevance and by date (two passes per term)
- 18-month lookback window (captures pre-ChatGPT through current)
- Terms span: general AI, video/image generation, audio/music AI, coding AI, non-English terms, domain-specific tools

**Current tracking:** Daily channel stats on Mac Mini (9:00 UTC). Video enumeration in progress (8.3% complete as of Feb 17).

**Known limitation:** "Found via AI keyword search" is NOT the same as "produces AI content." ~70% of census channels are general creators who made AI-adjacent videos; ~30% have AI keywords in their channel title/description (dedicated AI creators). Validation needed: "talking about AI" vs. "producing with AI" distinction requires transcript analysis and/or the AI keyword flagger.

**Script:** `src/collection/discover_ai_creators.py`

---

### 4.2 AI Adoption Diffusion Panel (Design 2)

**Research question:** Among established creators, who adopts AI tools, when, and what happens to their engagement metrics before and after adoption?

**Identification strategy:** Longitudinal panel + staggered difference-in-differences (Callaway & Sant'Anna 2021; Sun & Abraham 2021)
- AI adoption is rolling out heterogeneously across creators = natural staggered treatment
- Prospective data collection captures the pre-adoption baseline before creators adopt
- This is the design that requires starting collection NOW — pre-adoption baselines cannot be recovered retroactively

**Population:** Gender gap panel (9,760 channels). These are established creators with coded demographics whose pre-AI video history provides the baseline.

**Treatment variable:** AI adoption, detected through three layers:
1. **Keyword matching** on video titles/descriptions (101 keywords across 6 categories in `AI_FLAG_KEYWORDS`)
2. **Transcript analysis** for AI tool references within the video itself
3. **Production quality discontinuities** — sudden changes in upload frequency, video length distribution, or thumbnail style (requires longitudinal baseline)

**Key methodological challenge:** Distinguishing "talking about AI" from "producing with AI." A creator who reviews ChatGPT is different from a creator who uses ChatGPT to write their scripts. Layer 1 catches both; layers 2-3 are needed to separate them.

**Complementary analysis on new cohort:** Stream A (intent) vs. A' (non-intent) provides a natural experiment for AI adoption among new creators. Same entry cohort, different launch strategies. Stream D (casual) provides a non-strategic baseline. This tracks "born AI-native" adoption, complementing the established-creator adoption story.

**Script:** `src/collection/flag_ai_videos.py` (offline AI keyword flagger, built)
**Status:** Infrastructure built. Awaiting video inventory completion and Katie's decision on AI flagger scope.

---

### 4.3 AI Adoption Among New Creators (Design 3)

**Research question:** Do new strategic creators adopt AI more than non-strategic ones? Is AI adoption front-loaded in intentional launchers?

**Identification strategy:** Cross-stream comparison within the new creator cohort
- Stream A (intent) vs. A' (non-intent) vs. D (casual)
- Same temporal cohort, different launch strategies
- Tracks "born AI-native" adoption patterns

**Why this design:**
- Complements Design 2 (established creators pivoting to AI) with Design 3 (new creators who may be AI-native from day one)
- Stream A vs. A' is a natural experiment: same entry window, different launch behavior
- No new infrastructure required — the AI keyword flagger works on any channel's videos

**Status:** Depends on collection of Streams A' and D (expansion). Infrastructure ready.

---

### 4.4 Audience Response to AI Content (Design 4)

**Research question:** Does audience engagement differ for AI-produced content vs. non-AI content, and does the penalty/premium differ by creator gender?

**Identification strategy:** Within-creator matching + difference-in-differences
- Compare AI vs. non-AI videos from the SAME channel (each creator is their own control)
- DV: viewership trajectory (views over time), like-to-view ratio, comment volume/sentiment
- Key moderator: creator gender
- Controls for all channel-level confounders via creator fixed effects

**Why within-creator comparison:**
- Cross-channel matching (AI channel vs. non-AI channel) is confounded by unobserved channel quality
- Within-creator variation controls for everything about the creator (audience, niche, quality, charisma)
- Requires channels that produce both AI and non-AI content — the AI census naturally captures these

**Population:** AI census channels (50,010) who produce both AI-flagged and non-AI-flagged videos.

**Data requirements:**
- All video metadata from Design 1
- AI classification per video from Design 2's keyword flagger
- Daily viewcount trajectories for matched pairs for 30-60 days post-upload
- Comment text + sentiment for focal videos (deferred)

**Status:** Design ready. Depends on video inventory completion + AI flagging.

---

## 5. Proposed Future Streams (5 Expansion Streams)

These were approved in principle on Feb 17, 2026 but have no scripts, no collection, and no formal specifications yet.

### 5.1 Topic-Stratified Discovery

**What it would capture:** New channels sampled proportionally across YouTube's 26 topic categories using the `topicId` search parameter.

**Why:** Current streams discover channels through keyword searches, which are biased toward certain content types (intent keywords skew toward vloggers; content keywords skew toward gaming/cooking). Topic stratification ensures representation across categories that keyword searches may miss (e.g., automotive, pets, sports).

**Target:** ~30-40K channels
**Method:** `search.list(topicId=X, type='video', order='date')` across 26 topic categories
**Status:** PROPOSED

---

### 5.2 Trending Tracker

**What it would capture:** Channels that appear on YouTube's trending charts, tracked daily across 51 region codes.

**Why:** Trending represents a different selection mechanism than search. It captures what's culturally salient in the moment — viral content, news events, entertainment. Cross-referencing trending channels against other streams reveals which new creators break through to cultural visibility.

**Target:** Accumulating daily (no fixed target — this is a running log)
**Method:** `videos.list(chart=mostPopular)` across 51 region codes
**Status:** PROPOSED

---

### 5.3 Livestream Creators

**What it would capture:** Channels that have completed livestreams, captured via the `eventType=completed` search parameter.

**Why:** Livestreaming is a distinct creator modality with different engagement dynamics (real-time interaction, longer sessions, different monetization). Livestream-first creators may have different growth trajectories than video-first creators.

**Target:** ~25K channels
**Method:** `search.list(eventType=completed, type='video', order='date')`
**Status:** PROPOSED

---

### 5.4 Shorts-First Creators

**What it would capture:** Channels whose primary output is YouTube Shorts (videos ≤180 seconds).

**Why:** Shorts represent YouTube's fastest-growing content format and its direct competition with TikTok. Shorts-first creators may have fundamentally different growth dynamics, audience demographics, and monetization patterns than long-form creators.

**Target:** ~50K channels
**Method:** `search.list(videoDuration=short, type='video', order='date')`
**Status:** PROPOSED

---

### 5.5 Creative Commons Educators

**What it would capture:** Channels publishing under Creative Commons licenses, which tend to be educational and open-access.

**Why:** CC-licensed content represents a philosophically different approach to content creation — sharing vs. monetizing. This stream captures the educational/altruistic corner of YouTube that may have different relationships with AI tools (using AI for teaching vs. for production value).

**Target:** ~10-15K channels
**Method:** `search.list(videoLicense=creativeCommon, type='video', order='date')`
**Status:** PROPOSED

---

## 6. Experimental Validation Evidence

All core sampling strategies were empirically tested before production use. Full details in [docs/SAMPLING_EXPERIMENTS.md](SAMPLING_EXPERIMENTS.md).

### 6.1 Bias Profile Comparison (EXP-001/003)

| Strategy | N | Median Views | Zero-View % | Median Subs | Big Channel % |
|----------|---|-------------|-------------|-------------|---------------|
| Vowels (Stream B) | 125 | **1,161,938** | 0.0 | 199,000 | **94.4** |
| Raw Filenames (Stream D) | 105 | 214 | 2.9 | 1,810 | 59.0 |
| Random Prefix (Stream C) | 150 | 305 | 2.0 | 533 | **39.3** |
| Common Words | 125 | 137,193 | 0.0 | 39,500 | 81.6 |

**Key insight:** Each strategy captures a radically different slice of YouTube. The bias is not a bug — it's the research design. Stream B captures the ceiling, Stream C captures the population, Stream D captures the floor.

### 6.2 Intent Keyword Yield (EXP-002/010)

| Keyword Type | Channels Checked | New Channels | Yield Rate |
|--------------|-----------------|--------------|------------|
| Intent (Stream A) | 307 | 39 | **12.7%** |
| Non-Intent (Stream A') | 312 | 6 | 1.92% |

Intent keywords are 6.6x more efficient at finding new creators.

### 6.3 Language Bias (EXP-006)

| Language | Channels Checked | New Channels | Yield % |
|----------|-----------------|--------------|---------|
| Hindi | 136 | 48 | **35.3%** |
| English | 123 | 38 | 30.9% |
| Spanish | 147 | 43 | 29.3% |
| Japanese | 106 | 26 | 24.5% |
| German | 146 | 35 | 24.0% |
| Portuguese | 143 | 33 | 23.1% |
| Korean | 120 | 27 | 22.5% |
| French | 115 | 21 | 18.3% |

English alone captures only 14% of findable new creators. Multilingual sampling expands the accessible population by 7.1x.

### 6.4 Other Validated Findings

| Finding | Evidence | Design Implication |
|---------|----------|--------------------|
| Region codes don't introduce systematic bias | Median views 36-62 across US/GB/IN/BR/DE | Safe to use `regionCode=US` for consistency |
| Pagination doesn't reduce popularity bias | Page 2 has higher views than Page 1 | Use query diversification, not pagination depth |
| Channel ID enumeration is not viable | 0/100 random IDs exist | YouTube ID space is too sparse for brute-force |

---

## 7. Quota Budget Summary

**Available daily quota:** ~1,010,000 units (YouTube Researcher Program tier)

### 7.1 Initial Collection Costs

| Stream | Target | Units | Notes |
|--------|--------|-------|-------|
| Intent Creators (A) | 200K | ~404,000 | DONE (83,825 collected) |
| Non-Intent Creators (A') | 200K | ~404,000 | 1 day |
| Algorithm Favorites (B) | 25K | TBD | Expansion from 1,539 |
| Searchable Random (C) | 50K | ~300,000 | 1 day |
| Casual Uploaders (D) | 3-5K | ~150,000 | Expansion from 1,862 |
| AI Creator Census | 50K | ~100,000 | DONE (50,010 collected) |

### 7.2 Steady-State Costs (Running)

| Activity | Frequency | Units | Storage |
|----------|-----------|-------|---------|
| Gender gap channel stats | Daily | ~195 | 1.1 MB/day |
| Gender gap video stats | Weekly | ~240,000 | 756 MB/week |
| New cohort channel stats | Daily | ~1,700 | varies |
| AI census channel stats | Daily | ~1,000 | varies |
| Weekly sweeps (all streams) | Weekly | ~8,500 | minimal |

**Total steady-state:** <5% of daily quota. Quota is NOT a binding constraint.

---

## 8. Collection Cadence and Data Schemas

### 8.1 Cadence Rationale

| Level | Cadence | Reason |
|-------|---------|--------|
| Channel stats | Daily | Primary outcome variables (subscribers, views) change meaningfully day-to-day |
| Video stats | Weekly | Per-video views change slowly; weekly captures sufficient variation at 7x lower cost |
| Video discovery (new uploads) | Weekly | Detect new videos from tracked channels |
| Comments | Deferred | Retroactive (timestamped) — can be collected any time. Not time-sensitive like views. |
| Transcripts | Deferred | Unofficial API (no quota cost). Low priority until AI adoption detection phase. |

### 8.2 Channel Stats Schema (8 fields)

`channel_id`, `view_count`, `subscriber_count`, `video_count`, `made_for_kids`, `status`, `made_for_kids_changed`, `scraped_at`

### 8.3 Video Stats Schema (24 fields)

`video_id`, `channel_id`, `title`, `description`, `published_at`, `view_count`, `like_count`, `comment_count`, `duration`, `duration_seconds`, `is_short`, `category_id`, `category_name`, `tags`, `hashtags`, `hashtag_count`, `definition`, `dimension`, `caption`, `licensed_content`, `content_rating_yt`, `region_restriction_blocked`, `region_restriction_allowed`, `scraped_at`

### 8.4 Initial Channel Collection Schema (28+ fields)

Full schema documented in [TECHNICAL_SPECS.md](../TECHNICAL_SPECS.md).

---

## 9. Key Design Decisions and Rationale

### Decision 1: Triple-Stream → Five-Stream Design (Feb 2, 2026)
**What:** Expanded from 3 streams (A, B, C) to 5 (added A', D).
**Why:** A' provides a within-cohort control group (same entry timing, different launch strategy). D provides the behavioral floor (people who aren't even trying).
**Alternative rejected:** Two-stream (intent + random) — too coarse. "Random" conflated the algorithm ceiling with the population baseline.

### Decision 2: Coded Channels Only — 9,760 of 14,169 (Feb 16, 2026)
**What:** Restricted gender gap panel to channels with both gender AND race coded.
**Why:** Uncoded channels are 51% organizations, 13% teams, 13% broken. Zero overlap with individual entrepreneurs. Gender and race are the key IVs — missing both means zero analytical value.
**Alternative rejected:** Full 14,169 (wastes 35% of quota on channels that can't enter any regression).

### Decision 3: Dual-Cadence Collection (Feb 16, 2026)
**What:** Daily channel stats, weekly video stats.
**Why:** Channel metrics are primary DVs and change meaningfully day-to-day. Video metrics change slowly. Weekly video = 7x cheaper than daily.
**Alternative rejected:** Daily video stats (1.68M units/week vs. 241K; marginal analytical gain).

### Decision 4: Four AI Research Designs (Feb 17, 2026)
**What:** Expanded from 3 to 4 designs. Added AI Adoption Among New Creators.
**Why:** Stream A vs. A' is a natural experiment for "born AI-native" adoption. No new infrastructure required.

### Decision 5: Relabel Stream B from "Market Baseline" to "Algorithm Favorites" (Feb 2, 2026)
**What:** Changed the conceptual label after EXP-003 revealed catastrophic popularity bias.
**Why:** Vowel search doesn't capture the market — it captures what the algorithm promotes. Calling it "market baseline" would be analytically misleading. "Algorithm Favorites" is honest about what the data represents.

### Decision 6: Multilingual Collection (Feb 2, 2026)
**What:** Expanded from English-only to 8 languages.
**Why:** English captures only 14% of findable new creators. Hindi has the highest yield (35.3%). English-only would produce a fundamentally non-representative sample.

### Decision 7: Expand Stream B to 25K via Keywords, Not Categories (Feb 17, 2026)
**What:** Scale Stream B from 2K to 25K using expanded keyword searches.
**Why:** Katie wants this as a standalone "who wins on YouTube" dataset. Keyword expansion captures more of the algorithm's surface area than category stratification. Category stratification risks imposing researcher priors about which categories matter.

### Decision 8: Comments Deferred (Feb 17, 2026)
**What:** No comment collection until a specific paper needs them.
**Why:** Comments are timestamped and retroactive — they can be collected any time without losing data. Views are NOT retroactive — every day without view data is lost forever. Prioritize time-sensitive collection.

---

## 10. Known Limitations and Open Questions

### Limitations

1. **Search API unreliability.** YouTube's search results are not deterministic (Rieder et al. 2025; Efstratiou 2025). Identical queries return different results at different times. All keyword-based streams (A, A', B, D, AI Census) are affected. Mitigation: multiple query terms, multiple sort orders, checkpoint/resume.

2. **Subscriber count rounding.** Above 1K subscribers, YouTube rounds to 3 significant figures. Growth rate analysis is more reliable than level comparisons for mid-size channels.

3. **No dislike data.** Dislikes have been private since December 2021. Like-to-view ratio is the best available approval signal.

4. **No native Shorts identifier.** YouTube API does not flag Shorts. Workaround: `duration <= 180 seconds` (updated from 60s after YouTube expanded Shorts to 3 minutes in October 2024).

5. **AI census inclusion precision.** ~70% of the 50,010 AI census channels are general creators who made an AI-adjacent video, not dedicated AI creators. The "talking about AI" vs. "producing with AI" distinction needs operationalization.

6. **Gender coding is human-coded and binary-dominant.** Only 37 non-binary channels in the dataset. Intersectional analysis (gender x race) has small cell sizes for some combinations (e.g., Hispanic x woman).

7. **Stream A yield ceiling.** Target was 200K; actual yield was 83,825. The intent keyword search space has a natural ceiling — not every new channel uses these phrases, and the API only surfaces discoverable content.

### Open Questions

1. **AI adoption flagger scope.** Three-layer detection (keyword → transcript → production discontinuity) is designed but the "producing with AI" layer needs operationalization. What counts as "AI-produced" for a creator who uses ChatGPT for scripts but records themselves on camera?

2. **2020 Birth Cohort (Decision 005).** Retrospective cohort spanning the full AI diffusion arc (pre-ChatGPT through 2026). Proposed but needs Katie's decision on feasibility, sample size, and gender coding method.

3. **Future stream specifications.** The 5 proposed streams (Topic-Stratified, Trending, Livestream, Shorts-First, Creative Commons) are approved in principle but have no bias profiles, yield estimates, or collection specifications. Each needs validation experiments before production.

4. **Comment depth.** When comments are eventually collected: full pull or randomized sample? AI Census gets full pull on AI-flagged videos. Other streams TBD.

5. **Gender coding for new populations.** AI census channels (50K) and new creator cohort channels (83K+) have no gender/race coding. Method TBD: name-based classifier (Genderize.io) + manual coding for ambiguous cases? Or full manual coding?

---

## Source Documents

This document consolidates content from:

| Source | What was drawn |
|--------|---------------|
| [TECHNICAL_SPECS.md](../TECHNICAL_SPECS.md) | Stream specs, data schemas, quota budgets |
| [DECISION_LOG.md](../DECISION_LOG.md) | Design decisions and rationale |
| [SAMPLING_EXPERIMENTS.md](SAMPLING_EXPERIMENTS.md) | Experimental validation results |
| [PROJECT_MASTER_PLAN.md](../PROJECT_MASTER_PLAN.md) | Research questions, key findings, roadmap |
| [YOUTUBE_DATASET_DESIGN.md](../../SECOND_BRAIN/03-research/YOUTUBE_DATASET_DESIGN.md) | AI research designs, identification strategies |
| [PROGRESS_LOG.md](../PROGRESS_LOG.md) | Production status, 12-stream architecture discussion |
| [CLAUDE.md](../CLAUDE.md) | Sampling design reference tables |
