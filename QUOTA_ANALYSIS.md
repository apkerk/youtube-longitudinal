# Quota & Sample Size Analysis
# YouTube Longitudinal Data Collection

**Purpose:** Strategic planning for sample sizes and polling frequencies  
**Last Updated:** Feb 02, 2026  
**Daily Quota:** 1,010,000 units

---

## API Cost Reference

| Operation | Cost | Batch Size | Effective Cost |
|-----------|------|------------|----------------|
| `search.list` | 100 units | 50 results | 2 units/result |
| `channels.list` | 1 unit | 50 channels | 0.02 units/channel |
| `videos.list` | 1 unit | 50 videos | 0.02 units/video |

**Key Insight:** Polling is 100x cheaper than collection.

---

## PART 1: COLLECTION COSTS (Finding New Channels)

### Stream A: Intentional Cohort (English)
- Search: 100 units/call → 50 videos → ~40 unique channels
- Channel check: 1 unit/50 channels
- **Yield:** 12.7% new creators (from earlier experiment)
- **Cost per new channel:** ~200 units (search) + ~1 unit (check) ≈ **25 units/new channel**

### Stream A (Multilingual Expansion)
- 8 languages × 3 keywords = 24 search calls = 2,400 units
- ~1,000 unique channels to check = 20 units
- ~271 new channels found
- **Cost per new channel:** ~9 units/new channel (more efficient!)

### Stream C: Deep Random (Random Prefix)
- Search: 100 units/call → variable results (some 0, some 50)
- Hit rate: ~100% with short prefixes
- **Cost per channel:** ~4 units/channel (no filtering needed)

### Stream D: Amateur (IMG/MVI/DSC)
- Similar to Deep Random
- **Cost per channel:** ~4 units/channel

---

## PART 2: POLLING COSTS (Tracking Existing Channels)

### Cost Formula
```
Daily Polling Cost = (Total Channels / 50) × 1 unit
```

| Sample Size | Daily Cost | Weekly Cost | Monthly Cost |
|-------------|------------|-------------|--------------|
| 10,000 | 200 units | 29 units/day | 7 units/day |
| 50,000 | 1,000 units | 143 units/day | 33 units/day |
| 100,000 | 2,000 units | 286 units/day | 67 units/day |
| 500,000 | 10,000 units | 1,429 units/day | 333 units/day |
| 1,000,000 | 20,000 units | 2,857 units/day | 667 units/day |

**Key Insight:** Even 1 MILLION channels can be polled daily for only 2% of your quota.

---

## PART 3: SCENARIO ANALYSIS

### Scenario A: Maximum Sample Size (Daily Polling)

**Goal:** Largest possible sample with daily tracking

| Allocation | Units/Day | Purpose |
|------------|-----------|---------|
| Collection | 500,000 | Find new channels |
| Daily Polling | 500,000 | Track existing |
| **Buffer** | 10,000 | Safety margin |

**Polling capacity:** 500,000 × 50 = **25,000,000 channels/day**

This is absurdly large. You could track the entire "active" portion of YouTube daily.

**Realistic constraint:** Data storage, processing, research utility—not quota.

---

### Scenario B: Balanced Multi-Stream (Recommended)

**Goal:** Multiple meaningful samples with daily polling

| Stream | Target Size | Collection Cost | Daily Poll Cost |
|--------|-------------|-----------------|-----------------|
| A: Intentional (Multilingual) | 50,000 | 450,000 units (one-time) | 1,000 |
| B: Algorithm Favorites | 10,000 | 100,000 units (one-time) | 200 |
| C: Deep Random | 50,000 | 200,000 units (one-time) | 1,000 |
| D: Amateur | 20,000 | 80,000 units (one-time) | 400 |
| **TOTAL** | **130,000** | **830,000** (one-time) | **2,600/day** |

**Daily budget after initial collection:**
- Polling: 2,600 units (0.26% of quota)
- Remaining: 1,007,400 units for NEW collection or experiments

**This means:** After initial ramp-up, you can add ~5,000 new channels/day to your panel WHILE polling 130,000 existing channels daily.

---

### Scenario C: Massive Sample with Weekly Polling

**Goal:** Very large samples, less frequent tracking

| Stream | Target Size | Weekly Poll Cost |
|--------|-------------|------------------|
| A: Intentional | 200,000 | 571 units/day |
| B: Algorithm Favorites | 50,000 | 143 units/day |
| C: Deep Random | 200,000 | 571 units/day |
| D: Amateur | 100,000 | 286 units/day |
| **TOTAL** | **550,000** | **1,571 units/day** |

**Trade-off:** 4x larger sample, but you miss day-to-day viral spikes.

---

### Scenario D: Monthly Polling (Academic Research Mode)

**Goal:** Maximum statistical power, accept delayed measurement

| Stream | Target Size | Monthly Poll Cost |
|--------|-------------|-------------------|
| A: Intentional | 500,000 | 333 units/day |
| B: Algorithm Favorites | 100,000 | 67 units/day |
| C: Deep Random | 500,000 | 333 units/day |
| D: Amateur | 200,000 | 133 units/day |
| **TOTAL** | **1,300,000** | **866 units/day** |

