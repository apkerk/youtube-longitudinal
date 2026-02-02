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
