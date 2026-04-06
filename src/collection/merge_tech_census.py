"""
merge_tech_census.py
--------------------
One-time merge of Tech Census discovery methods into canonical channel list.

Merges topicId method + keyword method + Stream C Technology filter.
Deduplicates by channel_id, applies pre-2023 and Technology topic filters.

Outputs:
  - channel_ids.csv (one column: channel_id)
  - channel_metadata.csv (full channel details for filtered set)

Usage:
    python -m src.collection.merge_tech_census [--test]
"""

import argparse
import csv
import io
import logging
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (all derived from __file__)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHANNELS_DIR = PROJECT_ROOT / "data" / "channels"
TECH_CENSUS_DIR = CHANNELS_DIR / "tech_census"
STREAM_C_DIR = CHANNELS_DIR / "stream_c"

# Source files
TOPICID_CSV = TECH_CENSUS_DIR / "topicid_20260402.csv"
KEYWORD_CSV = TECH_CENSUS_DIR / "keyword_20260403.csv"
STREAM_C_CSV = STREAM_C_DIR / "initial_20260220.csv"

# Output files
OUTPUT_IDS = TECH_CENSUS_DIR / "channel_ids.csv"
OUTPUT_META = TECH_CENSUS_DIR / "channel_metadata.csv"

# Filter constants
TECHNOLOGY_TOPIC_ID = "/m/07c1v"
CREATION_CUTOFF = "2023-01-01T00:00:00Z"  # channels must be created BEFORE this

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NUL-safe CSV reader (handles NUL bytes from concurrent writes)
# ---------------------------------------------------------------------------

def nul_safe_dictreader(filepath: Path):
    """
    Yield dicts from a CSV that may contain NUL bytes and multi-line fields.

    Reads the file in binary, strips NUL bytes, decodes to UTF-8, then wraps
    in csv.DictReader. Loads the full text as a string (necessary to handle
    multi-line quoted fields correctly) but yields rows one at a time.
    """
    raw = filepath.read_bytes()
    cleaned = raw.replace(b"\x00", b"").decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(cleaned))
    for row in reader:
        yield row


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def has_technology_topic(row: dict) -> bool:
    """Return True if the channel has the Technology topic ID."""
    topic_ids = row.get("topic_ids") or ""
    return TECHNOLOGY_TOPIC_ID in topic_ids


def created_before_cutoff(row: dict) -> bool:
    """Return True if the channel was created before 2023-01-01."""
    published = row.get("published_at") or ""
    if not published:
        return False
    # ISO 8601 strings are lexicographically comparable
    return published < CREATION_CUTOFF


# ---------------------------------------------------------------------------
# Source readers
# ---------------------------------------------------------------------------

def read_source(filepath: Path, source_label: str, require_tech_topic: bool = False):
    """
    Read a source CSV and yield (channel_id, row_dict, source_label) tuples.

    If require_tech_topic is True, only yields rows that have the Technology
    topic ID (used for Stream C filtering).
    """
    if not filepath.exists():
        logger.warning("Source file not found: %s", filepath)
        return

    logger.info("Reading %s: %s", source_label, filepath)
    count = 0
    for row in nul_safe_dictreader(filepath):
        cid = row.get("channel_id")
        if not cid:
            continue
        if require_tech_topic and not has_technology_topic(row):
            continue
        count += 1
        yield cid, row, source_label

    logger.info("  %s: %d channels read", source_label, count)


# ---------------------------------------------------------------------------
# Main merge logic
# ---------------------------------------------------------------------------

