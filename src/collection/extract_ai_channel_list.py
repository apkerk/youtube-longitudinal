"""
extract_ai_channel_list.py
--------------------------
Extract clean channel_ids.csv and channel_metadata.csv from an AI census
output file. These feed into daily_stats.py for panel tracking.

Usage:
    python -m src.collection.extract_ai_channel_list \
        --input data/channels/ai_census/initial_20260216.csv
"""

import argparse
import csv
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

METADATA_FIELDS = [
    "channel_id",
    "title",
    "subscriber_count",
    "view_count",
    "video_count",
    "country",
    "topic_1",
    "topic_2",
    "published_at",
    "discovery_keyword",
]


def extract(input_path: Path, output_dir: Path) -> None:
    """
    Read the census CSV, deduplicate by channel_id, and write two files:
      - channel_ids.csv (just channel_id column, for daily_stats.py)
      - channel_metadata.csv (key fields for merges and descriptive work)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    ids_path = output_dir / "channel_ids.csv"
    meta_path = output_dir / "channel_metadata.csv"

    seen = set()
    rows = []

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get('channel_id', '').strip()
            if cid and cid not in seen:
                seen.add(cid)
                rows.append(row)

    # channel_ids.csv
    with open(ids_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["channel_id"])
        for row in rows:
            writer.writerow([row['channel_id']])

    # channel_metadata.csv
    with open(meta_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=METADATA_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in METADATA_FIELDS})

    logger.info(f"Extracted {len(rows)} unique channels")
    logger.info(f"  channel_ids.csv  -> {ids_path}")
    logger.info(f"  channel_metadata.csv -> {meta_path}")


def main():
    parser = argparse.ArgumentParser(description="Extract channel lists from AI census output")
    parser.add_argument('--input', type=str, required=True,
                        help='Path to census output CSV (e.g., data/channels/ai_census/initial_20260216.csv)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: same as input file)')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = config.PROJECT_ROOT / input_path

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else input_path.parent
    if not output_dir.is_absolute():
        output_dir = config.PROJECT_ROOT / output_dir

    extract(input_path, output_dir)


if __name__ == "__main__":
    main()
