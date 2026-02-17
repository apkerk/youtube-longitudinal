# Panel Data Schema: Dual-Cadence Design

**Created:** Feb 16, 2026
**Panel:** 9,760 channels with coded gender and race (from Bailey's 14,169)

---

## Design Rationale

Video-level stats (12M videos) are expensive to collect (~240K API units, ~756 MB per snapshot). Channel-level stats (9,760 channels) are negligible (~195 API units, ~791 KB per snapshot). Collecting video stats daily would consume 269 GB/year; weekly brings that to 38 GB/year with no loss of analytical power for the research designs that use this data.

Channel stats run daily because subscriber and view trajectories change meaningfully day-to-day and the cost is trivial.

## Collection Schedule

| Dataset | Frequency | Schedule | API units | File size |
|---------|-----------|----------|-----------|-----------|
| Channel stats | Daily | 3 AM EST (8 AM UTC) | ~195/day | ~791 KB/day |
| Video stats | Weekly | Sunday 3 AM EST | ~240K/week | ~756 MB/week |

## File Structure

```
data/daily_panels/
├── channel_stats/
│   ├── 2026-02-16.csv    ← daily files
│   ├── 2026-02-17.csv
│   ├── 2026-02-18.csv
│   └── ...
└── video_stats/
    ├── 2026-02-16.csv    ← weekly files (gaps between dates are expected)
    ├── 2026-02-23.csv
    ├── 2026-03-02.csv
    └── ...
```

## Schemas

### Channel Stats (`channel_stats/YYYY-MM-DD.csv`)
Daily. One row per channel per day.

| Column | Type | Description |
|--------|------|-------------|
| channel_id | string | YouTube channel ID (UC...) |
| view_count | int | Lifetime views |
| subscriber_count | int | Current subscribers |
| video_count | int | Total public videos |
| scraped_at | datetime | UTC timestamp of collection |

**Expected rows:** 9,760 per file
**Join key:** `channel_id` links to `channel_metadata.csv` for gender, race, runBy

### Video Stats (`video_stats/YYYY-MM-DD.csv`)
Weekly. One row per video per collection.

| Column | Type | Description |
|--------|------|-------------|
| video_id | string | YouTube video ID (11 chars) |
| view_count | int | Lifetime views |
| like_count | int | Lifetime likes |
| comment_count | int | Lifetime comments |
| scraped_at | datetime | UTC timestamp of collection |

**Expected rows:** ~12M per file (varies as new videos are detected)
**Join key:** `video_id` links to `gender_gap_inventory.csv` for channel_id, published_at, title

### Video Inventory (`video_inventory/gender_gap_inventory.csv`)
One-time enumeration + incremental appends when new videos are detected.

| Column | Type | Description |
|--------|------|-------------|
| video_id | string | YouTube video ID |
| channel_id | string | Parent channel ID |
| published_at | datetime | Video publish date |
| title | string | Video title at time of discovery |
| scraped_at | datetime | When this video was first seen |

## Joining for Analysis

### Video-level panel (weekly)
```python
# Load one week's video stats
video_stats = pd.read_csv('data/daily_panels/video_stats/2026-02-23.csv')

# Join to inventory for channel_id
inventory = pd.read_csv('data/video_inventory/gender_gap_inventory.csv')
merged = video_stats.merge(inventory[['video_id', 'channel_id', 'published_at']],
                           on='video_id', how='left')

# Join to channel metadata for gender/race
metadata = pd.read_csv('data/channels/gender_gap/channel_metadata.csv')
merged = merged.merge(metadata, on='channel_id', how='left')
```

### Channel-level panel (daily)
```python
# Stack all daily channel stats into one panel
import glob
files = sorted(glob.glob('data/daily_panels/channel_stats/*.csv'))
panel = pd.concat([pd.read_csv(f) for f in files])

# Join to metadata
metadata = pd.read_csv('data/channels/gender_gap/channel_metadata.csv')
panel = panel.merge(metadata, on='channel_id', how='left')
```

### Cross-cadence merge (channel trajectory + video detail)
```python
# Get channel-level daily trajectories
ch_panel = ...  # as above

# Get video stats for a specific week
vid_stats = pd.read_csv('data/daily_panels/video_stats/2026-02-23.csv')

# Aggregate video stats to channel level for that week
vid_by_channel = vid_stats.merge(
    inventory[['video_id', 'channel_id']], on='video_id'
).groupby('channel_id').agg(
    total_views=('view_count', 'sum'),
    total_likes=('like_count', 'sum'),
    total_comments=('comment_count', 'sum'),
    n_videos=('video_id', 'count'),
).reset_index()

# Merge with channel panel for that date
ch_day = ch_panel[ch_panel['scraped_at'].str[:10] == '2026-02-23']
combined = ch_day.merge(vid_by_channel, on='channel_id', how='left')
```

## New Video Detection

The daily channel stats run compares today's `video_count` with yesterday's. When a channel's count increases, new video IDs are discovered and appended to the inventory. This means the inventory grows over time and weekly video stats automatically capture newly published videos.

## Panel Inclusion Criteria

Channels are included if they have **both** gender and race coded in Bailey's data (i.e., `perceivedGender` is not blank/undetermined AND `race` is not blank/undetermined). This yields 9,760 of the original 14,169 channels.

| Gender | Count |
|--------|-------|
| man | ~6,400 |
| woman | ~3,100 |
| non-binary | ~37 |

| Race | Count |
|------|-------|
| white | ~6,500 |
| black | ~1,600 |
| asian | ~800 |
| hispanic | ~120 |
