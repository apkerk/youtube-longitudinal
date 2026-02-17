# DECISION_LOG.md
# YouTube Longitudinal Data Collection

## 001. Adoption of "Triple-Stream" Sampling Design
**Date:** Feb 02, 2026
**Status:** IMPLEMENTED

### Context
We needed a sampling strategy to study "New Creator" virality.
- **Problem:** "Random" broad queries (e.g., "video", "a") return high-view content (Median ~600k views), missing the "long tail" of true new entrants.
- **Problem:** "Random Prefix" queries (e.g., "xyz") return true random content (Median ~20 views), but are too noisy and low-yield to find specific "entrepreneurial" creators.

### Decision
We adopted a **Triangulated (Triple-Stream) Design**:
1.  **Stream A (Intentional Cohort):** Targeted Keywords (`Welcome`, `Intro`) -> Captures the Treatment Group (New Entrepreneurs).
2.  **Stream B (Visible Market):** Vowel Rotation (`a`, `e`, `i`) -> Captures the Competitive Context (Active Market).
3.  **Stream C (Deep Random):** Random Prefix (`xyz`) -> Captures the Null Baseline (Survivorship Control).

### Rationale
- **Survivorship Bias Control:** Stream C proves we aren't ignoring failed channels.
- **Market Context:** Stream B proves whether our cohort is "beating the market."
- **Efficiency:** Stream A maximizes the N for our primary variable of interest.

### Alternatives Considered
- *Single Random Sample:* Rejected. Would either miss the long tail (if broadly queried) or be 99% garbage (if prefix queried).
- *Two-Stream (New + Random):* Rejected. "Random" was ambiguous. We split it into "Visible" vs. "Deep" to be precise.

### Impact
- **Quota:** daily usage increased to ~700k units (70%).
- **Complexity:** Requires managing 3 scripts (`discover_cohort.py`, `discover_visible.py`, `discover_deep_random.py`).
- **Validity:** dramatically increases the academic defensibility of the study.

## 002. Gender Gap Panel: Coded Channels Only (9,760 of 14,169)
**Date:** Feb 16, 2026
**Status:** DECIDED

### Context
Bailey's dataset has 14,169 unique channels, but ~4,100 have blank gender and ~4,100 have blank race (largely overlapping). Channels without coded gender/race lack an identifiable creator and are less analytically useful for the gender gap study. Full panel would require 370K API units/day and produce 1.2 GB/day of video stats.

### Decision
Restrict the longitudinal panel to the **9,760 channels with both gender AND race coded** (excluding blank and undetermined). This drops ~31% of channels but retains all analytically actionable observations.

### Rationale
- The gender gap analysis requires gender and race as key independent variables. Channels missing both can't contribute to any regression.
- Saves 35% on quota (240K vs 370K units/day) and storage (269 vs 416 GB/year).
- Uncoded channels can always be added back later if gender/race coding is completed.

### Alternatives Considered
- *Full 14,169 panel:* Rejected. 4,400 channels with no gender/race provide no analytical value for the core research question.
- *Gender-only filter (10,092 channels):* Considered. Decided to require both gender AND race since intersectional analysis is a key design goal.

## 003. Dual-Cadence Collection: Daily Channels, Weekly Videos
**Date:** Feb 16, 2026
**Status:** DECIDED

### Context
With 9,760 channels and ~12M videos, collecting all video-level stats daily would use ~240K API units/day and produce ~756 MB/day. Channel-level stats for the same channels cost only ~195 units/day and ~1.1 MB/day.

### Decision
**Daily** collection of channel stats (subscribers, total views, video count). **Weekly** collection of video-level stats (per-video views, likes, comments). Implemented via `--mode channel|video|both` flag in daily_stats.py.

### Rationale
- Channel-level metrics (subscriber growth, total view growth) change meaningfully day-to-day and are the primary outcome variables for the gender gap study.
- Video-level metrics change more slowly for most videos and weekly snapshots capture sufficient variation for the staggered DiD design.
- Reduces daily quota from 240K to ~195 units and daily storage from 756 MB to 1.1 MB. Weekly video collection adds ~240K units and ~756 MB once per week.
- Total weekly cost: ~241K units + 756 MB (vs. 1.68M units + 5.3 GB at daily cadence).

### Alternatives Considered
- *Daily video stats:* Rejected. 7x the cost for marginal analytical gain. Most video view counts don't change meaningfully day-to-day.
- *Biweekly video stats:* Considered but weekly is standard in panel studies and keeps options open for time-series analysis.
