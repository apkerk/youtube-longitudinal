"""
merge_cohort_channels.py
------------------------
Merge per-stream channel ID files into unified new_cohort channel list.

Reads channel_ids.csv from each stream directory (stream_a through stream_d),
deduplicates, and produces two output files:
  - data/channels/new_cohort/channel_ids.csv       (channel_id only, sorted)
  - data/channels/new_cohort/channel_metadata.csv   (channel_id + source_stream)

Re-runnable: picks up new streams as they complete. Missing streams are
skipped gracefully.

Usage:
    python scripts/merge_cohort_channels.py [--dry-run] [--test]
"""

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Readable labels for provenance tracking
STREAM_LABELS: Dict[str, str] = {
    "stream_a": "A",
    "stream_a_prime": "A'",
    "stream_b": "B",
    "stream_c": "C",
    "stream_d": "D",
}


def discover_stream_files() -> List[Tuple[str, str, Path]]:
    """
    Find all stream directories that have a channel_ids.csv file.

    Returns:
        List of (stream_key, stream_label, path) tuples, sorted by stream_key.
    """
    found = []
    for stream_key in sorted(config.STREAM_DIRS.keys()):
        stream_dir = config.STREAM_DIRS[stream_key]
        ids_file = stream_dir / "channel_ids.csv"
        if ids_file.exists():
            label = STREAM_LABELS.get(stream_key, stream_key)
            found.append((stream_key, label, ids_file))
            logger.info("Found: %s (%s) -> %s", stream_key, label, ids_file.name)
        else:
            logger.info("Skipped: %s (no channel_ids.csv)", stream_key)
    return found


def load_channel_ids(filepath: Path) -> List[str]:
    """
    Read channel_ids.csv and return list of channel IDs.

    Expects a CSV with 'channel_id' header.
    """
    ids = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "channel_id" not in (reader.fieldnames or []):
            logger.error("Missing 'channel_id' column in %s", filepath)
            return []
        for row in reader:
            cid = row["channel_id"].strip()
            if cid:
                ids.append(cid)
    return ids


def merge_streams(
    stream_files: List[Tuple[str, str, Path]],
) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Merge channel IDs from multiple streams, deduplicating.

    First-seen-wins: if a channel appears in multiple streams, the
    provenance label is from the first stream encountered (sorted
    alphabetically by stream_key for determinism).

    Returns:
        (sorted_unique_ids, metadata_rows)
        where metadata_rows = [{"channel_id": ..., "source_stream": ...}, ...]
    """
    seen: Set[str] = set()
    metadata: List[Dict[str, str]] = []

    for stream_key, label, filepath in stream_files:
        ids = load_channel_ids(filepath)
        new_count = 0
        for cid in ids:
            if cid not in seen:
                seen.add(cid)
                metadata.append({"channel_id": cid, "source_stream": label})
                new_count += 1
        dupes = len(ids) - new_count
        logger.info(
            "  Stream %s: %d IDs loaded, %d new, %d duplicates with prior streams",
            label, len(ids), new_count, dupes,
        )

    sorted_ids = sorted(seen)
    # Sort metadata to match
    metadata.sort(key=lambda r: r["channel_id"])

    return sorted_ids, metadata


def write_channel_ids(channel_ids: List[str], output_path: Path) -> None:
    """Write sorted channel_ids.csv."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["channel_id"])
        for cid in channel_ids:
            writer.writerow([cid])
    logger.info("Wrote %d channel IDs -> %s", len(channel_ids), output_path)


def write_metadata(
    metadata: List[Dict[str, str]], output_path: Path
) -> None:
    """Write channel_metadata.csv with provenance."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["channel_id", "source_stream"])
        writer.writeheader()
        writer.writerows(metadata)
    logger.info("Wrote %d metadata rows -> %s", len(metadata), output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge per-stream channel IDs into unified new_cohort list"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would merge without writing files",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    if args.test:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Scanning stream directories for channel_ids.csv files...")
    stream_files = discover_stream_files()

    if not stream_files:
        logger.warning("No streams found with channel_ids.csv. Nothing to merge.")
        return

    logger.info("Merging %d stream(s)...", len(stream_files))
    sorted_ids, metadata = merge_streams(stream_files)

    # Summary by stream
    stream_counts: Dict[str, int] = {}
    for row in metadata:
        label = row["source_stream"]
        stream_counts[label] = stream_counts.get(label, 0) + 1

    logger.info("Summary:")
    for label in sorted(stream_counts.keys()):
        logger.info("  Stream %s: %d channels", label, stream_counts[label])
    logger.info("  Total unique: %d channels", len(sorted_ids))

    if args.dry_run:
        logger.info("DRY RUN: no files written.")
        return

    ids_path = config.NEW_COHORT_DIR / "channel_ids.csv"
    meta_path = config.NEW_COHORT_DIR / "channel_metadata.csv"

    write_channel_ids(sorted_ids, ids_path)
    write_metadata(metadata, meta_path)

    logger.info("Done. Output in %s", config.NEW_COHORT_DIR)


if __name__ == "__main__":
    main()