**1.3 MILLION channels** tracked monthly for less than 0.1% of daily quota.

---

## PART 4: POLLING FREQUENCY TRADE-OFFS

### What Changes Day-to-Day?
| Metric | Volatility | Best Frequency |
|--------|------------|----------------|
| View count | **HIGH** (viral spikes) | Daily |
| Subscriber count | Medium | Weekly |
| Video count | Low | Weekly |
| Channel status | Very low | Monthly |

### Research Question Alignment

| Research Question | Required Frequency | Rationale |
|-------------------|-------------------|-----------|
| "Shape of virality curves" | **Daily** | Need to capture 24-48hr spikes |
| "Growth trajectories" | Weekly | Week-over-week is standard |
| "Survival analysis" | Monthly | Events (quit/banned) are rare |
| "Market structure" | Monthly | Slow-moving |

### Hybrid Recommendation
```
Tier 1 (Hot): Daily polling
- Channels with activity in last 7 days
- Channels with >10% growth in last poll
- Est. 10-20% of sample

Tier 2 (Warm): Weekly polling  
- Channels with activity in last 30 days
- Est. 30-40% of sample

Tier 3 (Cold): Monthly polling
- Inactive channels (survivorship tracking)
- Est. 40-60% of sample
```

---

## PART 5: RECOMMENDED CONFIGURATION

### Phase 1: Initial Collection (Weeks 1-2)

| Task | Daily Units | Duration | Total |
|------|-------------|----------|-------|
| Stream A (Multilingual) | 200,000 | 7 days | 1,400,000 |
| Stream B (Algo Faves) | 50,000 | 3 days | 150,000 |
| Stream C (Deep Random) | 150,000 | 7 days | 1,050,000 |
| Stream D (Amateur) | 100,000 | 5 days | 500,000 |

**Expected yield:**
- Stream A: ~50,000 new intentional creators
- Stream B: ~10,000 algorithm favorites
- Stream C: ~100,000 random channels
- Stream D: ~30,000 amateur uploads

**Total panel:** ~190,000 channels

### Phase 2: Steady State (Week 3+)

| Activity | Daily Units |
|----------|-------------|
| Daily poll (Hot tier, ~20k channels) | 400 |
| Weekly poll (Warm tier, ~70k channels) | 200 |
| Monthly poll (Cold tier, ~100k channels) | 67 |
| New collection (ongoing) | 100,000 |
| Experiments/buffer | 809,333 |
| **TOTAL** | **~910,000** |

**You retain 90%+ of daily quota for flexibility.**

---

## PART 6: SAMPLE SIZE JUSTIFICATION

### Statistical Power Analysis

For detecting a "medium" effect size (Cohen's d = 0.5):
- 95% confidence, 80% power
- Required N per group: ~64

For detecting a "small" effect size (d = 0.2):
- Required N per group: ~394

**Your proposed samples (10k-100k per stream) are massively overpowered for standard hypothesis testing.**

### Why Large Samples Anyway?

1. **Subgroup analysis:** Stratify by language, category, timing
2. **Rare events:** Viral success is <1% of channels
3. **Longitudinal attrition:** 30-50% may become inactive
4. **Heterogeneity:** Want to detect patterns across diverse populations

### Recommended Minimum Viable Samples

| Stream | Minimum | Recommended | Luxury |
|--------|---------|-------------|--------|
| A: Intentional | 5,000 | 50,000 | 200,000 |
| B: Algo Faves | 2,000 | 10,000 | 50,000 |
| C: Deep Random | 10,000 | 50,000 | 500,000 |
| D: Amateur | 5,000 | 20,000 | 100,000 |

---

## PART 7: FINAL RECOMMENDATION

### The "Goldilocks" Configuration

| Stream | Size | Poll Frequency | Daily Cost |
|--------|------|----------------|------------|
| A: Intentional (8 languages) | 50,000 | Daily (hot) / Weekly (warm) | 500 |
| B: Algorithm Favorites | 10,000 | Weekly | 29 |
| C: Deep Random | 50,000 | Monthly | 33 |
| D: Amateur | 20,000 | Weekly | 57 |
| **TOTAL** | **130,000** | Mixed | **619 units/day** |

**Ongoing collection:** 200,000 units/day → ~2,000 new channels/day

**Remaining quota:** ~800,000 units/day for experiments, deeper dives, or expansion.

---

## Summary Table

| Metric | Value |
|--------|-------|
| **Total sample size** | 130,000 channels |
| **Polling cost** | 619 units/day (0.06% of quota) |
| **Collection cost** | 200,000 units/day (20% of quota) |
| **Remaining for flexibility** | 809,000 units/day (80% of quota) |
| **Time to full panel** | ~14 days |

---

*This analysis demonstrates that quota is NOT your constraint. Data management, research focus, and analytical capacity are the real limiting factors.*

