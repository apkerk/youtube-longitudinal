# Expansion Strategy Validation Framework

**Purpose:** Pre-registered validation checkpoints for the 6 adopted API expansion strategies. Each strategy gets a cheap test (~500-1000 API units) before committing full daily quota. Defines yield, quality, overlap, and diminishing-returns metrics with concrete success/fail criteria.

**Date:** Feb 19, 2026
**Context:** 5-expert API panel adopted 6 strategies to break the YouTube Search API's ~500-result-per-query ceiling. This document specifies how to validate each one before production deployment.

---

## Validation Design Principles

1. **Test before burn.** Every strategy gets a pilot run of ~500-1000 API units before committing a full day's quota.
2. **Same keyword, different treatment.** Validation compares each strategy against the current `order=date` baseline using the same keyword + time window, so the only thing that changes is the strategy parameter.
3. **Metrics are computed per-strategy, not pooled.** Each strategy earns its own GO/NO-GO.
4. **Provenance is mandatory.** Every channel discovered in validation must be tagged with `discovery_method` (the strategy that found it) and `discovery_topic` / `discovery_region` / `discovery_duration` / `discovery_order` / `discovery_safesearch` as appropriate.
5. **Results are logged.** Validation output goes to `data/validation/expansion_pilots/` with one CSV per strategy per date.

---

## Universal Metrics (Apply to All 6 Strategies)

### M1: Yield Rate
- **Definition:** Unique new channels found per 100 API units consumed.
- **Baseline:** Current yield for A (~612 channels/keyword) and A' (~251 channels/keyword) from existing runs.
- **Computation:** `(unique_new_channels / api_units_consumed) * 100`
- **Success criterion:** Strategy yield rate > 50% of baseline yield rate. If a strategy costs 2x the API units but finds <1x the unique channels, it's not worth it.

