# Sampling Methodology Experiments Log
# YouTube Longitudinal Data Collection

**Purpose:** Systematic record of all sampling strategy experiments  
**Last Updated:** Feb 02, 2026  
**Principle:** "Test before you trust"

---

## How to Use This File

1. **Before production sampling:** Run diagnostic experiments
2. **Log all results:** Even failed experiments are valuable
3. **Compare strategies:** Use standardized metrics across experiments
4. **Inform decisions:** Use evidence to choose sampling parameters

---

## Standard Metrics for Comparison

| Metric | Definition | Why It Matters |
|--------|------------|----------------|
| **Median Views** | Median view count of sampled videos | Low = less algorithmic bias |
| **Zero-View %** | % of videos with 0 views | High = capturing "dark matter" |
| **Big Channel %** | % of channels with >1k subs | Low = capturing new/small creators |
| **Yield Rate** | % of results meeting target criteria | Higher = more efficient sampling |
| **Hit Rate** | % of queries returning >0 results | Low hit rate = inefficient (random prefix) |
| **New Creator %** | % of channels created in target window | Core metric for cohort studies |

---

## EXPERIMENT LOG

### EXP-001/003: Bias Profile Comparison (COMPLETED)
**Date:** Feb 02, 2026  
**Script:** `test_sampling_battery.py`  
**Question:** What is the "bias profile" of each sampling strategy?

**Method:**
- Strategy A: High-Vis (Vowels: a, e, i, o, u)
- Strategy B: Raw/Amateur (IMG, MVI, DSC, MOV, VID_)
- Strategy C: Random Prefix (3-char strings)
- Strategy D: Common Words (video, 2026, new)
- 3 batches per strategy, 50 results per batch
- Window: Jan 1-15, 2026

**Results:**
| Strategy | N | Median Views | Zero-View % | Median Subs | Big Channel % | Hit Rate % |
|----------|---|--------------|-------------|-------------|---------------|------------|
| High-Vis (Vowels) | 125 | **1,161,938** | 0.0 | 199,000 | **94.4** | 100.0 |
| Raw/Amateur (IMG) | 105 | 214 | 2.9 | 1,810 | 59.0 | 100.0 |
| Random Prefix | 150 | 305 | 2.0 | 533 | **39.3** | 100.0 |
| Common Words | 125 | 137,193 | 0.0 | 39,500 | 81.6 | 100.0 |

**Conclusion:** 
- ⚠️ **Vowel search is catastrophically biased** — median 1.16M views, 94% channels have >1k subs
- ✅ Random Prefix has lowest bias (39% big channels)
- ✅ Raw/Amateur queries capture low-engagement content (median 214 views)

**Decision Impact:** 
- Stream B (Vowels) should be labeled "Algorithm Favorites" not "Market Baseline"
- Random Prefix confirmed as best method for Stream C (Deep Random)
- Added Stream D (Amateur) using IMG/MVI/DSC queries

---

### EXP-002/010: New Creator Yield Rates (COMPLETED)
**Date:** Feb 02, 2026  
**Script:** `test_sampling_battery.py`  
**Question:** What % of videos from intent vs non-intent keywords belong to NEW channels?

**Method:**
- Intent Queries: "Welcome to my channel", "My first video", "Intro", "Introduction", "Vlog 1", "Channel Trailer", "Get to know me"
- Non-Intent Queries: "gameplay", "let's play", "tutorial", "recipe", "review", "unboxing", "haul"
- Filter: Channel created >= Jan 1, 2026
- Window: Jan 1-15, 2026
- Region: US

