#!/bin/bash
# auto_parallel_enum.sh
# Self-contained script: prepare shards, launch, wait, merge.
# Designed to run unattended via at/launchd after the single-threaded
# enumeration finishes its max-runtime window.

set -euo pipefail

REPO="/Users/katieapker/.youtube-longitudinal/repo"
CHANNEL_LIST="data/channels/gender_gap/channel_ids.csv"
OUTPUT="data/video_inventory/gender_gap_inventory.csv"
SHARDS=10
LOG="$REPO/data/logs/parallel_enum_$(date +%Y%m%d_%H%M).log"

cd "$REPO"

exec > >(tee -a "$LOG") 2>&1

echo "=========================================="
echo "PARALLEL ENUMERATION — $(date)"
echo "=========================================="

# Step 0: Make sure the single-threaded enumeration isn't still running
ENUM_PIDS=$(pgrep -f "enumerate_videos.*gender_gap" || true)
if [ -n "$ENUM_PIDS" ]; then
    echo "WARNING: enumerate_videos still running (PIDs: $ENUM_PIDS)"
    echo "Waiting up to 30 minutes for it to finish..."
    for i in $(seq 1 60); do
        sleep 30
        ENUM_PIDS=$(pgrep -f "enumerate_videos.*gender_gap" || true)
        if [ -z "$ENUM_PIDS" ]; then
            echo "Single-threaded enumeration finished. Proceeding."
            break
        fi
        echo "  Still running (attempt $i/60)..."
    done
    # If still running after 30 min, bail
    ENUM_PIDS=$(pgrep -f "enumerate_videos.*gender_gap" || true)
    if [ -n "$ENUM_PIDS" ]; then
        echo "ERROR: enumeration still running after 30 min wait. Aborting."
        exit 1
    fi
fi

# Step 1: Git pull to get latest code
echo ""
echo "--- Step 1: git pull ---"
git pull origin main

# Step 2: Prepare shards
echo ""
echo "--- Step 2: Prepare shards ---"
python3 -m src.collection.parallel_enumerate --prepare \
    --channel-list "$CHANNEL_LIST" \
    --output "$OUTPUT" \
    --shards "$SHARDS"

# Step 3: Launch shards
echo ""
echo "--- Step 3: Launch $SHARDS parallel shards ---"
python3 -m src.collection.parallel_enumerate --launch \
    --output "$OUTPUT" \
    --shards "$SHARDS"

# Step 4: Wait for all shards to complete
echo ""
echo "--- Step 4: Monitoring shard completion ---"
MAX_WAIT=7200  # 2 hours max
INTERVAL=120    # check every 2 minutes
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))

    echo ""
    echo "--- Status check at $(date) ($ELAPSED s elapsed) ---"
    python3 -m src.collection.parallel_enumerate --status \
        --output "$OUTPUT" \
        --shards "$SHARDS" 2>&1

    # Check if all shards are done (no screen sessions named enum_shard_*)
    RUNNING=$(screen -ls 2>/dev/null | grep "enum_shard_" | wc -l || true)
    if [ "$RUNNING" -eq 0 ]; then
        echo "All shard screen sessions have exited."
        break
    fi
    echo "$RUNNING shard(s) still running..."
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "WARNING: Timed out after $MAX_WAIT seconds. Some shards may not have finished."
    echo "Run --status and --merge manually when ready."
    exit 1
fi

# Step 5: Merge
echo ""
echo "--- Step 5: Merging shards into master inventory ---"
python3 -m src.collection.parallel_enumerate --merge \
    --output "$OUTPUT" \
    --shards "$SHARDS"

echo ""
echo "=========================================="
echo "PARALLEL ENUMERATION COMPLETE — $(date)"
echo "=========================================="

# Count final inventory
python3 -c "
import csv, io
with open('$OUTPUT', 'rb') as f:
    raw = f.read().replace(b'\x00', b'')
text = raw.decode('utf-8', errors='replace')
reader = csv.DictReader(io.StringIO(text))
ids = set()
for row in reader:
    cid = row.get('channel_id', '').strip()
    if cid:
        ids.add(cid)
print('Final inventory: %d unique channels' % len(ids))
"
