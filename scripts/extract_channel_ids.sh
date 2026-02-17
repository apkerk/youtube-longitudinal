#!/usr/bin/env bash

# extract_channel_ids.sh
# Extracts channel_id column from discovery output CSV and writes clean channel list
# Usage: ./scripts/extract_channel_ids.sh INPUT_CSV OUTPUT_CSV

set -euo pipefail

# Usage message
usage() {
    echo "Usage: $0 INPUT_CSV OUTPUT_CSV"
    echo ""
    echo "Extracts channel_id column from discovery output CSV."
    echo "Deduplicates and sorts IDs, writes output suitable for daily_stats.py --channel-list"
    echo ""
    echo "Example:"
    echo "  $0 data/channels/stream_b/initial_20260217.csv data/channels/stream_b/channel_ids.csv"
    exit 1
}

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Error: Expected 2 arguments, got $#"
    usage
fi

INPUT_CSV="$1"
OUTPUT_CSV="$2"

# Check input file exists
if [ ! -f "$INPUT_CSV" ]; then
    echo "Error: Input file not found: $INPUT_CSV"
    exit 1
fi

# Check if input file is readable
if [ ! -r "$INPUT_CSV" ]; then
    echo "Error: Input file not readable: $INPUT_CSV"
    exit 1
fi

# Create output directory if it doesn't exist
OUTPUT_DIR=$(dirname "$OUTPUT_CSV")
mkdir -p "$OUTPUT_DIR"

echo "Extracting channel IDs from: $INPUT_CSV"

# Find the column index for channel_id
COLUMN_INDEX=$(head -n 1 "$INPUT_CSV" | awk -F',' '{
    for (i=1; i<=NF; i++) {
        if ($i == "channel_id") {
            print i
            exit
        }
    }
}')

# Check if channel_id column was found
if [ -z "$COLUMN_INDEX" ]; then
    echo "Error: 'channel_id' column not found in CSV header"
    echo "Available columns:"
    head -n 1 "$INPUT_CSV"
    exit 1
fi

echo "Found channel_id in column $COLUMN_INDEX"

# Extract channel IDs, deduplicate, and sort
# Skip header row, extract column, remove empty lines, sort uniquely
tail -n +2 "$INPUT_CSV" | \
    awk -F',' -v col="$COLUMN_INDEX" '{print $col}' | \
    grep -v '^$' | \
    sort -u > /tmp/channel_ids_tmp.txt

# Count extracted IDs
COUNT=$(wc -l < /tmp/channel_ids_tmp.txt | tr -d ' ')

# Write output with header
echo "channel_id" > "$OUTPUT_CSV"
cat /tmp/channel_ids_tmp.txt >> "$OUTPUT_CSV"

# Clean up temp file
rm -f /tmp/channel_ids_tmp.txt

echo "Extracted $COUNT unique channel IDs"
echo "Output written to: $OUTPUT_CSV"
echo "Done."
