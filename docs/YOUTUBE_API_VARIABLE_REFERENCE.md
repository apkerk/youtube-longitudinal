# YouTube API Variable Reference Guide
## Complete Variable Lists from Original & T2 Data Pulls + Recommendations for Future Longitudinal Studies

**Author:** Katie Apker  
**Date:** February 2, 2026  
**Purpose:** Document all variables collected in original (May 2025) and T2 (Jan-Feb 2026) API pulls, and provide comprehensive recommendations for building robust longitudinal YouTube datasets

---

## Table of Contents

1. [Original T1 Data Pull (May 2025) — Variables Collected](#1-original-t1-data-pull-may-2025--variables-collected)
2. [T2 Data Pull (Jan-Feb 2026) — Variables Collected](#2-t2-data-pull-jan-feb-2026--variables-collected)
3. [Recommended Comprehensive Variable List for Future Longitudinal Studies](#3-recommended-comprehensive-variable-list-for-future-longitudinal-studies)
4. [API Endpoint Reference](#4-api-endpoint-reference)
5. [Best Practices for Longitudinal Data Collection](#5-best-practices-for-longitudinal-data-collection)

---

## 1. Original T1 Data Pull (May 2025) — Variables Collected

### 1.1 Source Scripts
- **Primary script:** `PR_1_DEEPEST_Data.py` (most comprehensive version)
- **Alternative script:** `PR_4_Channel_id-->Deep_YT_API_Data.py` (earlier version)
- **Output file:** `all_channel_data.csv` (419 total variables)

### 1.2 Complete Variable List (N=419)

#### A. Original Infludata Variables (Preserved from Input CSV)
1. `channel_id` — YouTube channel identifier
2. `username` — Creator display name
3. `platformURL` — YouTube channel URL
4. `country` — Creator's country
5. `gender` — Creator gender (from Infludata)
6. `language` — Primary language
7. `followers` — Subscriber count at sampling
8. `posts` — Video count at sampling
9. `engagementRatePosts` — Engagement rate for regular posts
10. `engagementRateShorts` — Engagement rate for Shorts
11. `instagram` — Instagram presence indicator
12. `tiktok` — TikTok presence indicator
13. `lastest_posts_date` — Most recent post date
14. `lastest_posts_title` — Most recent post title
15. `handle` — YouTube handle

#### B. Channel-Level Metadata (from /channels endpoint)
16. `Retrieval Date` — Timestamp of API pull
17. `Channel URL` — Full YouTube channel URL
18. `Channel Title` — Official channel title
19. `Description` — Channel description
20. `Channel Created Date-Published At` — Channel creation timestamp
21. `API_Country` — Country from YouTube API
22. `View Count` — Total channel views (lifetime)
23. `Subscriber Count` — Current subscriber count
24. `Subscriber Count Date` — Date of subscriber count retrieval
25. `Hidden Subscriber Count` — Boolean: subscriber count hidden
26. `Video Count` — Total videos on channel
27. `Uploads Playlist ID` — Playlist ID for all uploads
28. `Privacy Status` — Channel privacy status
29. `Is Linked` — Boolean: channel linked to Google account
30. `Long Uploads Status` — Status of long upload capability
31. `Made For Kids` — Boolean: channel designated for kids
32. `Default Language` — Channel default language
33. `Custom URL` — Custom channel URL
34. `Profile Picture URL` — Channel profile image URL

#### C. Topic Categories (from topicDetails)
35. `Topic Categories` — Full list of Wikipedia topic URLs
36. `Topic 1` — Primary topic category (decoded)
37. `Topic 2` — Secondary topic category (decoded)
38. `Topic 3` — Tertiary topic category (decoded)
39. `Topic Ids` — YouTube topic IDs

#### D. Branding & Localization
40. `Content Owner` — Content owner identifier
41. `Time Linked` — Timestamp of content owner linkage
42. `Available Localizations` — List of available language localizations
43. `Localization Count` — Number of language localizations
44. `Localized Title` — Localized channel title
45. `Localized Description` — Localized channel description
46. `Channel Keywords` — Channel-level keywords
47. `Unsubscribed Trailer` — Trailer video for non-subscribers
48. `Analytics Account ID` — Google Analytics tracking ID

#### E. Channel Sections (up to 5 sections)
49-63. `Section {1-5} Type` — Section type (e.g., "recentUploads", "singlePlaylist")
64-78. `Section {1-5} Title` — Section title
79-93. `Section {1-5} Position` — Section position on channel page
94-108. `Section {1-5} Playlists` — Playlist IDs in section (if applicable)
109-123. `Section {1-5} Channels` — Channel IDs in section (if applicable)

#### F. Channel Activities (up to 5 recent activities)
124-138. `Activity {1-5} Type` — Activity type (upload, playlistItem, etc.)
139-153. `Activity {1-5} Published` — Activity timestamp
154-168. `Activity {1-5} Video ID` — Video ID (for uploads)
169-183. `Activity {1-5} Playlist ID` — Playlist ID (for playlist items)

#### G. Aggregate Engagement Metrics (Calculated)
184. `Total Views (channel lifetime)` — Lifetime channel views
185. `Newest Engagement Rate` — Engagement rate for 3 newest videos
186. `Oldest Videos Engagement Rate` — Engagement rate for 3 oldest videos
187. `Total Views (last 3 videos)` — Sum of views for 3 newest videos
188. `Total Likes (last 3 videos)` — Sum of likes for 3 newest videos
189. `Total Comments (last 3 videos)` — Sum of comments for 3 newest videos
190. `Total Views (3 popular videos)` — Sum of views for 3 most popular videos
191. `Total Likes (3 popular videos)` — Sum of likes for 3 most popular videos
192. `Total Comments (3 popular videos)` — Sum of comments for 3 most popular videos
193. `Total Views (3 sponsored videos)` — Sum of views for 3 sponsored videos
194. `Total Likes (3 sponsored videos)` — Sum of likes for 3 sponsored videos
195. `Total Comments (3 sponsored videos)` — Sum of comments for 3 sponsored videos
196. `Total Views (3 oldest videos)` — Sum of views for 3 oldest videos
197. `Total Likes (3 oldest videos)` — Sum of likes for 3 oldest videos
198. `Total Comments (3 oldest videos)` — Sum of comments for 3 oldest videos
199. `Total Views (all 12 videos)` — Sum across all sampled videos
200. `Total Likes (all 12 videos)` — Sum across all sampled videos
201. `Total Comments (all 12 videos)` — Sum across all sampled videos
202. `Average Engagement Rate (all sampled videos)` — Calculated: (likes + comments) / views × 100

#### H. Upload Patterns
203. `Most Recent Video Published Date` — Date of most recent upload
204. `Oldest Video Published Date` — Date of oldest video
205. `Oldest Video Title` — Title of oldest video
206. `Upload Frequency (30 days)` — Videos per month (30-day window)
207. `Upload Frequency (90 days)` — Videos per month (90-day window)
208. `Upload Frequency (365 days)` — Videos per month (365-day window)

#### I. Hashtag Analysis
209. `Top Hashtags` — Most frequently used hashtags with counts
210. `Unique Hashtag Count` — Number of unique hashtags used

#### J. Video-Level Data: Newest Videos 1-3 (25 variables × 3 videos = 75 variables)
For each of 3 newest videos:
- `Newest Video {1-3} Title` — Video title
- `Newest Video {1-3} Published At` — Publication timestamp
- `Newest Video {1-3} ID` — Video identifier
- `Newest Video {1-3} View Count` — View count
- `Newest Video {1-3} Like Count` — Like count
- `Newest Video {1-3} Comment Count` — Comment count
- `Newest Video {1-3} Duration` — Video duration (ISO 8601 format)
- `Newest Video {1-3} Thumbnail URL` — Thumbnail image URL
- `Newest Video {1-3} Description` — Video description
- `Newest Video {1-3} URL` — Full video URL
- `Newest Video {1-3} Tags` — Video tags (comma-separated)
- `Newest Video {1-3} Hashtags` — Hashtags from description (comma-separated)
- `Newest Video {1-3} Hashtag Count` — Number of hashtags
- `Newest Video {1-3} Caption Languages` — Caption languages available (with auto-generated vs. manual)
- `Newest Video {1-3} Caption Count` — Number of caption tracks
- `Newest Video {1-3} Category ID` — YouTube category ID
- `Newest Video {1-3} Category Name` — YouTube category name (decoded)
- `Newest Video {1-3} Definition` — Video definition (hd/sd)
- `Newest Video {1-3} Caption` — Boolean: captions available
- `Newest Video {1-3} Licensed Content` — Boolean: licensed content
- `Newest Video {1-3} Region Restriction Allowed` — Countries where video is allowed
- `Newest Video {1-3} Region Restriction Blocked` — Countries where video is blocked
- `Newest Video {1-3} Content Rating MPAA` — MPAA rating
- `Newest Video {1-3} Content Rating TV` — TV rating
- `Newest Video {1-3} Content Rating YT` — YouTube age restriction

#### K. Video-Level Data: Popular Videos 1-3 (25 variables × 3 videos = 75 variables)
Same structure as Newest Videos, with prefix `Popular Video {1-3}`

#### L. Video-Level Data: Oldest Videos 1-3 (25 variables × 3 videos = 75 variables)
Same structure as Newest Videos, with prefix `Oldest Video {1-3}`

#### M. Video-Level Data: Sponsored Videos 1-3 (25 variables × 3 videos = 75 variables)
Same structure as Newest Videos, with prefix `Sponsored Video {1-3}`

#### N. Comment Data for Each Video (12 variables × 3 comments × 12 videos = 432 potential variables, though not all present)
For each video type (Newest, Popular, Oldest, Sponsored) and each video (1-3), up to 3 comments:
- `{VideoType} Video {1-3} Comment {1-3} Text` — Comment text (truncated to 150 chars)
- `{VideoType} Video {1-3} Comment {1-3} Author` — Commenter display name
- `{VideoType} Video {1-3} Comment {1-3} Likes` — Comment like count
- `{VideoType} Video {1-3} Comment {1-3} Date` — Comment timestamp

**Total Original T1 Variables: 419** (exact count varies by channel due to optional fields)

---

## 2. T2 Data Pull (Jan-Feb 2026) — Variables Collected

### 2.1 Source Scripts
- **Viewcounts only:** `pull_T2_viewcounts.py` (January 2026)
- **Comprehensive:** `pull_T2_comprehensive.py` (February 2026)

### 2.2 T2 Channel Statistics (8 variables)

**Output file:** `T2_channel_stats_20260202.csv`

1. `channel_id` — YouTube channel identifier
2. `viewCount_T2` — Total channel views at T2
3. `subscriberCount_T2` — Subscriber count at T2
4. `videoCount_T2` — Video count at T2
5. `hiddenSubscriberCount` — Boolean: subscriber count hidden at T2
6. `uploads_playlist_id` — Uploads playlist ID
7. `status` — API call status (success, not_found, error, etc.)
8. `retrieval_date` — Timestamp of T2 retrieval

### 2.3 T2 Video Sample (13 variables)

**Output file:** `T2_video_sample_20260202.csv`  
**Sampling:** Up to 3 newest videos per channel

1. `channel_id` — YouTube channel identifier
2. `video_id` — Video identifier
3. `video_rank` — Rank (1-3, newest first)
4. `title` — Video title
5. `description` — Video description
6. `published_at` — Publication timestamp
7. `view_count` — View count at T2
8. `like_count` — Like count at T2
9. `comment_count` — Comment count at T2
10. `duration` — Video duration (ISO 8601)
11. `definition` — Video definition (hd/sd)
12. `category_id` — YouTube category ID
13. `retrieval_date` — Timestamp of T2 retrieval

**Total T2 Variables: 21 unique variables** (8 channel-level + 13 video-level)

---

## 3. Recommended Comprehensive Variable List for Future Longitudinal Studies

### 3.1 Design Philosophy

For building robust longitudinal YouTube datasets, prioritize:
1. **Core metrics that change over time** (views, subscribers, engagement)
2. **Content characteristics** (titles, descriptions, tags for text analysis)
3. **Audience signals** (comment patterns, engagement rates)
4. **Platform features** (captions, translations, monetization indicators)
5. **Temporal markers** (upload dates, activity timestamps)

### 3.2 Recommended Variable List (Organized by Priority)

#### TIER 1: Essential Core Metrics (Collect at Every Time Point)

**Channel-Level (13 variables)**
1. `channel_id` — Unique identifier
2. `retrieval_date` — Timestamp of data collection
3. `viewCount` — Total channel views
4. `subscriberCount` — Total subscribers
5. `videoCount` — Total videos
6. `hiddenSubscriberCount` — Boolean: subscriber visibility
7. `channel_title` — Channel name
8. `channel_description` — Channel description
9. `uploads_playlist_id` — Uploads playlist ID
10. `channel_created_date` — Channel creation date (static, but useful for age calculations)
11. `country` — Channel country
12. `default_language` — Default language
13. `custom_url` — Custom URL

**Video Sample: Newest 5 Videos (12 variables × 5 videos = 60 variables)**
14. `video_id` — Video identifier
15. `video_rank` — Rank (1-5, newest first)
16. `title` — Video title
17. `description` — Video description
18. `published_at` — Publication timestamp
19. `view_count` — View count
20. `like_count` — Like count
21. `comment_count` — Comment count
22. `duration` — Video duration
23. `definition` — HD/SD
24. `category_id` — YouTube category
25. `tags` — Video tags (for content analysis)

**Rationale:** These 73 variables capture the core dynamics of channel growth and content performance over time.

---

#### TIER 2: Enhanced Content & Engagement Metrics (Add for Richer Analysis)

**Channel-Level Additional (10 variables)**
26. `topic_categories` — Wikipedia topic classifications
27. `made_for_kids` — Boolean: kids content designation
28. `branding_keywords` — Channel keywords
29. `localization_count` — Number of language localizations
30. `available_localizations` — List of localization languages
31. `profile_picture_url` — Profile image URL (for image analysis)
32. `privacy_status` — Channel privacy status
33. `long_uploads_status` — Long upload capability
34. `is_linked` — Boolean: Google account linkage
35. `unsubscribed_trailer` — Trailer video ID

**Video Sample: Enhanced Fields (8 additional variables × 5 videos = 40 variables)**
36. `hashtags` — Hashtags from description
37. `hashtag_count` — Number of hashtags
38. `caption_languages` — Available caption languages
39. `caption_count` — Number of caption tracks
40. `licensed_content` — Boolean: licensed content flag
41. `region_restriction_blocked` — Blocked countries
42. `region_restriction_allowed` — Allowed countries
43. `content_rating_yt` — YouTube age restriction

**Calculated Engagement Metrics (5 variables)**
44. `engagement_rate_newest_5` — (likes + comments) / views for newest 5 videos
45. `avg_views_newest_5` — Average views for newest 5 videos
46. `avg_likes_newest_5` — Average likes for newest 5 videos
47. `avg_comments_newest_5` — Average comments for newest 5 videos
48. `upload_frequency_90d` — Videos per month (90-day window)

**Rationale:** These 55 variables add content characteristics useful for understanding what drives engagement.

---

#### TIER 3: Deep Dive — Audience & Content Patterns (Optional, for Specialized Studies)

**Video Sample: Popular Videos (12 variables × 3 videos = 36 variables)**
- Same structure as Tier 1 video variables
- Pulled via `/search?order=viewCount`
- Useful for tracking "breakout" content

**Comment Sampling (8 variables × 10 comments per channel = 80 variables)**
49. `comment_text` — Comment text
50. `comment_author` — Commenter name
51. `comment_likes` — Comment like count
52. `comment_date` — Comment timestamp
53. `comment_video_id` — Source video
54. `commenter_channel_id` — Commenter's channel ID
55. `is_reply` — Boolean: is this a reply
56. `parent_comment_id` — Parent comment ID (if reply)

**Channel Activities (4 variables × 10 activities = 40 variables)**
57. `activity_type` — Activity type (upload, playlist, etc.)
58. `activity_published` — Activity timestamp
59. `activity_video_id` — Video ID (if upload)
60. `activity_playlist_id` — Playlist ID (if playlist activity)

**Channel Sections (4 variables × 5 sections = 20 variables)**
61. `section_type` — Section type
62. `section_title` — Section title
63. `section_position` — Section position
64. `section_playlists` — Playlist IDs in section

**Rationale:** These 176 variables provide deep context for understanding audience composition and channel organization strategies.

---

### 3.3 Recommended Minimal Longitudinal Dataset

**For efficient longitudinal tracking with minimal API quota usage:**

**Collect at each time point (T1, T2, T3, ...):**
- **Channel stats:** 13 variables (Tier 1 channel-level)
- **Newest 3 videos:** 36 variables (12 × 3)
- **Calculated metrics:** 5 variables (engagement rates, upload frequency)

**Total: 54 variables per time point**

**API Quota Cost:**
- 1 unit for channel stats
- 1 unit for playlist items (get video IDs)
- ~1 unit for video details (batched, 50 videos per call)
- **Total: ~3 units per channel per time point**

For 10,000 channels: 30,000 units per wave (well within daily quota of 10,000 units if spread over 3 days)

---

### 3.4 Recommended Comprehensive Longitudinal Dataset

**For rich longitudinal analysis with moderate API usage:**

**Collect at each time point:**
- **Tier 1:** 73 variables (channel + newest 5 videos)
- **Tier 2:** 55 variables (enhanced content + engagement)
- **Comment sample:** 80 variables (10 comments per channel)

**Total: 208 variables per time point**

**API Quota Cost:**
- 1 unit for channel stats
- 1 unit for playlist items
- ~1 unit for video details (batched)
- 1 unit for comment threads
- **Total: ~4 units per channel per time point**

For 10,000 channels: 40,000 units per wave (requires 4 days with 10,000 daily quota)

---

## 4. API Endpoint Reference

### 4.1 Channels Endpoint
```
GET https://www.googleapis.com/youtube/v3/channels
```

**Useful parts:**
- `snippet` — Title, description, country, language, thumbnails
- `statistics` — Views, subscribers, video count
- `contentDetails` — Uploads playlist ID, related playlists
- `status` — Privacy status, kids designation, upload status
- `topicDetails` — Topic categories, topic IDs
- `brandingSettings` — Keywords, channel settings
- `localizations` — Available language localizations

**Quota cost:** 1 unit per call

### 4.2 Videos Endpoint
```
GET https://www.googleapis.com/youtube/v3/videos
```

**Useful parts:**
- `snippet` — Title, description, tags, category, thumbnails
- `statistics` — Views, likes, comments
- `contentDetails` — Duration, definition, captions, region restrictions

**Quota cost:** 1 unit per call (can batch up to 50 video IDs)

### 4.3 PlaylistItems Endpoint
```
GET https://www.googleapis.com/youtube/v3/playlistItems
```

**Purpose:** Get video IDs from uploads playlist

**Quota cost:** 1 unit per call

### 4.4 Search Endpoint
```
GET https://www.googleapis.com/youtube/v3/search
```

**Useful for:**
- Finding popular videos (`order=viewCount`)
- Finding recent videos (`order=date`)
- Finding sponsored videos (`videoPaidProductPlacement=true`)

**Quota cost:** 100 units per call (expensive!)

### 4.5 CommentThreads Endpoint
```
GET https://www.googleapis.com/youtube/v3/commentThreads
```

**Purpose:** Get comments for videos

**Quota cost:** 1 unit per call

### 4.6 Captions Endpoint
```
GET https://www.googleapis.com/youtube/v3/captions
```

**Purpose:** Get caption metadata (languages, auto-generated status)

**Quota cost:** 50 units per call (expensive!)

---

## 5. Best Practices for Longitudinal Data Collection

### 5.1 Timing Considerations

**Recommended collection intervals:**
- **Quarterly (every 3 months):** Good balance for tracking growth
- **Semi-annually (every 6 months):** Sufficient for slower-moving metrics
- **Annually:** Minimum for longitudinal analysis

**Avoid:**
- Monthly collection (too frequent, minimal change)
- Irregular intervals (complicates time-series analysis)

### 5.2 Data Quality Checks

**At each time point, validate:**
1. Channel still exists (`status != 'not_found'`)
2. View counts are monotonically increasing (or flag anomalies)
3. Subscriber counts are reasonable (flag sudden drops)
4. Video counts match expected upload frequency
5. No duplicate channel IDs in dataset

### 5.3 API Quota Management

**Strategies:**
1. **Use multiple API keys** and rotate on quota exhaustion
2. **Batch video requests** (50 IDs per call)
3. **Avoid expensive endpoints** (search = 100 units, captions = 50 units)
4. **Implement exponential backoff** for rate limiting
5. **Save progress incrementally** (append to CSV after each channel)

### 5.4 Variable Naming Conventions

**For longitudinal datasets:**
- Use time-point suffixes: `viewCount_T1`, `viewCount_T2`, `viewCount_T3`
- Or use date suffixes: `viewCount_2025_05`, `viewCount_2026_01`
- Keep channel identifiers consistent across waves
- Document variable definitions in data dictionary

### 5.5 Storage Recommendations

**File structure:**
```
/data/
  /T1_2025_05/
    channel_stats_T1.csv
    video_sample_T1.csv
    comments_T1.csv
  /T2_2026_01/
    channel_stats_T2.csv
    video_sample_T2.csv
    comments_T2.csv
  /merged/
    longitudinal_panel.csv
```

**Merge strategy:**
- Keep separate files for each wave
- Create merged panel dataset with one row per channel-time observation
- Use wide format (one row per channel, multiple time columns) or long format (multiple rows per channel)

---

## 6. Comparison: T1 vs. T2 Data Pulls

### 6.1 What Changed Between T1 and T2

| Dimension | T1 (May 2025) | T2 (Jan-Feb 2026) | Reason for Change |
|-----------|---------------|-------------------|-------------------|
| **Scope** | Comprehensive (419 vars) | Minimal (21 vars) | T2 focused on growth metrics only |
| **Video sample** | 12 videos (newest 3, oldest 3, popular 3, sponsored 3) | 3 videos (newest only) | T2 prioritized efficiency |
| **Comments** | Yes (3 per video, 12 videos) | No | T2 skipped to save quota |
| **Captions** | Yes (languages + auto-generated status) | No | T2 skipped to save quota |
| **Hashtags** | Yes (extracted + analyzed) | No | T2 skipped |
| **Channel sections** | Yes (5 sections) | No | T2 skipped |
| **Activities** | Yes (5 recent) | No | T2 skipped |
| **API quota cost** | ~15 units per channel | ~3 units per channel | T2 optimized for speed |

### 6.2 Lessons Learned

**From T1 (comprehensive pull):**
- ✅ Rich data for exploratory analysis
- ✅ Enabled text analysis (LIWC on titles, descriptions, comments)
- ✅ Captured content strategy (hashtags, sections, activities)
- ❌ High API quota cost (required multiple keys)
- ❌ Many variables unused in final analysis

**From T2 (minimal pull):**
- ✅ Fast and efficient
- ✅ Sufficient for growth tracking
- ✅ Low API quota cost
- ❌ Cannot analyze content changes over time
- ❌ Cannot track audience engagement patterns

**Recommendation for future studies:**
- Use **Tier 1 + Tier 2** (128 variables) as default
- Add **Tier 3** only if research questions require deep content/audience analysis
- Collect **comprehensive data at T1** (baseline), then **streamlined data at T2+** (tracking)

---

## 7. Quick Reference: Variable Counts by Category

| Category | T1 (May 2025) | T2 (Jan-Feb 2026) | Recommended Minimal | Recommended Comprehensive |
|----------|---------------|-------------------|---------------------|---------------------------|
| **Channel metadata** | 48 | 8 | 13 | 23 |
| **Video data** | 300 (12 videos × 25 vars) | 11 (3 videos × ~4 vars) | 36 (3 videos × 12 vars) | 100 (5 videos × 20 vars) |
| **Comments** | 36 (3 per video × 12 videos) | 0 | 0 | 80 (10 comments) |
| **Engagement metrics** | 19 | 0 | 5 | 5 |
| **Channel sections** | 15 | 0 | 0 | 20 |
| **Activities** | 15 | 0 | 0 | 40 |
| **Calculated fields** | 10 | 2 | 5 | 10 |
| **TOTAL** | **419** | **21** | **54** | **208** |

---

## 8. Example Use Cases by Variable Tier

### Tier 1 (Minimal) — Good for:
- Tracking channel growth over time
- Measuring cumulative advantage effects
- Analyzing upload frequency patterns
- Basic engagement rate calculations
- Content category analysis (via video titles)

### Tier 1 + Tier 2 (Recommended) — Good for:
- All of the above, plus:
- Text analysis of titles/descriptions (LIWC, sentiment, etc.)
- Hashtag strategy analysis
- Caption/localization strategy tracking
- Content rating and restriction patterns
- Regional availability analysis

### Tier 1 + Tier 2 + Tier 3 (Comprehensive) — Good for:
- All of the above, plus:
- Audience composition analysis (via comments)
- Comment sentiment and engagement quality
- Channel organization strategy (sections, playlists)
- Activity patterns (upload timing, playlist updates)
- Identifying "breakout" content (popular videos)
- Sponsored content analysis

---

## 9. Code Template for Future Data Pulls

```python
"""
YouTube API Longitudinal Data Collection Template
Recommended configuration for robust longitudinal studies
"""

import requests
import csv
from datetime import datetime
from typing import Dict, List

# Configuration
API_KEY = "YOUR_API_KEY_HERE"
API_BASE = "https://www.googleapis.com/youtube/v3"
SLEEP_BETWEEN_CALLS = 0.15  # Conservative rate limiting

# Tier 1: Essential metrics (always collect)
CHANNEL_PARTS = "snippet,statistics,contentDetails,status,topicDetails"
VIDEO_PARTS = "snippet,statistics,contentDetails"
VIDEOS_PER_CHANNEL = 5  # Newest 5 videos

# Tier 2: Enhanced metrics (recommended)
INCLUDE_HASHTAGS = True
INCLUDE_CAPTIONS = True
INCLUDE_LOCALIZATIONS = True

# Tier 3: Deep dive (optional)
INCLUDE_POPULAR_VIDEOS = False  # Expensive (100 units per call)
INCLUDE_COMMENTS = False  # Moderate cost (1 unit per call)
INCLUDE_ACTIVITIES = False
INCLUDE_SECTIONS = False

def get_channel_stats(channel_id: str) -> Dict:
    """Fetch Tier 1 + Tier 2 channel statistics."""
    url = f"{API_BASE}/channels"
    params = {
        "part": CHANNEL_PARTS,
        "id": channel_id,
        "key": API_KEY
    }
    response = requests.get(url, params=params, timeout=10)
    # ... implementation ...

def get_newest_videos(uploads_playlist_id: str, max_results: int = 5) -> List[str]:
    """Get newest video IDs from uploads playlist."""
    url = f"{API_BASE}/playlistItems"
    params = {
        "part": "contentDetails",
        "playlistId": uploads_playlist_id,
        "maxResults": max_results,
        "key": API_KEY
    }
    response = requests.get(url, params=params, timeout=10)
    # ... implementation ...

def get_video_details_batch(video_ids: List[str]) -> List[Dict]:
    """Fetch video details in batch (up to 50 IDs)."""
    url = f"{API_BASE}/videos"
    params = {
        "part": VIDEO_PARTS,
        "id": ",".join(video_ids),
        "key": API_KEY
    }
    response = requests.get(url, params=params, timeout=10)
    # ... implementation ...

# Main collection loop
for channel_id in channel_list:
    # Tier 1: Channel stats
    channel_stats = get_channel_stats(channel_id)
    
    # Tier 1: Newest videos
    video_ids = get_newest_videos(channel_stats['uploads_playlist_id'], VIDEOS_PER_CHANNEL)
    video_details = get_video_details_batch(video_ids)
    
    # Tier 2: Enhanced fields (if enabled)
    if INCLUDE_HASHTAGS:
        extract_hashtags(video_details)
    
    # Tier 3: Optional deep dive (if enabled)
    if INCLUDE_COMMENTS:
        comments = get_video_comments(video_ids[0])  # Sample from newest video
    
    # Save incrementally
    save_to_csv(channel_stats, video_details)
```

---

## 10. Final Recommendations

### For Your Next Project:

1. **Start with Tier 1 + Tier 2** (128 variables)
   - Sufficient for most longitudinal analyses
   - Moderate API quota cost (~4 units per channel)
   - Enables text analysis and content strategy tracking

2. **Collect comprehensive data at baseline (T1)**
   - Include Tier 3 variables at T1 for exploratory analysis
   - Identify which variables are most useful
   - Streamline to Tier 1 + Tier 2 for subsequent waves

3. **Plan collection schedule**
   - Quarterly or semi-annually
   - Same month each year for seasonal consistency
   - Document exact collection dates for time-series analysis

4. **Implement robust error handling**
   - Save progress incrementally
   - Log API errors and channel status
   - Validate data quality at each wave

5. **Use consistent naming conventions**
   - Suffix variables with time point: `_T1`, `_T2`, etc.
   - Keep channel IDs as primary key
   - Document variable definitions in data dictionary

6. **Budget API quota carefully**
   - 10,000 units per day per key
   - Tier 1 + Tier 2 = ~4 units per channel
   - 2,500 channels per day per key
   - Use multiple keys for large samples

---

**Document Version:** 1.0  
**Last Updated:** February 2, 2026  
**Contact:** Katie Apker (apker.katie@gmail.com)

