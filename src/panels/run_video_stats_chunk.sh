#!/bin/bash
# run_video_stats_chunk.sh
# Wrapper for daily chunked video stats collection.
# Calculates chunk_index from day of week (Mon=0 .. Sun=6) and calls daily_stats.py.
#
# Usage (called by launchd):
#   ./run_video_stats_chunk.sh <inventory_path> <panel_name> <num_chunks>
#
# Example:
#   ./run_video_stats_chunk.sh data/video_inventory/gender_gap_inventory.csv gender_gap 7

set -euo pipefail

REPO_DIR="/Users/katieapker/.youtube-longitudinal/repo"
cd "$REPO_DIR"

INVENTORY="$1"
PANEL_NAME="$2"
NUM_CHUNKS="${3:-7}"

# Day of week: Mon=0 .. Sun=6 (Python-style)
CHUNK_INDEX=$(python3 -c "from datetime import datetime; print(datetime.utcnow().weekday())")

echo "$(date): Running video stats chunk $CHUNK_INDEX/$NUM_CHUNKS for $PANEL_NAME"

/usr/bin/python3 -m src.panels.daily_stats \
    --video-inventory "$INVENTORY" \
    --mode video \
    --panel-name "$PANEL_NAME" \
    --chunk-index "$CHUNK_INDEX" \
    --num-chunks "$NUM_CHUNKS"
