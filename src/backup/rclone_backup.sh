#!/bin/bash
# rclone_backup.sh — nightly verified backup of panel data to Google Drive.
#
# Copies (never deletes: `rclone copy`, not `sync`) these trees to
# gdrive:YT-LONGITUDINAL-BACKUP, skipping files already uploaded and unchanged:
#   data/daily_panels   (daily — the irreplaceable point-in-time snapshots)
#   data/channels       (daily — cheap, mostly static)
#   data/raw            (daily — cheap, static originals)
#   data/video_inventory (Sundays only — multi-GB files, ~15h at this uplink)
# Every copied tree is then checksum-verified with `rclone check --one-way`.
# Any failure writes data/logs/backup_FAILED_<date>.flag, which
# check_daily_health.py surfaces the next morning.
#
# Scheduled by com.youtube-longitudinal.rclone-backup at 23:30 local
# (after the day's last video-stats chunk finishes ~22:00).

set -u
REPO="/Users/katieapker/.youtube-longitudinal/repo"
RCLONE="/Users/katieapker/.local/bin/rclone"
REMOTE="gdrive:YT-LONGITUDINAL-BACKUP"
LOG="$REPO/data/logs/rclone_backup_$(date +%Y%m%d).log"
FLAG="$REPO/data/logs/backup_FAILED_$(date +%Y-%m-%d).flag"
cd "$REPO" || exit 1

# If the initial backfill (or a previous night's run) is still uploading,
# don't start a second copy of the same tree.
if pgrep -f "rclone copy" > /dev/null; then
    echo "$(date): another rclone copy is running (backfill?); skipping this run" >> "$LOG"
    exit 0
fi

fail=0
for d in daily_panels channels raw; do
    "$RCLONE" copy "data/$d" "$REMOTE/$d" --transfers 2 --log-level INFO --log-file "$LOG" || fail=1
    "$RCLONE" check "data/$d" "$REMOTE/$d" --one-way --log-level NOTICE --log-file "$LOG" || fail=1
done

# Weekly (Sunday) upload of the big video inventories
if [ "$(date +%u)" = "7" ]; then
    "$RCLONE" copy data/video_inventory "$REMOTE/video_inventory" --transfers 1 --log-level INFO --log-file "$LOG" || fail=1
    "$RCLONE" check data/video_inventory "$REMOTE/video_inventory" --one-way --log-level NOTICE --log-file "$LOG" || fail=1
fi

if [ "$fail" -ne 0 ]; then
    echo "Backup failed at $(date -u +%Y-%m-%dT%H:%M:%S) — see $LOG" > "$FLAG"
    echo "$(date): BACKUP FAILED — flag written" >> "$LOG"
    exit 1
fi
echo "$(date): backup + checksum verify OK" >> "$LOG"