def merge_tech_census(test_mode: bool = False):
    """
    Merge all Tech Census sources, dedup, filter, and write output.
    """
    seen_ids: set = set()
    kept_rows: list = []

    # Counters for summary
    source_counts = Counter()     # total per source before dedup
    source_new = Counter()        # unique (first-seen) per source
    overlap_counts = Counter()    # duplicates per source

    # Read sources in priority order: topicId first, keyword second, Stream C third
    sources = [
        (TOPICID_CSV, "topicid", False),
        (KEYWORD_CSV, "keyword", False),
        (STREAM_C_CSV, "stream_c", True),  # require Technology topic
    ]

    for filepath, label, require_tech in sources:
        for cid, row, src in read_source(filepath, label, require_tech_topic=require_tech):
            source_counts[src] += 1
            if cid in seen_ids:
                overlap_counts[src] += 1
                continue
            seen_ids.add(cid)
            source_new[src] += 1
            kept_rows.append((cid, row, src))

    logger.info("")
    logger.info("=== Pre-filter summary ===")
    logger.info("Total rows read:  topicid=%d  keyword=%d  stream_c=%d",
                source_counts.get("topicid", 0),
                source_counts.get("keyword", 0),
                source_counts.get("stream_c", 0))
    logger.info("Unique (first-seen): topicid=%d  keyword=%d  stream_c=%d",
                source_new.get("topicid", 0),
                source_new.get("keyword", 0),
                source_new.get("stream_c", 0))
    logger.info("Duplicates skipped:  topicid=%d  keyword=%d  stream_c=%d",
                overlap_counts.get("topicid", 0),
                overlap_counts.get("keyword", 0),
                overlap_counts.get("stream_c", 0))
    logger.info("Combined unique (pre-filter): %d", len(kept_rows))

    # Apply filters: pre-2023 creation + Technology topic
    filtered = []
    filter_stats = Counter()  # reason -> count

    for cid, row, src in kept_rows:
        if not created_before_cutoff(row):
            filter_stats["created_2023_or_later"] += 1
            continue
        if not has_technology_topic(row):
            filter_stats["no_technology_topic"] += 1
            continue
        filtered.append((cid, row, src))

    logger.info("")
    logger.info("=== Filter results ===")
    for reason, count in filter_stats.most_common():
        logger.info("  Removed (%s): %d", reason, count)
    logger.info("Final channel count: %d", len(filtered))

    # Topic distribution in final set
    topic_counter = Counter()
    for _, row, _ in filtered:
        topic_ids_str = row.get("topic_ids") or ""
        for tid in topic_ids_str.split(","):
            tid = tid.strip()
            if tid:
                topic_counter[tid] += 1

    # Import topic map for readable names
    try:
        from src.config import YOUTUBE_PARENT_TOPICS as TOPIC_ID_MAP
    except ImportError:
        TOPIC_ID_MAP = {}

    logger.info("")
    logger.info("=== Topic distribution (top 20) ===")
    for tid, count in topic_counter.most_common(20):
        name = TOPIC_ID_MAP.get(tid, tid)
        pct = 100.0 * count / len(filtered) if filtered else 0
        logger.info("  %-30s  %6d  (%5.1f%%)", name, count, pct)

    # Source breakdown of final set
    final_source = Counter(src for _, _, src in filtered)
    logger.info("")
    logger.info("=== Final set by source ===")
    for src, count in final_source.most_common():
        logger.info("  %-12s  %d", src, count)

    if test_mode:
        logger.info("")
        logger.info("[TEST MODE] No files written.")
        return

    # Write output files
    TECH_CENSUS_DIR.mkdir(parents=True, exist_ok=True)

    # channel_ids.csv
    with open(OUTPUT_IDS, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["channel_id"])
        for cid, _, _ in filtered:
            writer.writerow([cid])
    logger.info("")
    logger.info("Wrote %d channel IDs to %s", len(filtered), OUTPUT_IDS)

    # channel_metadata.csv (full row data)
    if filtered:
        fieldnames = list(filtered[0][1].keys())
        with open(OUTPUT_META, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for _, row, _ in filtered:
                writer.writerow(row)
        logger.info("Wrote %d rows to %s", len(filtered), OUTPUT_META)
    else:
        logger.warning("No channels passed filters. No metadata file written.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Merge Tech Census sources into canonical channel list."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Dry run: print stats without writing output files.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.info("Tech Census Merge")
    logger.info("  topicid: %s", TOPICID_CSV)
    logger.info("  keyword: %s", KEYWORD_CSV)
    logger.info("  stream_c: %s", STREAM_C_CSV)
    logger.info("  test mode: %s", args.test)
    logger.info("")

    merge_tech_census(test_mode=args.test)

    logger.info("")
    logger.info("Done.")


if __name__ == "__main__":
    main()
