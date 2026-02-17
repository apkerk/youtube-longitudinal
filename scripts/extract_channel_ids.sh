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

# Use Python's csv module to handle quoted fields with embedded newlines/commas
python3 -c "
import csv, sys
inpath, outpath = sys.argv[1], sys.argv[2]
with open(inpath) as f:
    reader = csv.DictReader(f)
    if 'channel_id' not in reader.fieldnames:
        print('Error: channel_id column not found in CSV header')
        print('Available columns:', ', '.join(reader.fieldnames))
        sys.exit(1)
    ids = sorted(set(row['channel_id'] for row in reader if row['channel_id']))
with open(outpath, 'w') as f:
    f.write('channel_id\n')
    for cid in ids:
        f.write(cid + '\n')
print(f'Extracted {len(ids)} unique channel IDs')
print(f'Output written to: {outpath}')
" "$INPUT_CSV" "$OUTPUT_CSV"

echo "Done."
