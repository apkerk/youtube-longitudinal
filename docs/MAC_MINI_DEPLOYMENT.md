# Mac Mini Deployment: YouTube Longitudinal Panel Collection

**Created:** Feb 16, 2026
**Purpose:** Complete handoff for deploying the daily/weekly panel collection on Katie's Mac Mini.

---

## Context: What Was Done This Session

This session made three scope changes and built the infrastructure for production:

### Scope Changes (Katie-approved)
1. **Panel filtered to coded channels only:** 9,760 channels with both gender AND race coded (was 14,169). Channels with blank or "undetermined" gender/race excluded. Saves ~35% on storage and quota.
2. **Video stats moved to weekly:** Video-level stats (12M videos, 756 MB/snapshot) collect weekly instead of daily. Channel stats remain daily (negligible cost). Saves 86% on storage (40 GB/year instead of 416 GB).
3. **Automation on Mac Mini:** launchd jobs run on the Mac Mini, not the laptop, because the Mac Mini is always on.

### Infrastructure Built
- **`daily_stats.py` updated** with `--mode` flag: `channel` (daily), `video` (weekly), `both` (manual)
- **`channel_ids.csv` regenerated** to 9,760 coded channels (was 14,169)
- **`channel_metadata.csv` regenerated** with matching 9,760 rows
- **`docs/PANEL_SCHEMA.md` written** — full dual-cadence schema documentation with join examples
- **Two launchd plists created** (on laptop, need to be recreated for Mac Mini local paths):
  - `com.youtube-longitudinal.daily-channel-stats.plist` — daily 8:00 UTC (3 AM EST)
  - `com.youtube-longitudinal.weekly-video-stats.plist` — Sunday 8:00 UTC (3 AM EST)
- **Video enumeration running** on the laptop (9,760 channels, ~12M videos expected, checkpoint/resume enabled). As of session end: ~80/9760 channels done. The background process will continue. If interrupted, resume with the same command — checkpoint handles it.

### What's Still Running
The enumeration command is running in the background on Katie's laptop:
```bash
cd "/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL"
python3 -m src.collection.enumerate_videos --channel-list data/channels/gender_gap/channel_ids.csv
```
It has checkpoint/resume. If it gets interrupted (laptop sleep, etc.), just re-run the same command and it picks up where it left off. Output: `data/video_inventory/gender_gap_inventory.csv`.

---

## Critical Constraint: Google Drive + launchd = EDEADLK

**From Katie's Mac Mini setup logs (SECOND_BRAIN/05-reference/MAC_MINI_SETUP.md):**

Google Drive streaming mode uses FUSE. When launchd processes write files to the Drive mount, they hit EDEADLK (resource deadlock) errors. This is unsolvable with permissions — it's a FUSE + launchd process tree interaction.

**The proven pattern (from Pat bot/dashboard):** LOCAL-FIRST I/O.
- Source code and data live in a LOCAL directory on the Mac Mini
- launchd services read/write to local paths only
- A separate sync job copies results to Google Drive using `osascript` (which runs in GUI context, bypassing the FUSE deadlock)

This project must follow the same pattern.

---

## Deployment Plan: Step by Step

### Mac Mini Details
- **Username:** `katieapker`
- **SSH:** `ssh katieapker@192.168.86.48` (ethernet)
- **System Python:** `/usr/bin/python3` (3.9.6 — use this, NOT Homebrew)
- **Existing launchd services:** 9 (Pat bot, dashboard, heartbeat, inbox sync, etc.)
- **Local service directory pattern:** `~/.pat-system/` (follow this convention)

### Step 1: Create Local Project Directory

```bash
ssh katieapker@192.168.86.48

# Create local working directory (follows the ~/.pat-system/ convention)
mkdir -p ~/.youtube-longitudinal

# Clone the repo
cd ~/.youtube-longitudinal
git clone https://github.com/apkerk/youtube-longitudinal.git repo
cd repo
```

### Step 2: Install Python Dependencies

```bash
# Use system python3, need --break-system-packages on macOS
/usr/bin/python3 -m pip install --break-system-packages \
    openpyxl pyyaml pandas tqdm isodate google-api-python-client
```

**Verify:**
```bash
/usr/bin/python3 -c "import openpyxl, yaml, pandas, tqdm, isodate; print('All deps OK')"
```

### Step 3: Copy Config (API Key)

The API key lives in `config/config.yaml` which is gitignored. Copy it from Drive:

```bash
mkdir -p ~/.youtube-longitudinal/repo/config
cp "/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL/config/config.yaml" \
   ~/.youtube-longitudinal/repo/config/config.yaml
```

### Step 4: Copy Data Files

