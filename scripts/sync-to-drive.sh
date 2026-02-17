#!/bin/bash
# sync-to-drive.sh
# Copy panel data from local Mac Mini to Google Drive.
# Runs via launchd every 6 hours.
#
# Deploy: cp scripts/sync-to-drive.sh ~/.youtube-longitudinal/sync-to-drive.sh
#
# If rsync-via-launchd hits EDEADLK, wrap each rsync in:
#   osascript -e 'do shell script "rsync ..."'
# See docs/MAC_MINI_DEPLOYMENT.md for details.

set -euo pipefail

LOCAL_DATA="/Users/katieapker/.youtube-longitudinal/repo/data"
DRIVE_DATA="/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL/data"

# Sync daily panel files (includes gender_gap + new_cohort subdirs)
rsync -av "$LOCAL_DATA/daily_panels/" "$DRIVE_DATA/daily_panels/"

# Sync video inventory
rsync -av "$LOCAL_DATA/video_inventory/" "$DRIVE_DATA/video_inventory/"

# Sync merged cohort channel list
rsync -av "$LOCAL_DATA/channels/new_cohort/" "$DRIVE_DATA/channels/new_cohort/"

# Sync logs
rsync -av "$LOCAL_DATA/logs/" "$DRIVE_DATA/logs/"

echo "$(date): Sync complete" >> /Users/katieapker/.youtube-longitudinal/sync.log
