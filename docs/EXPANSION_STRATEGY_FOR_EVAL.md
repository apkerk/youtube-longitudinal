# YouTube API Expansion Strategy: Academic Evaluation Document

**Purpose:** This document presents 6 adopted API expansion strategies for a 5-stream new creator cohort study. It addresses whether the expanded samples will produce credible empirical research, with explicit attention to selection bias, causal inference, power, and analytical scope.

**Date:** Feb 19, 2026 (R3: final expert-panel revision)
**Project:** YouTube Longitudinal Data Collection (Cornell University, PhD dissertation research)
**Principal Investigator:** Katie Apker, Management & Organizations

---

## 1. Research Context

### 1.1 What This Project Studies

This project builds longitudinal databases of YouTube creator data to study how social forces (gender, AI adoption, strategic behavior) affect career dynamics within digital technology platforms. It supports multiple papers across management, organizational studies, and sociology journals.

### 1.2 Scope of Inference

**Target population:** Individuals who attempt to build audiences on YouTube as a form of cultural production, creating channels in 2026.

**Accessible population:** The subset of new YouTube creators whose early videos are indexed and returned by the YouTube Search API for specific keyword queries. This is a *discovery-based* sample, not a probability sample. Inclusion probabilities are unknown and unequal.

**What this sample represents:** YouTube creators discoverable via intent/content keyword searches in 15 languages. These are creators who use recognizable language in their video titles and descriptions, whose content is indexed by YouTube's search system, and whose videos appear in the first ~500 results for at least one query configuration.

**What this sample does NOT represent:** (a) Creators whose content is not indexed by YouTube Search, (b) creators who use non-standard language or purely visual/musical content without descriptive titles, (c) creators in languages not covered by the keyword set, (d) creators whose channels exist but whose videos never appear in keyword-based search results. Generalization to the full population of new YouTube creators requires the assumption that API-discoverable creators do not systematically differ from API-invisible creators on the dimensions of interest. This assumption is untestable without an external population frame.

**Stream C as calibration:** Stream C (random prefix search, 50K target, not yet collected) provides the closest available approximation to a population baseline. Once collected, it enables formal coverage calibration:

**Coverage calibration protocol:**

1. **Coverage rate statistic:** For each content category c and language l, compute:
   ```
   Coverage(c, l) = |A ∪ A' ∩ C(c,l)| / |C(c,l)|
   ```
   where C(c,l) is the subset of Stream C channels in category c and language l. This is the fraction of "random" creators who would also be discoverable via keyword search. Report the full matrix of coverage rates, plus the marginal rates across categories and languages.

2. **Coverage-weighted estimates:** Use 1/Coverage(c,l) as analytic weights in sensitivity analyses. This reweights keyword-discovered channels to approximate the category-language distribution of the random baseline. Compare unweighted and coverage-weighted point estimates for all primary analyses.

3. **Selection profile comparison:** Produce a balance table comparing A∩C (keyword-discoverable) vs. C\A (keyword-invisible) on: subscriber count, view count, video count, creation date, and channel description length. If the keyword-invisible channels are systematically smaller/newer, this documents the discovery bias explicitly.

4. **Latin-alphabet limitation:** Stream C uses random 3-character alphanumeric prefixes, which biases toward Latin-alphabet channel names. Coverage rates for non-Latin-script languages (Hindi, Japanese, Korean, Arabic) will be downward-biased in C. Report this limitation and compute coverage rates for Latin-script languages only as a sensitivity check.

5. **Minimum cell size requirement:** Coverage rate estimates require at least 50 channels per (category, language) cell. Report cells below this threshold as "insufficient data" rather than as point estimates.

### 1.3 The 5-Stream Discovery Design

Five streams capture different slices of the new YouTube creator population through different *discovery mechanisms*. Each mechanism has a known bias profile. The streams are not random samples from a common population; they are systematically different captures designed to span the creator landscape.

| Stream | Name | Current N | Target | Purpose | Discovery Mechanism |
|--------|------|----------|--------|---------|---------------------|
| A | Intent Creators | 26,327 | 60-100K | Channels that explicitly start creator journeys | YouTube Search API: intent keywords in 15 languages, `order=date`, filtered to 2026+ creation date |
| A' | Non-Intent Creators | 11,303 | 40-80K | Content-first channels (no intent signals) | YouTube Search API: content keywords in 15 languages, `order=date`, filtered to 2026+, cross-deduped against A |
| B | Algorithm Favorites | 18,208 | Complete | Algorithm-promoted benchmark | 122 generic queries, `order=relevance` (bias IS the signal) |
| C | Random Baseline | 0 (not started) | 50K | Population baseline via random prefix search | Random 3-char alphanumeric prefixes, no filters |
| D | Casual Uploaders | 3,933 | Complete | Raw-filename channels (non-strategic baseline) | Camera/phone default filenames |