The data/ directory is gitignored. Copy the essential files from Drive:

```bash
# Create data directories
cd ~/.youtube-longitudinal/repo
/usr/bin/python3 -c "from src import config; config.ensure_directories()"

# Copy channel lists
cp "/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL/data/channels/gender_gap/channel_ids.csv" \
   data/channels/gender_gap/channel_ids.csv
cp "/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL/data/channels/gender_gap/channel_metadata.csv" \
   data/channels/gender_gap/channel_metadata.csv

# Copy video inventory (AFTER enumeration completes on laptop)
cp "/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL/data/video_inventory/gender_gap_inventory.csv" \
   data/video_inventory/gender_gap_inventory.csv
```

**IMPORTANT:** The video inventory must be complete before the weekly video stats job can run. The enumeration is still running on the laptop. Check completion:
```bash
# On laptop, check if enumeration is done:
wc -l "/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL/data/video_inventory/gender_gap_inventory.csv"
# Expected: ~12,000,000 rows (plus header)

# Check checkpoint:
python3 -c "
import json
with open('/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL/data/video_inventory/.enumerate_checkpoint.json') as f:
    cp = json.load(f)
print(f'{len(cp[\"completed_channels\"])} / 9760 channels done')
"
```

If the enumeration was interrupted, resume on the Mac Mini:
```bash
cd ~/.youtube-longitudinal/repo
/usr/bin/python3 -m src.collection.enumerate_videos \
    --channel-list data/channels/gender_gap/channel_ids.csv
```

### Step 5: Test Both Collection Modes

```bash
cd ~/.youtube-longitudinal/repo

# Test channel stats (should take ~30 seconds)
/usr/bin/python3 -m src.panels.daily_stats \
    --video-inventory data/video_inventory/gender_gap_inventory.csv \
    --mode channel --test

# Verify output
ls -la data/daily_panels/channel_stats/
head -3 data/daily_panels/channel_stats/*.csv

# Test video stats (should take ~30 seconds with default 250-video limit)
/usr/bin/python3 -m src.panels.daily_stats \
    --video-inventory data/video_inventory/gender_gap_inventory.csv \
    --mode video --test

# Verify output
ls -la data/daily_panels/video_stats/
head -3 data/daily_panels/video_stats/*.csv
```

### Step 6: Create launchd Plists (Local Paths)

**Daily channel stats** — `~/Library/LaunchAgents/com.youtube-longitudinal.daily-channel-stats.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.youtube-longitudinal.daily-channel-stats</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>src.panels.daily_stats</string>
        <string>--video-inventory</string>
        <string>data/video_inventory/gender_gap_inventory.csv</string>
        <string>--mode</string>
        <string>channel</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/katieapker/.youtube-longitudinal/repo</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/katieapker/.youtube-longitudinal/repo/data/logs/daily_channel_stats_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/katieapker/.youtube-longitudinal/repo/data/logs/daily_channel_stats_stderr.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

**Weekly video stats** — `~/Library/LaunchAgents/com.youtube-longitudinal.weekly-video-stats.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.youtube-longitudinal.weekly-video-stats</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>src.panels.daily_stats</string>
        <string>--video-inventory</string>
        <string>data/video_inventory/gender_gap_inventory.csv</string>
        <string>--mode</string>
        <string>video</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/katieapker/.youtube-longitudinal/repo</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/katieapker/.youtube-longitudinal/repo/data/logs/weekly_video_stats_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/katieapker/.youtube-longitudinal/repo/data/logs/weekly_video_stats_stderr.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

Load them:
```bash
launchctl load ~/Library/LaunchAgents/com.youtube-longitudinal.daily-channel-stats.plist
launchctl load ~/Library/LaunchAgents/com.youtube-longitudinal.weekly-video-stats.plist
launchctl list | grep youtube
```

### Step 7: Create Sync-to-Drive Script

Create `~/.youtube-longitudinal/sync-to-drive.sh` to copy panel data from local to Google Drive. Uses `rsync` (not direct write from launchd, avoiding EDEADLK):

```bash
#!/bin/bash
# sync-to-drive.sh — Copy panel data from local Mac Mini to Google Drive
# Runs via launchd every 6 hours (or after each collection completes)

LOCAL_DATA="/Users/katieapker/.youtube-longitudinal/repo/data"
DRIVE_DATA="/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL/data"

# Sync daily panel files
rsync -av "$LOCAL_DATA/daily_panels/" "$DRIVE_DATA/daily_panels/"

# Sync video inventory (in case new videos were detected)
rsync -av "$LOCAL_DATA/video_inventory/" "$DRIVE_DATA/video_inventory/"

# Sync logs
rsync -av "$LOCAL_DATA/logs/" "$DRIVE_DATA/logs/"

echo "$(date): Sync complete" >> /Users/katieapker/.youtube-longitudinal/sync.log
```

