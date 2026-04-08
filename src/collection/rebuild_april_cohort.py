"""
rebuild_april_cohort.py
-----------------------
Rebuilds the combined April cohort channel_ids.csv from April Intent
and April Non-Intent discovery CSVs.

Run after each daily discovery to update the channel list that
daily_stats reads. Handles NUL bytes in source CSVs.

The April Non-Intent channels are cross-deduped against April Intent
(same rule as original A'/A).

Usage:
    python -m src.collection.rebuild_april_cohort

Author: Katie Apker
Created: Apr 8, 2026
"""

import csv
import io
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logger = logging.getLogger(__name__)

APRIL_INTENT_DIR = config.CHANNELS_DIR / "april_intent"
APRIL_NON_INTENT_DIR = config.CHANNELS_DIR / "april_non_intent"
APRIL_COHORT_DIR = config.CHANNELS_DIR / "april_cohort"
OUTPUT_IDS = APRIL_COHORT_DIR / "channel_ids.csv"


def nul_safe_reader(filepath):
    """Yield dicts from a CSV that may contain NUL bytes."""
    raw = filepath.read_bytes()
    cleaned = raw.replace(b"\x00", b"").decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(cleaned))
    for row in reader:
        yield row


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    APRIL_COHORT_DIR.mkdir(parents=True, exist_ok=True)

    seen = set()
    intent_count = 0
    non_intent_count = 0

    # Read April Intent first (priority in dedup)
    for csv_file in sorted(APRIL_INTENT_DIR.glob("*.csv")):
        if csv_file.name == "channel_ids.csv":
            continue
        for row in nul_safe_reader(csv_file):
            cid = row.get("channel_id", "").strip()
            if cid and cid not in seen:
                seen.add(cid)
                intent_count += 1

    # Read April Non-Intent, excluding Intent channels
    for csv_file in sorted(APRIL_NON_INTENT_DIR.glob("*.csv")):
        if csv_file.name == "channel_ids.csv":
            continue
        for row in nul_safe_reader(csv_file):
            cid = row.get("channel_id", "").strip()
            if cid and cid not in seen:
                seen.add(cid)
                non_intent_count += 1

    # Write combined channel_ids.csv
    with open(OUTPUT_IDS, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["channel_id"])
        for cid in sorted(seen):
            writer.writerow([cid])

    total = intent_count + non_intent_count
    logger.info("April cohort rebuilt: %d channels (intent=%d, non_intent=%d, overlap excluded)",
                total, intent_count, non_intent_count)


if __name__ == "__main__":
    main()
