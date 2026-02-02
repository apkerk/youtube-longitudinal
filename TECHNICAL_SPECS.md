# Technical Specifications — YouTube Longitudinal Project

**Purpose:** Centralized technical details for replication and onboarding  
**Last Updated:** Feb 02, 2026  
**Use:** Reference when running discovery scripts or analyzing sampling bias

---

## PROJECT OVERVIEW

- **Project:** YouTube Longitudinal Study (New Creator Virality)
- **Type:** Quantitative / Big Data
- **Primary Software:** Python 3.12 (EXTREMELY STRICT RULES)
- **API:** YouTube Data API v3 (Quota: 1M units/day)

---

## SAMPLING SPECIFICATIONS (The Triple-Stream Design)

### Stream A: Intentional Cohort (Treatment)
*   **Target:** New creators signaling entrepreneurial intent.
*   **Method:** `search.list(q=KEYWORDS, type='video', order='date')` -> Filter `publishedAt`
*   **Keywords:**
    *   "Welcome to my channel"
    *   "My first video"
    *   "Intro"
    *   "Vlog 1"
    *   "Channel Trailer"
    *   "Introduction"
*   **Filter Logic:**
    *   Collect Video ID -> Get Channel ID.
    *   Get Channel Details (`brandingSettings`, `statistics`).
    *   **KEEP IF:** Channel Creation Date >= Jan 1, 2026.
*   **Daily Quota:** ~600,000 units.

### Stream B: Visible Market (Control)
*   **Target:** The active, visible YouTube ecosystem (active competitors).
*   **Method:** `search.list(q=VOWELS, type='video', order='date')`
*   **Keywords (Rotated):**
    *   `a`, `e`, `i`, `o`, `u`
    *   `video`
    *   `shou`
*   **Filter Logic:**
    *   Collect Video ID -> Get Channel ID.
    *   **KEEP IF:** Channel is active (Video Count >= 1). No date filter.
*   **Daily Quota:** ~100,000 units.

### Stream C: Deep Random (Survivorship Control)
*   **Target:** The hidden "Dark Matter" (unbiased sample).
*   **Method:** Random Prefix Sampling (Zhou et al., 2011).
*   **Keywords:** Randomly generated 3-character strings (e.g., `x7z`, `1a2`).
*   **Filter Logic:**
    *   Collect whatever is returned. No filtering.
*   **Daily Quota:** ~250,000 units.

---

## DATA STRUCTURES

### Channel Object (Common Schema)
| Variable | Type | Source | Definition |
|----------|------|--------|------------|
| `channel_id` | String | API | Unique YouTube Channel ID (starts with UC) |
| `title` | String | API | Channel Display Name |
| `published_at` | DateTime | API | Account Creation Timestamp |
| `video_count` | Int | API | Total uploaded videos |
| `scraped_at` | DateTime | System | Timestamp of collection |
| `stream_type` | String | System | 'cohort', 'visible', or 'deep_random' |
| `intent_signal` | Boolean | Derived | True if Intent Keywords present in metadata |

---

## FILE LOCATIONS

### Code
- **Cohorts:** `src/discover_cohort.py`
- **Visible:** `src/discover_visible.py`
- **Deep Random:** `src/discover_deep_random.py`
- **Utils:** `src/youtube_api.py`

### Data
- **Raw (Daily):** `data/raw/{YYYY}/{MM}/`
- **Processed (Monthly):** `data/processed/cohort_master.csv` (Appended)

---

## QUOTA MATH (Est. Daily)

| Action | Cost/Unit | Volume | Total Cost |
|--------|-----------|--------|------------|
| Search (Stream A) | 100 | 4,000 pgs | 400,000 |
| Channel Check (A) | 1 | 200,000 ch | 200,000 |
| Search (Stream B) | 100 | 500 pgs | 50,000 |
| Channel Check (B) | 1 | 25,000 ch | 25,000 |
| Search (Stream C) | 100 | 2,000 pgs | 200,000 |
| **TOTAL** | | | **~875,000** |

*Note: Leaves ~125k buffer (12.5%).*