**IMPORTANT NOTE ON SYNC:** The EDEADLK issue is specifically about launchd processes writing to Drive. `rsync` run from a SEPARATE launchd job might also hit this. If it does, the fallback is the same `osascript` trick used by Pat's inbox sync:

```bash
# Alternative sync using osascript (bypasses FUSE deadlock)
osascript -e 'do shell script "rsync -av /Users/katieapker/.youtube-longitudinal/repo/data/daily_panels/ \"/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL/data/daily_panels/\""'
```

If rsync-via-launchd works fine (it might, since it's a separate process), use it directly. If it deadlocks, wrap in osascript.

**Sync launchd plist** — `~/Library/LaunchAgents/com.youtube-longitudinal.sync-to-drive.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.youtube-longitudinal.sync-to-drive</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/katieapker/.youtube-longitudinal/sync-to-drive.sh</string>
    </array>

    <key>StartInterval</key>
    <integer>21600</integer>

    <key>StandardOutPath</key>
    <string>/Users/katieapker/.youtube-longitudinal/sync-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/katieapker/.youtube-longitudinal/sync-stderr.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

### Step 8: Run First Full Collection (Manual)

After everything is set up, run the first real collection manually to verify:

```bash
cd ~/.youtube-longitudinal/repo

# Full channel stats (production, not test)
/usr/bin/python3 -m src.panels.daily_stats \
    --video-inventory data/video_inventory/gender_gap_inventory.csv \
    --mode channel

# Verify: should have 9,760 rows
wc -l data/daily_panels/channel_stats/*.csv

# Full video stats (production — this will take ~1 hour for 12M videos)
/usr/bin/python3 -m src.panels.daily_stats \
    --video-inventory data/video_inventory/gender_gap_inventory.csv \
    --mode video

# Verify: should have ~12M rows
wc -l data/daily_panels/video_stats/*.csv
```

### Step 9: Verify Automation Next Day

```bash
# Check if daily channel stats ran at 3 AM
ssh katieapker@192.168.86.48 'ls -la ~/.youtube-longitudinal/repo/data/daily_panels/channel_stats/'
ssh katieapker@192.168.86.48 'tail -20 ~/.youtube-longitudinal/repo/data/logs/daily_channel_stats_stdout.log'

# Check for errors
ssh katieapker@192.168.86.48 'tail -20 ~/.youtube-longitudinal/repo/data/logs/daily_channel_stats_stderr.log'

# Check launchd status
ssh katieapker@192.168.86.48 'launchctl list | grep youtube'
```

---

## Keeping Code Updated

The Mac Mini runs from a local git clone. When code changes are pushed from the laptop:

```bash
ssh katieapker@192.168.86.48 'cd ~/.youtube-longitudinal/repo && git pull'
```

The data/ directory is gitignored, so `git pull` only updates code, never overwrites data.

---

## Expected Resource Usage

| Resource | Daily | Weekly | Monthly | Annual |
|----------|-------|--------|---------|--------|
| Channel stats API | 195 units | 1,365 | ~6K | ~71K |
| Video stats API | — | 240K | ~1M | ~12.5M |
| Channel stats storage | 791 KB | 5.5 MB | 23 MB | 282 MB |
| Video stats storage | — | 756 MB | 3.2 GB | 38 GB |
| **Total quota/day avg** | | | | **~35K/day** |
| **Total storage at 1 year** | | | | **~40 GB** |

Daily quota average is ~3.5% of the 1,010,000 unit daily limit. Leaves 96.5% for AI Census, new creator cohort, and ad hoc analysis.

---

## Troubleshooting

**Enumeration incomplete:** If the video inventory doesn't have all channels, re-run:
```bash
/usr/bin/python3 -m src.collection.enumerate_videos \
    --channel-list data/channels/gender_gap/channel_ids.csv
```
Checkpoint/resume handles it automatically.

**launchd job didn't fire:** Check with `launchctl list | grep youtube`. If status shows `-1`, check stderr log. Common issue: Python import errors from missing deps.

**EDEADLK on sync:** Switch from direct rsync to the osascript wrapper (see Step 7 notes).

**Quota exceeded:** Check `data/logs/quota_YYYYMMDD.csv`. The video stats run uses ~240K units. If another process consumed quota first, the run will fail partway through but checkpoint/resume will pick up next time.

**Config.yaml missing:** The API key must be at `~/.youtube-longitudinal/repo/config/config.yaml`. Copy from Drive (see Step 3).