### 1.4 Key Research Comparisons and Their Analytical Status

| Comparison | Analytical Status | Identifying Assumption | Threats |
|------------|-------------------|----------------------|---------|
| A vs. A' | **Observational/descriptive.** Not a natural experiment. Creators self-select into launch strategies. | Conditional independence: after controlling for content category, language, and channel age, remaining differences in trajectories are attributable to launch strategy. | Unobserved confounders (personality, strategic orientation) are plausible and cannot be ruled out. |
| A vs. B | **Descriptive benchmark.** Documents distance from algorithmic ceiling. | None needed — purely descriptive. | N/A |
| A vs. C | **Coverage calibration.** Quantifies representativeness of keyword-based discovery. | Stream C approximates the API-accessible population. | Latin-alphabet bias in C (Limitation 12). |
| Within-stream DiD | **Causal (conditional on parallel trends).** Exploits within-creator variation in AI adoption timing. | Pre-adoption trends parallel for early vs. late/never adopters. No anticipation of adoption. | Discovery method may correlate with AI adoption propensity (see Section 7.2). |
| Gender x AI interaction | **Causal (within gender gap panel).** 9,760 established channels with coded demographics. | Same staggered DiD assumptions within the gender gap panel. | Small cell sizes for some intersections (e.g., non-binary x Hispanic). |

### 1.5 The Core Problem: YouTube Search API Result Ceiling

