# Handoff: Deploy AI Census Daily Tracking + Video Enumeration

**Date:** Feb 17, 2026
**From:** Prior agent session (AI census scaling)
**For:** New agent session

---

## Context

The AI Creator Census just completed: **50,010 unique channels** discovered across 45 search terms, 2 sort orders, 18 months of lookback. Channel lists are extracted and ready. Two tasks remain:

1. Deploy daily channel stats tracking for AI census channels on Mac Mini
2. Start video enumeration for those 50K channels (on laptop)

## Task 1: Deploy AI Census Daily Stats on Mac Mini

### What needs to happen

Create a launchd plist for daily channel stats collection on the AI census panel, SCP the channel list to the Mac Mini, and load the service.

### Files involved

- **Channel list (source, on laptop):** `data/channels/ai_census/channel_ids.csv` (50,010 channels)
- **Existing plist to copy pattern from:** `config/launchd/com.youtube.new-cohort-daily-channel-stats.plist`
- **New plist to create:** `config/launchd/com.youtube.ai-census-daily-channel-stats.plist`

### Plist specification

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.youtube.ai-census-daily-channel-stats</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>src.panels.daily_stats</string>
        <string>--channel-list</string>
        <string>data/channels/ai_census/channel_ids.csv</string>
        <string>--mode</string>
        <string>channel</string>
        <string>--panel-name</string>
        <string>ai_census</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/katieapker/.youtube-longitudinal/repo</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/katieapker/.youtube-longitudinal/repo/data/logs/ai_census_channel_stats_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/katieapker/.youtube-longitudinal/repo/data/logs/ai_census_channel_stats_stderr.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

**Schedule:** 9:00 UTC (4:00 AM EST) — 1 hour after gender gap panel (8:00 UTC), 30 min after new cohort panel (8:30 UTC). Staggered to avoid concurrent API usage.

**Quota cost:** 50,010 channels / 50 per API call = 1,001 API calls = ~1,001 units/day. Trivial.

### Deployment steps (on Mac Mini via SSH)

```bash
# SSH into Mac Mini
ssh katieapker@192.168.86.48

# Pull latest code (includes the new scripts and expanded config)
cd /Users/katieapker/.youtube-longitudinal/repo
git pull origin main

# SCP the channel list FROM LAPTOP (run this on laptop, not Mac Mini):
# scp "data/channels/ai_census/channel_ids.csv" katieapker@192.168.86.48:/Users/katieapker/.youtube-longitudinal/repo/data/channels/ai_census/

# On Mac Mini: verify the file arrived
wc -l data/channels/ai_census/channel_ids.csv
# Should show 50011 (50010 channels + 1 header)

# Test the collection first
python3 -m src.panels.daily_stats \
    --channel-list data/channels/ai_census/channel_ids.csv \
    --mode channel \
    --panel-name ai_census \
    --test

# Verify test output
ls -la data/daily_panels/channel_stats/ai_census/

# Copy plist and load
cp config/launchd/com.youtube.ai-census-daily-channel-stats.plist \
   ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.youtube.ai-census-daily-channel-stats.plist

# Verify loaded
launchctl list | grep ai-census
```

### Critical constraint: EDEADLK

All launchd services must use LOCAL paths (`/Users/katieapker/.youtube-longitudinal/repo/`), never Google Drive FUSE paths. The existing sync-to-drive service handles copying results to Drive every 6 hours.

### Verification

After the service runs (or after manual test):
- Check `data/daily_panels/channel_stats/ai_census/YYYY-MM-DD.csv` exists
- Verify row count (~50K rows)
- Check logs: `tail data/logs/ai_census_channel_stats_stderr.log`

---

## Task 2: Start Video Enumeration for AI Census Channels

### What needs to happen

Run `enumerate_videos.py` on the 50K AI census channels to build a video inventory. This is a one-time operation that lists all video IDs for every channel. Runs on the laptop (not Mac Mini — it's a one-time heavy job).

### Command

```bash
python3 -m src.collection.enumerate_videos \
    --channel-list data/channels/ai_census/channel_ids.csv \
    --output data/video_inventory/ai_census_inventory.csv
```

### Expected cost and duration

- 50K channels x avg ~183 videos x (1 API unit per 50 videos) = ~183K units
- Runtime: several hours (checkpoint/resume handles interruptions)
- The script supports checkpoint/resume natively — safe to interrupt and restart

### After enumeration completes

1. Verify output: `wc -l data/video_inventory/ai_census_inventory.csv`
2. Run AI flagger on the inventory:
   ```bash
   python3 -m src.analysis.flag_ai_videos \
       --input data/video_inventory/ai_census_inventory.csv \
       --output data/processed/ai_census_ai_flagged.csv
   ```
3. SCP the inventory to Mac Mini for weekly video stats (future)

---

## File Inventory

| File | Status | Location |
|------|--------|----------|
| `data/channels/ai_census/initial_20260217.csv` | DONE | Laptop (50,010 channels) |
| `data/channels/ai_census/channel_ids.csv` | DONE | Laptop (extracted, needs SCP to Mac Mini) |
| `data/channels/ai_census/channel_metadata.csv` | DONE | Laptop (for merges) |
| `config/launchd/com.youtube.ai-census-daily-channel-stats.plist` | TO CREATE | In repo |
| `data/video_inventory/ai_census_inventory.csv` | TO CREATE | Laptop (from enumeration) |
| `data/processed/ai_census_ai_flagged.csv` | TO CREATE | Laptop (from flagger) |

## Approval Status

- Katie approved the full plan including production runs (this session)
- Daily channel stats for AI census: pre-approved (trivial quota cost, ~1K units/day)
- Video enumeration: pre-approved (~183K units, one-time)
- No additional approval needed for these two tasks