**Results:**
| Keyword Type | Channels Checked | New Channels | Yield Rate % |
|--------------|------------------|--------------|--------------|
| Intent Keywords (Stream A) | 307 | 39 | **12.7%** |
| Non-Intent Keywords (Stream A') | 312 | 6 | 1.92% |

**Viability Assessment:**
- ✅ Intent Keywords: **12.7% yield = EXCELLENT** (>5% threshold)
- ⚠️ Non-Intent Keywords: 1.92% yield = VIABLE but inefficient

**Conclusion:** 
- Intent keywords are **6.6x more efficient** at finding new creators
- Non-intent control group IS possible but requires more quota
- Stream A strategy fully validated

**Decision Impact:** Keep Stream A keywords as-is. Consider Stream A' for within-cohort control if budget allows.

---

## PLANNED EXPERIMENTS

### EXP-005: Channel ID Enumeration Hit Rate (COMPLETED - NOT VIABLE)
**Date:** Feb 02, 2026  
**Question:** What % of randomly generated channel IDs actually exist?

**Method:**
- Generated 100 random channel IDs (UC + 22 base64 chars)
- Checked existence via `channels.list`

**Results:**
- Attempts: 100
- Hits: 0
- Hit Rate: **0.0%**

**Conclusion:** ❌ **NOT VIABLE.** The YouTube channel ID space is too sparse. Would need 100,000+ attempts to find even a few valid channels. Not cost-effective.

**Decision:** Abandoned. Use Random Prefix search instead for unbiased sampling.

---

### EXP-006: Language Bias Detection (COMPLETED)
**Date:** Feb 02, 2026  
**Script:** `test_language_pagination.py`  
**Question:** Are English intent keywords missing non-English creators?

**Method:**
- Tested 8 languages: English, Spanish, Portuguese, Hindi, French, German, Korean, Japanese
- 3 intent keywords per language
- Same date filter (Jan 2026)
- Global search (no region filter)

**Results:**
| Language | Videos Found | Channels Checked | New Channels | Yield % |
|----------|--------------|------------------|--------------|---------|
| English | 125 | 123 | 38 | 30.89% |
| Spanish | 150 | 147 | 43 | 29.25% |
| Portuguese | 150 | 143 | 33 | 23.08% |
| **Hindi** | 150 | 136 | **48** | **35.29%** |
| French | 125 | 115 | 21 | 18.26% |
| German | 150 | 146 | 35 | 23.97% |
| Korean | 150 | 120 | 27 | 22.5% |
| Japanese | 125 | 106 | 26 | 24.53% |
| **TOTAL** | — | — | **271** | — |

**Key Findings:**
- 🚨 **English alone captures only 14% of findable new creators**
- Multilingual sampling expands population by **7.1x**
- **Hindi has highest yield (35.3%)** — higher than English!
- French has lowest yield (18.3%)

**Decision Impact:** 
- MUST expand Stream A to multilingual keywords
- Prioritize: Hindi, Spanish, English, German, Japanese, Korean, Portuguese, French

---

### EXP-007: Region Code Impact (COMPLETED)
**Date:** Feb 02, 2026  
**Question:** Does `regionCode=US` vs `regionCode=None` change sample composition?

**Method:**
- Query: "Welcome to my channel"
- Regions tested: Global (None), US, GB, IN, BR, DE
- Window: Jan 1-15, 2026

**Results:**
| Region | Videos Found | Median Views |
|--------|--------------|--------------|
| Global (None) | 25 | 46 |
| US | 50 | 36 |
| GB | 50 | 52 |
| IN | 50 | 43 |
| BR | 25 | 62 |
| DE | 50 | 52 |

**Conclusion:** ✅ Minimal bias across regions. Median views remarkably consistent (36-62). US returns more results than Global, likely due to API optimization.

**Decision:** Keep `regionCode=US` for consistency and higher yield.

---

### EXP-008: Pagination Depth Bias (COMPLETED)
**Date:** Feb 02, 2026  
**Script:** `test_language_pagination.py`  
**Question:** Do results at rank 1-50 differ systematically from deeper pages?

**Method:**
- Query: "a" (neutral, broad)
- Paginated through search results
- Compared metrics at different rank positions

**Results:**
| Page | Rank Range | Videos | Median Views | Median Subs | Big Channel % |
|------|------------|--------|--------------|-------------|---------------|
| 1 | 1-50 | 50 | 313,864 | 958,000 | 100.0% |
| 2 | 51-100 | 25 | 1,255,390 | 1,980,000 | 100.0% |

**Key Findings:**
- ❌ Only 2 pages returned (API limitation with date+query filters)
- ❌ Both pages show 100% big channels (>1k subs)
- ❌ Page 2 has HIGHER median views than page 1 (counterintuitive)
- **Pagination does NOT reduce algorithmic bias for broad queries**

**Decision Impact:** Abandon pagination as bias reduction strategy. Use query diversification instead.

---

### EXP-009: Temporal Stability (PLANNED)
**Question:** Do identical queries return similar results at different times of day?

**Method:**
- Run same query at 02:00, 08:00, 14:00, 20:00 UTC
- Compare overlap in results

**Status:** Not yet run

---

### EXP-010: Non-Intent Cohort Yield (COMPLETED - see EXP-002)
**Result:** 1.92% yield — viable but 6.6x less efficient than intent keywords.

---

## KEY FINDINGS SUMMARY

| Finding | Evidence | Implication |
|---------|----------|-------------|
| **Vowel search is MASSIVELY biased** | Median views 1.16M, 94% big channels | Stream B captures algorithm favorites, not "the market" |
| **Raw file queries reduce bias** | Median views 214 (5,400x lower than vowels) | Use IMG/MVI/DSC for amateur baseline |
| **Random prefix is least biased** | Median views 305, 39% big channels | Best for true random sample (Stream C) |
| **Intent keywords have 12.7% yield** | 39/307 channels were new (Jan 2026+) | Stream A strategy is highly efficient |
| **Non-intent keywords have 1.9% yield** | 6/312 channels were new | Possible for control, but 6.6x less efficient |
| **Channel ID enumeration not viable** | 0/100 hits | ID space too sparse, not worth quota |
| **Region codes don't bias much** | Median views 36-62 across all regions | Safe to use US for consistency |
| 🚨 **English misses 86% of new creators** | 38 vs 271 across 8 languages | MUST use multilingual keywords |
| **Hindi has HIGHEST yield (35.3%)** | 48 new channels vs 38 for English | Prioritize Hindi, Spanish alongside English |
| **Pagination doesn't reduce bias** | Page 2 has higher views than page 1 | Abandon pagination strategy |

---

## METHODOLOGY DECISIONS

| Decision | Date | Based On | Rationale |
|----------|------|----------|-----------|
| Use `order=date` not `relevance` | Feb 2026 | EXP-001 | Reduces popularity bias |
| Triple-stream design | Feb 2026 | EXP-003 | Different strategies capture different populations |
| **Redefine Stream B purpose** | Feb 02, 2026 | Bias Profile | Vowel search = "Algorithm Favorites" not "Market Baseline" |
| **Add Stream D (Amateur)** | Feb 02, 2026 | Bias Profile | IMG/MVI queries capture low-effort uploads (median 214 views) |
| **Keep Stream A as-is** | Feb 02, 2026 | Yield Experiment | 12.7% yield is excellent; intent keywords validated |
| **Keep Random Prefix for Stream C** | Feb 02, 2026 | Bias Profile | Lowest big-channel % (39.3%); best unbiased baseline |
| **Abandon Channel ID enumeration** | Feb 02, 2026 | EXP-005 | 0% hit rate; not cost-effective |
| **Keep regionCode=US** | Feb 02, 2026 | Region Impact | No significant bias; gives consistent results |

---

*This log is the audit trail for all sampling methodology decisions. Update after every experiment.*