The YouTube Search API returns a maximum of ~500 unique results per query. With 94 intent keywords x ~50 time windows x ~500 results = ~2.35M result slots, but only 26,327 unique channels (1.1% utilization for A) and 11,303 (0.55% for A'). The expansion strategies aim to multiply result slots by adding orthogonal search dimensions.

---

## 2. The 6 Adopted Expansion Strategies

### Strategy 1: `topicId` Partitioning

**Mechanism:** Add `topicId` parameter (12 Freebase topic IDs) to each search query. Each topic+keyword combination gets its own ~500-result ceiling.

**Proposed topics:** Music, Gaming, Entertainment, People & Blogs, Education, Howto & Style, Science & Technology, Sports, Comedy, News & Politics, Film & Animation, Pets & Animals.

**Projected yield improvement:** 2-4x for A', 1.3-2x for A.

**CRITICAL DISTINCTION:** This is NOT category-specific keyword expansion (which was rejected for introducing topic selection bias). The keywords remain identical. TopicId partitions the API index by topic, giving each partition its own result ceiling.

**Selection model:** topicId=X filters to channels that YouTube's classifier has tagged with topic X. This classifier is opaque, may be noisy, and is likely correlated with channel maturity (YouTube may only assign topics after sufficient content analysis). Channels in the topicId-discovered set are therefore channels that (a) match the keyword AND (b) have been classified by YouTube into a topic. This second condition is not random. Newer, smaller channels may not yet have topic assignments, creating a systematic exclusion of the youngest/smallest channels. Channels with multiple topic assignments appear in multiple strata, creating unequal inclusion probabilities (see Section 6).

**Empirical validation requirement:** Before production deployment, run the topicId pilot experiment defined in `docs/EXPANSION_VALIDATION_FRAMEWORK.md` (Strategy 1). Must validate: (a) result pool independence (Jaccard index between topic strata), (b) actual multiplier on 5-10 test queries, (c) multi-topic overlap rates, (d) topic classification accuracy (% of returned channels whose actual content matches the search topicId).

### Strategy 2: `order=relevance` Second Pass

**Mechanism:** After the primary `order=date` pass, re-run capped queries with `order=relevance` to surface channels that date-ordering buried.

**Projected yield improvement:** +15-35% on capped queries.

**Selection model:** YouTube's relevance algorithm weights watch time, engagement, click-through rate, and likely recency and channel authority. `order=relevance` therefore systematically oversamples: (a) channels with higher engagement, (b) channels with more total views, (c) possibly older/more established channels. This creates a selection on the dependent variable for any analysis where engagement or growth is an outcome.

**Analytical restriction:** Relevance-discovered channels must NEVER be pooled with date-discovered channels in causal analyses (DiD, A vs. A' comparisons) without explicit sensitivity checks. They represent a different draw from the population. The primary analytical use of relevance-discovered channels is for robustness: if results hold in both the date-only sample and the date+relevance sample, they are more credible.

### Strategy 3: `regionCode` Matched to Language

**Mechanism:** For non-English keywords, add `regionCode=XX` to query region-specific index servers (e.g., Spanish → MX, ES, AR). 23 total regions across 15 languages.

**Projected yield improvement:** +10-40% per region.

**Selection model:** regionCode shifts which index shard YouTube queries, not which creators exist. Mexican and Argentine YouTube creators are in the same global population but may be indexed differently by region-specific servers. regionCode expansion should increase coverage of within-language geographic variation without introducing a new dimension of selection bias. The concern is within-language heterogeneity: Mexican and Argentine creators may differ on dimensions relevant to the research questions (content norms, monetization access, audience demographics). This is a feature for external validity (broader geographic coverage) but requires documentation as a source of within-sample variation.

### Strategy 4: `safeSearch=none`

**Mechanism:** Override `safeSearch=moderate` default to recover beauty/fitness/gaming/comedy creators silently excluded by the filter.

**Projected yield improvement:** +5-10%. Zero additional quota cost.

**Selection model:** safeSearch=moderate excludes content YouTube classifies as adult-adjacent. This disproportionately affects beauty, fitness, and comedy creators (documented in API behavioral studies). Removing the filter recovers these creators, improving coverage. The marginal channels are not random — they are systematically from content categories that trigger content filtering. This slightly shifts the category distribution toward beauty/fitness/comedy/gaming.

### Strategy 5: `videoDuration` Partitioning

**Mechanism:** Run each query 3x with `videoDuration=short/medium/long`. Each slice gets its own result ceiling.

**Projected yield improvement:** +50-150% for A'.

**Selection model:** Duration partitioning segments the index by video format. Shorts-first creators (<4 min), standard creators (4-20 min), and longform/livestream creators (>20 min) may represent theoretically distinct subpopulations with different growth dynamics, audience demographics, and monetization paths. Multi-format creators (who upload shorts AND long videos) are discoverable through multiple duration strata, creating unequal inclusion probabilities.

### Strategy 6: Shorter Time Windows for A' (12h)

**Mechanism:** Halve windows from 24h to 12h for A' keywords that hit the ~500-result cap. Doubles windows, each with own ceiling.

**Projected yield improvement:** +30-80% for capped keywords.

**Selection model:** This is a mechanical API strategy with no selection implications. Each 12h window is a non-overlapping temporal slice of the same index. The channels discovered are from the same population, accessed at finer temporal resolution.

---

## 3. Provenance and Control Infrastructure

### 3.1 Existing Provenance Fields

| Field | Values | Purpose |
|-------|--------|---------|
| `stream_type` | stream_a, stream_a_prime, etc. | Stream membership |
| `discovery_language` | Hindi, English, Spanish, etc. | Keyword language |
| `discovery_keyword` | The keyword | Which keyword found it |
| `expansion_wave` | wave_1_original, wave_2_expansion | Keyword wave |
| `scraped_at` | ISO timestamp | Collection time |

### 3.2 Proposed Additions

| Field | Values | Purpose |
|-------|--------|---------|
| `discovery_method` | base, topicid, relevance, regioncode, safesearch, duration, windows | Expansion strategy |
| `discovery_topic_id` | /m/04rlf etc. | Topic filter (topicId only) |
| `discovery_topic_name` | Music, Gaming etc. | Human-readable topic |
| `discovery_region_code` | MX, BR, IN etc. | Region filter |
| `discovery_order` | date, relevance | Sort order |
| `discovery_safesearch` | moderate, none | SafeSearch setting |
| `discovery_duration` | any, short, medium, long | Duration filter |
| `discovery_window_hours` | 24, 12 | Window size |
| `search_query_timestamp` | ISO timestamp | When the search API call was executed |
| `script_git_commit` | SHA hash | Version of discovery script |
| `api_total_results` | integer | YouTube-reported total results for the query |
| `api_pages_retrieved` | integer | Actual pages fetched |

### 3.3 Discoverability Index

**Problem:** Strategy stacking creates unequal inclusion probabilities. A channel discoverable via 3 topics, 2 regions, and 3 durations has up to 18x the discovery probability of a single-path channel. Ignoring this biases unweighted estimates.

**Solution:** For each channel in the expanded sample, compute a **discoverability index**: the number of unique (keyword, topic, region, duration, window, order) combinations that returned this channel. Report the distribution of this index. Use it as:
- A control variable in regressions (channels with higher discoverability are systematically different)
- An analytic weight (inverse discoverability weighting) for sensitivity analyses
- A stratification variable (analyses within low-discoverability vs. high-discoverability subsets)

---

## 4. Power Analysis Framework

### 4.1 Effect Size Benchmarks

Effect sizes from the dissertation CH2 gender gap paper and the literature:

| Comparison | Plausible Effect Size | Source |
|------------|----------------------|--------|
| Gender gap in subscriber growth | Cohen's d = 0.10-0.20 (small) | CH2 preliminary estimates; Duffy et al. 2021 |
| AI adoption on engagement (within-creator) | Cohen's d = 0.05-0.15 | No prior; conservatively small |
| Intent vs. non-intent trajectory difference | Cohen's d = 0.10-0.25 | No prior; moderate based on strategic management literature |
| Gender x AI interaction | Cohen's d = 0.03-0.10 | Interaction effects are typically ~50% of main effects |

### 4.2 Power at Current and Projected Sample Sizes

Power calculations below use a two-sample t-test at alpha=0.05, two-sided, with equal group sizes. **Important caveat:** For the DiD comparisons (rows 2, 4, 5), these are upper bounds on power. DiD with panel data and serial correlation requires cluster-robust inference at the channel level, which reduces effective sample size. Bertrand, Duflo & Mullainathan (2004) show that ignoring serial correlation in DiD inflates rejection rates by 2-5x. The actual effective N depends on the intra-cluster correlation (ICC) of the outcome variable, which will be estimated from early panel data. If ICC > 0.30, the effective N for DiD comparisons should be deflated by a factor of approximately 1/(1 + (T-1)*ICC) where T is the number of time periods.

| Comparison | N per group (current) | Power for d=0.10 | N per group (projected) | Power for d=0.10 | Power for d=0.05 |
|------------|----------------------|-------------------|------------------------|-------------------|-------------------|
| A vs. A' | 26K vs. 11K | >99% | 80K vs. 60K | >99% | >99% |
| Within-A DiD (treated vs. control) | ~2.6K vs. ~23.7K (10% adoption) | 97% | ~8K vs. ~72K | >99% | 96% |
| Gender gap panel (male vs. female) | 6,345 vs. 3,383 | 98% | same | same | 78% |
| Gender x AI interaction | ~635 vs. ~338 (10% adoption) | 28% | same | same | 11% |
| Subgroup: gaming A' creators | ~1,100 | 20% (vs. matched A) | ~6,000 | 62% | 20% |

### 4.3 What Power Analysis Reveals

1. **Main comparisons (A vs. A', within-stream DiD) are already overpowered at current N** for effect sizes d >= 0.10. The expansion strategies do NOT change power for these comparisons in any meaningful way. Current N is sufficient.

2. **The binding constraint is subgroup analysis.** The expansion strategies matter for content-category-specific comparisons (e.g., gaming intent vs. gaming non-intent creators) and for triple interactions (gender x AI x category). At current N, gaming A' has only ~1,100 channels; at projected 60K, it would have ~6,000 — enough for moderate effects but still underpowered for small ones.

3. **The gender x AI interaction in the gender gap panel is underpowered regardless of expansion.** The gender gap panel is fixed at 9,760 channels. If 10% adopt AI, the treated female subgroup is ~338. No expansion strategy changes this. This is a floor constraint that requires methodological solutions (Bayesian methods, continuous treatment measures) rather than more data.

4. **Decision rule:** Expansion strategies are justified primarily for subgroup power, not main-effect power. The question for each strategy is: "Does this strategy add channels in currently underpowered subgroups?" not "Does this strategy increase total N?"

### 4.4 Subgroup Power Requirements

| Subgroup | Current N (A') | Needed N for 80% power at d=0.10 | Gap | Strategy most likely to fill |
|----------|---------------|----------------------------------|-----|------------------------------|
| Gaming A' | ~1,100 | ~3,200 | ~2,100 | topicId=Gaming, videoDuration=short |
| Beauty/Fashion A' | ~400 | ~3,200 | ~2,800 | safeSearch=none, topicId=Lifestyle |
| Education A' | ~600 | ~3,200 | ~2,600 | topicId=Education |
| Hindi A' | ~800 | ~3,200 | ~2,400 | regionCode=IN |
| Arabic A' | 0 (wave 2) | ~3,200 | ~3,200 | regionCode=SA,EG |

*Note: Subgroup Ns are approximate extrapolations from Stream A category distribution applied to A' targets. Actual distributions will differ because A' uses content keywords that skew toward gaming, cooking, and tutorials.*

---

## 5. Pre-Registration and Analytical Commitments

### 5.1 Pre-Registration Plan

The sampling protocol and primary analyses will be pre-registered on OSF before expansion strategy deployment. The pre-registration will include:

1. **Sampling protocol:** Exact keyword lists, API parameters for each strategy, dedup rules, provenance fields, GO/NO-GO criteria from validation framework
2. **Primary hypotheses (3-5):** Specific stream comparisons, DVs, significance thresholds, and whether each is descriptive or causal
3. **Primary vs. exploratory analysis designation:** All analyses not pre-registered as primary are exploratory and will be labeled as such
4. **Multiple comparison correction:** Benjamini-Hochberg FDR correction (chosen over Bonferroni for its greater power with correlated tests) at q = 0.05 for the set of primary hypotheses

### 5.2 Primary vs. Exploratory Analyses

**Primary (pre-registered):**
1. Descriptive comparison of A vs. A' on 6-month subscriber growth trajectory, conditional on language and content category
2. Staggered DiD for AI adoption effect on channel engagement within Stream A (Callaway & Sant'Anna estimator)
3. Gender x AI adoption interaction within the gender gap panel

**Exploratory (not pre-registered, labeled as such):**
- All subgroup analyses by language, content category, or discovery method
- All cross-stream comparisons (A vs. B, A vs. D)
- All expansion-strategy-specific analyses

### 5.3 Pre-Registered Analytical Thresholds

All thresholds used in decision rules and robustness checks are pre-committed here to prevent post-hoc rationalization:

| Threshold | Value | Used In | Justification |
|-----------|-------|---------|---------------|
| Leave-one-strategy-out shift | >15% of point estimate | Section 6.1 (robustness) | Follows Oster (2019) convention for coefficient stability; 15% is between "trivially different" (~5%) and "economically significant" (~25%) |
| Covariate balance SMD | >0.25 triggers IPW | Section 6.2 (balance) | Cohen's conventional "small" effect = 0.20; 0.25 is a common threshold in matching/weighting literature (Stuart 2010) |
| Construct validity accuracy (base) | >70% | Section 6.3 | Above-chance (50%) + meaningful margin. A vs. A' should be distinguishable if the construct is real |
| Construct validity accuracy (expanded) | <60% signals dilution | Section 6.3 | Approaching chance indicates the expansion has merged the two populations. Gap between 70% and 60% = 10pp tolerance for noise |
| Minimum cell size for subgroup analysis | N >= 200 per cell | Section 4.4 | Balances statistical reliability with analytical coverage. At N=200, a two-sample t-test has 80% power for d=0.28 |
| Minimum cell size for coverage rates | N >= 50 per cell | Section 1.2 | Standard threshold for proportions (ensures standard error < 0.07 at p=0.5) |
| Pre-trends test significance | p < 0.05 (joint Wald) | Section 6.4.2 | Conventional significance level; report individual coefficients regardless |
| Discovery method predicts adoption | F-test p < 0.05 | Section 6.4.3 | Conventional significance level; triggers stratified analysis |
| Rambachan-Roth sensitivity | M = {0, δ/2, δ, 2δ} | Section 6.4.2 | Standard grid from Rambachan & Roth (2023); δ = largest pre-treatment coefficient |
| Multiple comparison correction | BH-FDR at q = 0.05 | Section 5.1 | Controls false discovery rate at 5% across primary hypotheses |
| Power calculation alpha | α = 0.05, two-sided | Section 4.2 | Conventional; power tables use equal allocation unless noted |
| Validation GO/NO-GO criteria | Per-strategy in EXPANSION_VALIDATION_FRAMEWORK.md | Section 2 (all strategies) | Pre-committed before pilots; not adjustable post-hoc |

**Commitment:** If any threshold triggers a remedial action (e.g., IPW for SMD > 0.25), the remedial analysis REPLACES the naive analysis in the primary results, not appended as a robustness check. The naive version moves to the appendix.

---

## 6. Robustness Protocol

### 6.1 Mandatory Robustness Checks

Every primary analysis will be presented in three versions:

1. **Base sample only:** Channels discovered via the baseline `order=date` search with no expansion parameters. This is the cleanest, most homogeneous sample. If the result holds here, it is robust to any concerns about expansion-induced bias.

2. **Full expanded sample:** All channels, with `discovery_method` and `discoverability_index` as control variables. If this agrees with (1), the expansion added power without introducing bias.

3. **Leave-one-strategy-out:** Re-run the analysis excluding channels from each expansion strategy, one at a time. If excluding any single strategy changes the point estimate by >15%, that strategy is introducing compositional bias, and its channels should be excluded from the primary analysis.

### 6.2 Covariate Balance Protocol

Before any substantive analysis, produce a balance table comparing channels across discovery methods on:
- Subscriber count (at discovery)
- View count (at discovery)
- Video count (at discovery)
- Channel creation date
- Content category distribution
- Language distribution
- Country distribution

Compute standardized mean differences (SMDs) between base and each strategy. Flag any SMD > 0.25 (moderate imbalance). If imbalance is detected, apply inverse probability weighting using a logistic regression of `discovery_method` on observables.

### 6.3 Construct Validity Test for A vs. A'

After expansion, test whether the intent vs. non-intent distinction remains empirically meaningful:
- Train a classifier (logistic regression on observables: category, language, video count, subscriber count at discovery) to predict stream membership (A vs. A')
- If classification accuracy is >70% for base-discovered channels but drops below 60% for expanded channels, the expansion is diluting the construct
- Report the classification accuracy in both samples

### 6.4 Within-Stream DiD Identification Strategy

#### 6.4.1 Causal Structure (Directed Acyclic Graph)

The within-stream DiD exploits staggered AI adoption timing. The causal structure:

```
Channel Characteristics (U)
  ├──→ Discovery Method (D)    [pre-treatment, fixed at data collection]
  ├──→ AI Adoption Timing (T)  [treatment: when/whether creator adopts AI tools]
  ├──→ Engagement Trajectory (Y) [outcome: subscriber growth, views, etc.]
  └──→ Content Category (X)    [observed covariate]

AI Adoption Timing (T) ──→ Engagement Trajectory (Y)  [causal effect of interest]

Discovery Method (D) ──/──→ AI Adoption Timing (T)  [assumption: D does not cause T]
Discovery Method (D) ──/──→ Engagement Trajectory (Y) [assumption: D does not directly cause Y]
```

**Key identifying assumption:** Conditional on observed channel characteristics (content category, language, creation date, baseline subscriber count), the timing of AI adoption is independent of potential outcomes. Early adopters and late/never adopters would have followed parallel trajectories absent adoption.

**Why staggered adoption provides variation:** AI tool availability rolls out continuously (new tools, platform features, API changes). Creators adopt at different times based on: awareness (exposure to AI content), risk tolerance, content format suitability, and resource constraints. This generates within-stream variation in adoption timing that is plausibly exogenous conditional on observables — no single policy shock determines adoption for all creators simultaneously.

**Threat to exogeneity:** If a creator's unobserved "strategic sophistication" drives both early AI adoption AND faster growth, the parallel trends assumption fails. This is the standard selection-on-unobservables concern. We address it with: (a) event-study plots showing pre-trends, (b) sensitivity analysis using Rambachan & Roth (2023) bounds on violations of parallel trends, and (c) the Callaway & Sant'Anna (2021) estimator's group-time structure, which allows heterogeneous treatment effects and avoids the "negative weighting" problem of TWFE.

#### 6.4.2 Estimator Specification

**Primary estimator:** Callaway & Sant'Anna (2021) staggered DiD.

- **Group definition (g):** Calendar month of first AI-related video upload (detected via keyword matching on title/description, validated by transcript analysis). Groups: {2026-01, 2026-02, ..., 2026-06, never-treated}.
- **Time periods (t):** Weeks (for subscriber/view dynamics) or months (for video output/category shifts).
- **Outcome variables (Y):** (a) Weekly subscriber growth rate, (b) weekly view growth rate, (c) monthly video output count, (d) monthly unique content category count.
- **Covariates (X):** Content category (primary), language, creation date, baseline subscriber count (log), baseline video count, discoverability index.
- **Aggregation:** Group-time ATT(g,t) estimates aggregated using the "simple" weighting scheme (equally weighted across groups and time periods). Report both the overall ATT and the dynamic event-study ATT(e) for e = {-12, -11, ..., -1, 0, 1, ..., 24} weeks relative to adoption.

**Why CS over TWFE:** Two-way fixed effects (TWFE) with staggered adoption produces biased estimates when treatment effects are heterogeneous across groups or over time (Goodman-Bacon 2021; de Chaisemartin & d'Haultfœuille 2020). With 6 adoption cohorts spanning H1 2026, treatment effect heterogeneity is likely (early adopters may differ from late adopters). CS avoids this by estimating group-time specific effects and aggregating with proper weights.

**Pre-trends test:** For each group g, estimate ATT(g,t) for t < g (pre-treatment periods). Test the joint null that all pre-treatment ATT(g,t) = 0. Report individual event-study coefficients and the Wald test p-value.

**Sensitivity to parallel trends violations:** Apply Rambachan & Roth (2023) to bound the treatment effect under controlled departures from parallel trends. Report results under M = {0, δ/2, δ, 2δ} where δ is the largest pre-treatment coefficient.

#### 6.4.3 Discovery Method as a Pre-Treatment Variable

- Plot event-study coefficients for leads and lags around the AI adoption date
- Test whether discovery method predicts AI adoption timing (regress adoption date on discovery_method dummies, controlling for content category and language)
- If discovery_method predicts adoption timing (F-test p < 0.05), it is a confounder. In this case:
  - Estimate DiD within discovery-method strata
  - Present stratified results alongside the pooled estimate
  - Include discovery_method as a covariate in the CS estimator's propensity score model

**Why conditioning on discovery method is safe:** Discovery method is determined by the researcher's API query at a fixed point in time, before any outcomes are realized. It cannot be caused by future outcomes (no reverse causality) and is not a descendant of the treatment on the DAG. The concern is that discovery method proxies for channel characteristics (e.g., topicId-discovered channels are in popular topics) that also predict outcomes. This is classic confounding, not collider bias, and conditioning on it is appropriate — provided the confounding is on observables. If unobservable channel quality drives both discoverability and outcomes, conditioning on discovery method does not fully resolve confounding.

**Falsification test:** Estimate the DiD on a "placebo treatment" — randomly reassigning AI adoption dates within each content category. If the placebo DiD returns a significant effect, the identification strategy is suspect.

---

## 7. Strategy-Specific Risk Assessment

### 7.1 Strategy Risk Matrix

| Strategy | Selection Bias Risk | A vs. A' Comparability Risk | DiD Parallel Trends Risk | Recommended Use |
|----------|--------------------|-----------------------------|--------------------------|-----------------|
| 1. topicId | **Medium.** Topic classifier correlated with channel maturity. | **Medium.** Asymmetric A/A' composition shift. | **Low.** Topic is pre-treatment. | Primary + robustness |
| 2. relevance | **High.** Popularity-based selection. | **High.** Changes the DGP of one stream. | **High.** Relevance-discovered channels have different baselines. | Robustness only |
| 3. regionCode | **Low.** Geographic coverage, not selection. | **Low.** Symmetric across A and A'. | **Low.** Region is pre-treatment. | Primary + robustness |
| 4. safeSearch | **Low.** Coverage improvement. | **Low.** Symmetric across A and A'. | **Low.** Content category shift is minor. | Primary |
| 5. duration | **Medium.** Duration proxies for content format. | **Medium.** Asymmetric A/A' benefit. | **Low.** Duration is pre-treatment. | Primary + robustness |
| 6. 12h windows | **None.** Mechanical. | **None.** A'-only but no compositional change. | **None.** No selection. | Primary |

### 7.2 Recommended Tiering for Analysis

**Tier 1 (Primary analytical sample):** Base + safeSearch=none + regionCode + 12h windows. These strategies improve coverage without introducing new selection mechanisms.

**Tier 2 (Extended sample for robustness):** Tier 1 + topicId + videoDuration. These add channels that may differ systematically from Tier 1 on observables. Use for subgroup analysis and robustness checks.

**Tier 3 (Sensitivity analysis only):** Tier 2 + order=relevance. Relevance-discovered channels are systematically different (higher engagement baselines). Present results on Tier 3 only as "results hold even when including relevance-ordered channels."

---

## 8. Specific Questions for the Academic Panel

### 8.1 Selection Bias
Q1: Does the topicId selection model in Section 2 adequately characterize the bias? Is the empirical validation requirement (Section 2, Strategy 1) sufficient?
Q2: Is the Tier 1/2/3 analytical tiering (Section 7.2) the right way to handle the order=relevance risk?
Q3: Does safeSearch=none introduce noise, or is the R1 panel's unanimous GO verdict correct?

### 8.2 Comparability
Q4: Does regionCode expansion create heterogeneity that complicates comparisons, or is it benign geographic coverage improvement?
Q5: Is the construct validity test (Section 6.3) adequate for detecting A vs. A' dilution under asymmetric expansion?

### 8.3 Causal Inference
Q6: Does the parallel trends diagnostic (Section 6.4) adequately address discovery-method confounding in the DiD?
Q7: Is the "discovery method is pre-treatment by construction" argument (Section 6.4) valid, or is there a subtlety we're missing?

### 8.4 Power and Design
Q8: Given the power analysis (Section 4), are the expansion strategies justified primarily for subgroup power? Is this framing correct?
Q9: Is the three-version robustness protocol (Section 6.1) sufficient, or should additional sensitivity checks be specified?

### 8.5 Integrity
Q10: Is the pre-registration plan (Section 5) adequate? What specific hypotheses should be pre-registered?
Q11: Does the discoverability index (Section 3.3) adequately address unequal inclusion probabilities?

---

## 9. Known Constraints

1. **YouTube Search API is non-deterministic** (Rieder et al. 2025; Efstratiou 2025). Applies equally to all strategies. Exact replication is not possible; methodological replication (same procedure, different sample) is the appropriate standard.
2. **~500-result cap is per-query.** Each strategy parameter combination gets its own cap.
3. **A and A' use cross-deduplication.** Expanding A increases A' exclusion list.
4. **Category keyword expansion was REJECTED** (introduces topic selection bias at keyword level). TopicId partitioning is distinct: same keywords, partitioned index.
5. **All streams except C use keyword-based discovery.** Stream C is the linchpin of representativeness claims.
6. **Gender gap panel (9,760) is fixed.** Expansion strategies do not affect it.
7. **Non-determinism is unmeasured.** A replicability experiment (10 identical queries x 48 hours, measuring Jaccard overlap) should be run before production to quantify baseline non-determinism. Then repeat with topicId to measure whether partitioning increases instability.

---

## Evaluation Record

### /plan-eval: 8-Expert Academic Panel (Feb 19, 2026)

**Panel composition:** Econometrician (DiD specialist), Survey Sampling Methodologist, Platform Data Peer Reviewer (Reviewer 2), Sociologist of Digital Platforms, Power Analysis Statistician, IR/API Measurement Specialist, Replication/Open Science Specialist, Labor Economics/IO Methodologist

### Score Trajectory

| Round | Average | Low | High | Key Fix |
|-------|---------|-----|------|---------|
| R1 | 63.1 | ~55 | ~72 | Baseline: vague identification, no thresholds, no coverage protocol |
| R2 | 75.9 | ~68 | ~82 | Added selection models, tiering system, power analysis, pre-registration plan |
| R3 | 81.5 | 77.3 | 84.8 | Formalized DiD (DAG + CS spec + R&R), operationalized coverage calibration, 12 pre-committed thresholds |

### Final Expert Scores (R3)

| Expert | Score | Summary |
|--------|-------|---------|
| Econometrician | 84.8 | DAG and CS spec are publication-quality; wants Oster delta for unobservables |
| Sampling Methodologist | 80.8 | Coverage calibration well-specified; needs design effects under weighting |
| Reviewer 2 | 77.3 | AI adoption measurement is the Achilles heel; too much aspirational infrastructure |
| Sociologist | 79.9 | Scope-of-inference framing is exemplary; needs named theoretical framework |
| Power Statistician | 83.2 | Correct subgroup power framing; should compute effective N under serial correlation |
| API Measurement | 81.9 | Provenance above field standard; replicability experiment needs acceptance criteria |
| Open Science | 82.4 | Threshold table is strongest section; primary hypotheses need directional predictions |
| Labor Econ/IO | 81.4 | Tiering system is practically useful; report discovery-method-stratified ATTs |

### Remaining Weaknesses (Not Fixable in This Document)

1. **AI adoption measurement instrument** — entire causal framework rests on keyword-based classification with no validation evidence. Requires future pipeline work: human-coded validation sample, precision/recall thresholds, conditional execution of DiD.
2. **Effective N under serial correlation** — ICC deflation formula provided but never computed. Requires panel data to estimate ICC. A table at ICC={0.1, 0.2, 0.3, 0.4} and T={12, 26, 52} would transform power analysis from upper bounds to realistic estimates.
3. **Named theoretical framework for A vs. A'** — paper-level decision. Candidates: organizational imprinting, strategic signaling, deliberate vs. emergent strategy. Not a sampling expansion concern.

### Changes Made Across 3 Rounds

**R1 → R2:**
- Added Section 1.2 (Scope of Inference) with target vs. accessible population distinction
- Added formal selection models for each strategy (Section 2)
- Added Section 4 (Power Analysis) with MDE tables and subgroup gap analysis
- Added Section 5 (Pre-Registration Plan) with primary/exploratory designation
- Added Section 6 (Robustness Protocol) with three-version requirement
- Added Section 6.2 (Covariate Balance) with SMD threshold
- Added Section 6.3 (Construct Validity Test) for A vs. A'
- Added Section 3.3 (Discoverability Index)
- Added Section 7 (Strategy Risk Matrix + Tier 1/2/3 hierarchy)
- Added 4 API metadata provenance fields

**R2 → R3:**
- Replaced Section 6.4 with full DiD identification strategy: DAG, CS estimator specification (group/time/outcome/covariate definitions), Rambachan & Roth sensitivity grid, falsification test, discovery method conditioning justification
- Expanded Section 1.2 coverage calibration with: formula, coverage-weighted estimates, selection profile comparison, Latin-alphabet limitation, minimum cell sizes
- Added Section 5.3 with 12 pre-registered analytical thresholds (leave-one-out 15%, SMD 0.25, construct validity 70%/60%, BH-FDR q=0.05, etc.) with citations and justifications
- Added serial correlation caveat to power analysis with Bertrand et al. (2004) reference and ICC deflation formula
- Commitment that remedial analyses REPLACE naive analyses in primary results