### M2: Quality Check (2026+ Creators, Not Bots)
- **Definition:** Proportion of newly discovered channels that pass the existing quality filters:
  - `published_at >= 2026-01-01` (for Streams A/A' only)
  - `video_count >= 1` (not empty channels)
  - Not flagged by bot heuristic: 0 or 1 videos AND 0 subscribers AND default profile picture
- **Computation:** `passing_channels / total_new_channels`
- **Success criterion:** Quality rate >= 90%. If a strategy finds mostly dead/bot/pre-2026 channels, it's adding noise.

### M3: Overlap with Baseline
- **Definition:** Proportion of channels found by the strategy that were ALREADY found by the baseline `order=date` search on the same keyword + window.
- **Computation:** `|strategy_channels ∩ baseline_channels| / |strategy_channels|`
- **What it tells us:** High overlap (>80%) means the strategy is redundant with the baseline. Low overlap (<20%) means it's accessing genuinely different result sets.
- **Ideal range:** 10-50% overlap. Some overlap confirms we're in the right population; too much means wasted quota.

### M4: Marginal New Channel Rate
- **Definition:** Proportion of channels found by the strategy that are NEW (not in any existing stream CSV).
- **Computation:** `|strategy_channels - all_existing_channels| / |strategy_channels|`
- **Success criterion:** Marginal new rate >= 40%. Below this, the strategy is mostly re-finding known channels.

### M5: Diminishing Returns Test
- **Definition:** For strategies with multiple partitions (topicId, regionCode, videoDuration), measure yield per partition ordered from highest to lowest. Plot cumulative unique channels vs. partitions used.
- **Test:** If the last 25% of partitions contribute <5% of cumulative unique channels, those partitions should be dropped.
- **Implementation:** Sort partitions by descending yield. Mark the "elbow" where marginal yield drops below `mean_yield / 3`.

---

## Strategy 1: `topicId` Partitioning

**What it does:** Adds `topicId=X` to each search query, creating per-topic result slots. Each topic gets its own ~500-result ceiling, multiplying the discoverable population.

**Validation experiment:**
- **Keywords to test:** Pick 3 high-volume keywords: 1 intent ("My first video"), 1 non-intent ("gameplay"), 1 bilingual ("Mi primer video")
- **Time window:** Single 24h window (yesterday)
- **Topics to test:** All 12 proposed topics from `DISCOVERY_TOPIC_IDS`
- **Protocol:**
  1. Run each keyword with NO topicId (baseline): ~3 searches x 10 pages = ~3,000 units
  2. Run each keyword WITH each of 12 topicIds: ~3 x 12 x 5 pages = ~1,800 units (reduced pages for pilot)
  3. Total pilot cost: ~4,800 units (<0.5% daily quota)
- **Metrics to compute:**
  - M1 (yield per unit) for each topic
  - M3 (overlap): How many topic-discovered channels were already in the no-topic baseline?
  - M5 (diminishing returns): Rank topics by unique new channels found. Which topics are empty?
  - **Topic bias check:** For channels found via topicId, does their actual `topic_categories_raw` match the search topicId? If <50% match, the topicId parameter is filtering unpredictably.
- **Success criteria:**
  - At least 6 of 12 topics produce unique new channels not in baseline
  - Total unique channels across all topics >= 1.5x baseline unique channels
  - Topic bias match rate >= 40% (the topicId is actually returning on-topic content)
- **GO condition:** >= 1.5x total yield, >= 6 productive topics
- **NO-GO condition:** <1.2x total yield OR <4 productive topics OR topic bias match <30%

**Provenance tags:** `discovery_topic_id`, `discovery_topic_name`

---

## Strategy 2: `order=relevance` Second Pass

**What it does:** After the standard `order=date` pass, re-runs the same query with `order=relevance` to find channels the date-ordered results missed.

**Validation experiment:**
- **Keywords to test:** 3 keywords known to hit the 500-result cap in at least one time window (check existing logs for capped queries)
- **Time window:** 3 windows (one recent, one mid-range, one early January)
- **Protocol:**
  1. Run each keyword x window with `order=date` (baseline): ~9 searches x 10 pages = ~9,000 units
  2. Run same keyword x window with `order=relevance`: ~9 searches x 5 pages = ~4,500 units
  3. Total pilot cost: ~13,500 units (~1.3% daily quota)
- **Metrics to compute:**
  - M3 (overlap): What % of relevance-found channels are already in date-ordered results?
  - M1 (yield): unique NEW channels from relevance pass / API units consumed
  - **Popularity bias check:** Compare median `subscriber_count` and `view_count` of relevance-pass channels vs. date-pass channels. If relevance-pass median subs > 5x date-pass, it's systematically oversampling popular channels.
  - **2026 filter survival rate:** What % of relevance-found channels pass the `published_at >= 2026-01-01` filter? Relevance ordering may surface older, established channels.
- **Success criteria:**
  - Overlap < 60% (relevance pass is finding different channels)
  - Popularity bias: relevance-pass median subs < 10x date-pass median subs
  - 2026 survival rate >= 50% (at least half are new creators)
  - Unique new channel yield >= 10% of date-pass yield (net additive value)
- **GO condition:** Overlap < 60% AND popularity bias < 10x AND survival >= 50%
- **NO-GO condition:** Overlap > 80% OR popularity bias > 20x OR survival < 30%
- **CONDITIONAL GO:** If popularity bias is 10-20x, adopt but MUST include `discovery_order` as a control variable in all regressions. Channels found via relevance ordering are analytically distinguishable from date-ordered channels.

**Provenance tags:** `discovery_order` (values: "date", "relevance")

---

## Strategy 3: `regionCode` Matched to Language

**What it does:** For non-English keywords, adds `regionCode=XX` to bias results toward the target country (e.g., `regionCode=MX` for Spanish keywords). Accesses region-specific index servers.

**Validation experiment:**
- **Languages to test:** Spanish (MX, ES, AR), Portuguese (BR, PT), Hindi (IN), Arabic (SA, EG) = 4 languages, 9 regions
- **Keywords:** 1 intent keyword per language (e.g., "Bienvenidos a mi canal", "Meu primeiro video", "Mera pehla video", "awwal video")
- **Time window:** Single 24h window
- **Protocol:**
  1. Run each keyword with NO regionCode (baseline): ~4 x 10 pages = ~4,000 units
  2. Run each keyword WITH each mapped regionCode: ~9 x 5 pages = ~4,500 units
  3. Total pilot cost: ~8,500 units (<1% daily quota)
- **Metrics to compute:**
  - M3 (overlap with baseline): per region
  - M1 (yield per unit): per region
  - M5 (diminishing returns): Rank regions by unique yield. Do secondary regions (AR, PT, EG) add meaningfully?
  - **Country match check:** For channels found via regionCode=MX, what % have `country=MX` in their channel metadata? If <20%, the regionCode isn't meaningfully localizing results.
  - **Cross-region overlap:** How much do MX, ES, AR overlap with each other? If >70% overlap among Spanish regions, only the top-yielding region is worth running.
- **Success criteria:**
  - At least 1 region per language adds >= 15% unique channels over baseline
  - Cross-region overlap < 50% (different regions find different channels)
  - Country match rate provides useful signal (any value is informative, no hard threshold)
- **GO condition:** >= 15% net new per region for primary regions (MX, BR, IN, SA)
- **NO-GO condition:** <5% net new for primary regions OR >70% cross-region overlap

**Provenance tags:** `discovery_region_code`

---

## Strategy 4: `safeSearch=none`

**What it does:** Overrides the API default of `safeSearch=moderate` to include content YouTube classifies as potentially adult. The default silently excludes beauty/fitness/gaming/comedy creators whose content triggers the moderate filter.

**Validation experiment:**
- **Keywords to test:** 4 keywords likely affected by safeSearch: "GRWM" (beauty), "workout" (fitness), "gameplay" (gaming), "comedy" (humor). Plus 2 control keywords unlikely to be affected: "tutorial", "My first video"
- **Time window:** Single 24h window
- **Protocol:**
  1. Run each keyword with `safeSearch=moderate` (current default): ~6 x 10 pages = ~6,000 units
  2. Run each keyword with `safeSearch=none`: ~6 x 10 pages = ~6,000 units
  3. Total pilot cost: ~12,000 units (~1.2% daily quota)
  4. NOTE: `safeSearch=none` costs 0 additional quota over `moderate` for the same queries. The 12K is the cost of running BOTH for comparison.
- **Metrics to compute:**
  - M3 (overlap): How many `safeSearch=none` channels are already in `safeSearch=moderate` results?
  - Net new channels: `|none_channels - moderate_channels|`
  - **Content safety check:** Manually inspect 20 randomly sampled channels from the `safeSearch=none` ONLY set (not in moderate). Are they genuinely content creators excluded by overzealous filtering, or are they spam/adult/low-quality?
  - **Category distribution:** Compare category breakdown of none-only channels vs. moderate channels. Hypothesis: none-only channels cluster in beauty, fitness, gaming, comedy.
- **Success criteria:**
  - Net new channels >= 3% of moderate total (even small gains are free here since no extra quota)
  - Manual inspection: >= 80% of none-only channels are legitimate creators (not spam/adult)
  - No category is >50% of none-only set (not systematically pulling one type)
- **GO condition:** Net new >= 3% AND manual inspection >= 80% legitimate
- **NO-GO condition:** Manual inspection < 50% legitimate (the filter exists for a reason)
- **Note:** Even a small gain is worth taking since `safeSearch=none` costs nothing extra. The bar is low — just verify it's not introducing garbage.

**Provenance tags:** `discovery_safesearch` (values: "moderate", "none")

---

## Strategy 5: `videoDuration` Partitioning

**What it does:** Runs each query three times with `videoDuration=short`, `videoDuration=medium`, `videoDuration=long`. Each duration slice gets its own ~500-result ceiling, tripling the discoverable population.

**Validation experiment:**
- **Keywords to test:** 3 keywords: "gameplay" (likely has all 3 durations), "tutorial" (likely medium/long heavy), "My first video" (likely medium heavy)
- **Time window:** Single 24h window
- **Protocol:**
  1. Run each keyword with NO videoDuration (baseline): ~3 x 10 pages = ~3,000 units
  2. Run each keyword with short/medium/long: ~3 x 3 x 5 pages = ~4,500 units
  3. Total pilot cost: ~7,500 units (<1% daily quota)
- **Metrics to compute:**
  - M1 (yield per unit) per duration slice
  - M3 (overlap with baseline) per duration slice
  - M5 (diminishing returns): Which duration slices are productive? Hypothesis: A' benefits most from `short` (Shorts) and `long` (streams/longform), which are underrepresented in the unfiltered baseline.
  - **Duration accuracy check:** For channels found via `videoDuration=short`, sample 20 channels and check their actual video durations. Does the API accurately filter?
  - **Cross-duration overlap:** Do different duration slices find different channels? Low overlap = high value.
- **Success criteria:**
  - At least 2 of 3 duration slices produce unique channels not in baseline
  - Total unique across all slices >= 1.5x baseline
  - Cross-duration overlap < 30% (the slices are genuinely disjoint)
- **GO condition:** >= 1.5x yield AND >= 2 productive slices AND cross-duration overlap < 40%
- **NO-GO condition:** <1.2x yield OR only 1 productive slice

**Provenance tags:** `discovery_duration` (values: "any", "short", "medium", "long")

---

## Strategy 6: Shorter Time Windows for A' (12h)

**What it does:** For keywords that hit the ~500-result cap with 24h windows, halves the window to 12h. This doubles the number of windows, each with its own 500-result ceiling.

**Validation experiment:**
- **Keywords to test:** 3 A' keywords known or expected to cap: "gameplay", "tutorial", "recipe"
- **Time windows:** 4 consecutive 24h windows AND the same 4 days split into 8 x 12h windows
- **Protocol:**
  1. Run each keyword across 4 x 24h windows: ~3 x 4 x 10 pages = ~12,000 units
  2. Run each keyword across 8 x 12h windows: ~3 x 8 x 5 pages = ~12,000 units (fewer pages per window since smaller windows have fewer results)
  3. Total pilot cost: ~24,000 units (~2.4% daily quota)
  4. NOTE: This is the most expensive pilot because it requires running the full time-window comparison. Worth the cost because 12h windows are the highest-impact change for A'.
- **Metrics to compute:**
  - M1 (yield per unit) for 24h vs. 12h
  - **Cap detection:** For each keyword x window, did the 24h search hit the ~500-result cap? (Check if results returned == max_pages * 50)
  - **Net new from 12h:** Unique channels found in 12h windows NOT found in corresponding 24h windows
  - **Quota efficiency:** Units consumed per unique new channel for 12h vs. 24h
  - M5 (diminishing returns): Is 12h better than 6h? (Don't test 6h in this pilot, but flag for future if 12h shows >80% improvement)
- **Success criteria:**
  - For capped keywords: 12h windows find >= 30% more unique channels than 24h
  - For uncapped keywords: minimal difference (confirming that window splitting only helps when hitting the cap)
  - Quota efficiency: unique channels per unit is not WORSE for 12h than 24h (same or better)
- **GO condition:** >= 30% more unique channels for capped keywords
- **NO-GO condition:** <10% improvement for capped keywords (the cap hypothesis is wrong)
- **Scope limitation:** Only apply 12h windows to keywords that actually hit the cap. No benefit for uncapped keywords, and it doubles API cost.

**Provenance tags:** `discovery_window_hours` (values: 24, 12)

---

## Pilot Execution Plan

### Total Pilot Budget
| Strategy | Estimated Units | % of Daily Quota |
|----------|----------------|-----------------|
| 1. topicId partitioning | ~4,800 | 0.5% |
| 2. order=relevance | ~13,500 | 1.3% |
| 3. regionCode | ~8,500 | 0.8% |
| 4. safeSearch=none | ~12,000 | 1.2% |
| 5. videoDuration | ~7,500 | 0.7% |
| 6. 12h windows | ~24,000 | 2.4% |
| **Total** | **~70,300** | **~7.0%** |

All 6 pilots fit within a single day's quota with 93% headroom for daily stats and other work. Can run all 6 sequentially in one session.

### Execution Order (Recommended)
1. **safeSearch=none** (cheapest per-insight, zero quota risk since it replaces existing calls)
2. **topicId partitioning** (highest projected impact, second cheapest)
3. **videoDuration partitioning** (similar logic to topicId)
4. **regionCode** (moderate cost, moderate impact)
5. **order=relevance** (moderate cost, needs capped-query detection first)
6. **12h windows** (most expensive, but also highest-confidence expected return for A')

### Implementation: Pilot Script Specification

A single validation script (`src/validation/validate_expansion.py`) should:

1. Accept `--strategy {topicid,relevance,regioncode,safesearch,duration,windows}` flag
2. Accept `--keywords` to override default test keywords
3. Accept `--dry-run` to calculate API cost without executing
4. Run the baseline (no-strategy) and strategy variants for the specified keywords + windows
5. Compute all 5 universal metrics (M1-M5) plus strategy-specific checks
6. Write results to `data/validation/expansion_pilots/{strategy}_{date}.csv`
7. Print a summary table with GO/NO-GO recommendation
8. Log everything to `data/logs/expansion_pilot_{strategy}_{date}.log`

---

## Post-Validation: Production Deployment Gates

### Gate 1: Per-Strategy GO/NO-GO
Each strategy must pass its specific criteria (defined above). Strategies that fail are excluded from production.

### Gate 2: Combined Effect Test
After individual strategies pass, run a combined pilot with ALL passing strategies active simultaneously on 3 keywords x 1 day:
- **Check for interaction effects:** Do strategies interfere with each other? (e.g., does topicId + regionCode produce different results than either alone?)
- **Check for quota explosion:** Combined strategy cost should be <= sum of individual costs (no multiplicative blowup)
- **Compute net combined yield** vs. baseline

### Gate 3: Provenance Completeness
Before production, verify that every channel discovered has ALL applicable provenance tags populated. Missing tags make post-hoc analysis impossible.

### Gate 4: Schema Update
Add new provenance fields to `CHANNEL_INITIAL_FIELDS` in `config.py`:
```python
# Discovery provenance (expansion strategies)
"discovery_method",       # base, topicid, relevance, regioncode, safesearch, duration, windows
"discovery_topic_id",     # /m/04rlf etc. (only for topicId strategy)
"discovery_topic_name",   # Music, Gaming etc.
"discovery_region_code",  # MX, BR etc. (only for regionCode strategy)
"discovery_order",        # date, relevance
"discovery_safesearch",   # moderate, none
"discovery_duration",     # any, short, medium, long
"discovery_window_hours", # 24, 12
```

---

## Analytical Implications of Provenance Tags

Each strategy introduces a potential confound. The provenance tags exist so that downstream analysis can either:

1. **Control for discovery method** (include `discovery_method` as a fixed effect or control variable)
2. **Test for discovery-method effects** (regress outcomes on `discovery_method` to check if channels found by different strategies differ systematically)
3. **Restrict samples** (analyze only baseline-discovered channels for the cleanest sample; use strategy-discovered channels for robustness checks)

The expansion strategies increase sample size at the cost of sample homogeneity. The provenance tags are the insurance policy that makes this trade-off viable.

---

## Strategy-Specific Provenance Analysis Plan

After production, before any substantive analysis:

1. **Balance table:** Compare mean/median channel characteristics (subs, views, video_count, creation date, topic distribution) across discovery methods. If means differ substantially, propensity score weighting or matching may be needed.
2. **Outcome sensitivity:** Run key regressions with and without strategy-discovered channels. If point estimates shift by >15%, the strategy is introducing systematic differences that matter for inference.
3. **Wave-strategy interaction:** Check if Wave 1 keywords + new strategies find different channels than Wave 2 keywords + new strategies. If so, there's a wave x strategy confound to document.

---

## Decision Protocol

After running all 6 pilots:

| Outcome | Action |
|---------|--------|
| All 6 pass GO | Deploy all 6 with provenance tags. Combined test required. |
| 4-5 pass GO | Deploy passing strategies. Document why others were dropped. |
| 2-3 pass GO | Deploy passing strategies. Re-evaluate yield projections (60-100K targets may be unrealistic). |
| 0-1 pass GO | Strategies don't work as projected. Fall back to 15-language + relevanceLanguage only. Adjust targets downward. |

**Katie's approval required before:** Moving from pilot to production on any strategy. The pilot generates evidence; Katie makes the call.
