"""
discover_category_quota.py
--------------------------
Category Quota Sampler -- floor-based discovery across YouTube's 15 video categories.

Replaces the broken Topic-Stratified stream (which used deprecated Freebase topicId).
Uses YouTube's native videoCategoryId parameter on search.list, which is actively
maintained and returns reliable results.

Design:
  - 15 YouTube video categories (integer IDs)
  - For each category: search with videoCategoryId + letter cycling + order=date
  - Per-category floor target: collect until each has N unique channels
  - Categories that fill fast stop early; rare categories get more cycles
  - Checkpoint per category (resume-safe for launchd)

Discovery uses videoCategoryId (works as search filter).
Analysis variable is topic_1/2/3 (channel-level topicCategories, consistent with JMP).
Both are captured: videoCategoryId during search, topic_1/2/3 when channels.list runs.

See DECISION_LOG.md entries 006 and 007 for full rationale.

Usage:
    python -m src.collection.discover_category_quota [--test] [--limit N]
        [--per-category N] [--max-runtime N] [--reserve-quota N]

Author: Katie Apker
Created: Apr 8, 2026
"""

import argparse
import csv
import json
import time
import logging
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    search_videos_paginated,
    extract_channel_ids_from_search,
    get_channel_full_details,
    QuotaExhaustedError,
    get_quota_used,
    load_config,
)
import config

logger = logging.getLogger(__name__)

# YouTube's 15 native video categories (integer IDs)
# These are set by creators on each video upload. Stable, not deprecated.
VIDEO_CATEGORIES: Dict[int, str] = {
    1: "Film & Animation",
    2: "Autos & Vehicles",
    10: "Music",
    15: "Pets & Animals",
    17: "Sports",
    19: "Travel & Events",
    20: "Gaming",
    22: "People & Blogs",
    23: "Comedy",
    24: "Entertainment",
    25: "News & Politics",
    26: "Howto & Style",
    27: "Education",
    28: "Science & Technology",
    29: "Nonprofits & Activism",
}

# Query letters for cycling (a-z + 0-9). Minimal semantic bias.
QUERY_LETTERS = list(string.ascii_lowercase) + list(string.digits)

# Output directory (reuses topic_stratified slot in STREAM_DIRS)
OUTPUT_DIR = config.STREAM_DIRS.get("topic_stratified", config.CHANNELS_DIR / "category_quota")
CHECKPOINT_PATH = OUTPUT_DIR / ".category_quota_checkpoint.json"


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'discover_category_quota_{config.get_date_stamp()}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )


def load_checkpoint() -> Dict:
    """Load checkpoint state."""
    if not CHECKPOINT_PATH.exists():
        return {}

    with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_checkpoint(state: Dict) -> None:
    """Save checkpoint state."""
    state["timestamp"] = datetime.utcnow().isoformat()
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def clear_checkpoint() -> None:
    """Remove checkpoint file after successful completion."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared")


def discover_category_quota(
    youtube,
    per_category_target: int = 5000,
    total_limit: int = 75000,
    test_mode: bool = False,
    output_path: Optional[Path] = None,
    max_runtime: Optional[int] = None,
    reserve_quota: int = 0,
    daily_quota_limit: int = 0,
) -> int:
    """
    Discover channels with floor-based category balancing.

    For each of YouTube's 15 video categories, cycles through query letters
    (a-z, 0-9) searching for recent videos. Collects until each category
    reaches per_category_target unique channels, then moves to the next.

    Args:
        youtube: Authenticated YouTube API service
        per_category_target: Floor target per category
        total_limit: Hard cap on total channels across all categories
        test_mode: If True, reduced targets for testing
        output_path: Path to write CSV output
        max_runtime: Stop after N seconds (for launchd safety)
        reserve_quota: Stop this many units before daily limit
        daily_quota_limit: Daily quota ceiling

    Returns:
        Total number of channels collected
    """
    if test_mode:
        per_category_target = min(per_category_target, 20)
        total_limit = min(total_limit, 100)
        logger.info("TEST MODE: per_category=%d, total_limit=%d",
                     per_category_target, total_limit)

    start_time = time.time()
    quota_ceiling = (daily_quota_limit - reserve_quota
                     if reserve_quota > 0 and daily_quota_limit > 0 else 0)

    # Load checkpoint
    ckpt = load_checkpoint()
    completed_categories: Set[int] = set(ckpt.get("completed_categories", []))
    # Per-category letter index: tracks where each category left off
    letter_indices: Dict[str, int] = ckpt.get("letter_indices", {})
    # Global seen channel IDs (loaded from existing CSV)
    seen_ids: Set[str] = set()
    # Per-category counts
    category_counts: Dict[int, int] = {}

    # Rebuild state from existing CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and ckpt:
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get('channel_id', '').strip()
                if not cid:
                    continue
                seen_ids.add(cid)
                # Parse discovery_keyword to extract category ID
                dk = row.get('discovery_keyword', '')
                if dk.startswith('videoCategoryId='):
                    try:
                        cat_id = int(dk.split('=')[1])
                        category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
                    except (ValueError, IndexError):
                        pass
        logger.info("Resumed: %d channels across %d categories",
                     len(seen_ids), len(category_counts))
    else:
        # Fresh start: write CSV header
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
            writer.writeheader()

    total_collected = len(seen_ids)

    logger.info("Per-category target: %d", per_category_target)
    logger.info("Total limit: %d", total_limit)
    logger.info("Categories: %d", len(VIDEO_CATEGORIES))
    logger.info("Already collected: %d channels", total_collected)

    # Show current category fill levels
    for cat_id, cat_name in sorted(VIDEO_CATEGORIES.items()):
        count = category_counts.get(cat_id, 0)
        status = "DONE" if cat_id in completed_categories else "%d/%d" % (count, per_category_target)
        logger.info("  [%2d] %-25s %s", cat_id, cat_name, status)

    all_done = True

    for cat_id, cat_name in sorted(VIDEO_CATEGORIES.items()):
        if cat_id in completed_categories:
            continue

        current_count = category_counts.get(cat_id, 0)
        if current_count >= per_category_target:
            completed_categories.add(cat_id)
            save_checkpoint({
                "completed_categories": list(completed_categories),
                "letter_indices": letter_indices,
                "total_collected": total_collected,
            })
            continue

        if total_collected >= total_limit:
            logger.info("Total limit %d reached", total_limit)
            all_done = True
            break

        if max_runtime is not None and time.time() - start_time > max_runtime:
            logger.info("Max runtime reached -- stopping. Will resume next run.")
            all_done = False
            break

        if quota_ceiling > 0 and get_quota_used() >= quota_ceiling:
            logger.info("Quota ceiling reached -- stopping. Will resume next run.")
            all_done = False
            break

        # Determine starting letter for this category
        letter_idx = letter_indices.get(str(cat_id), 0)

        logger.info("")
        logger.info("=== Category [%d] %s: %d/%d (starting at letter '%s') ===",
                     cat_id, cat_name, current_count, per_category_target,
                     QUERY_LETTERS[letter_idx] if letter_idx < len(QUERY_LETTERS) else "exhausted")

        while (current_count < per_category_target
               and letter_idx < len(QUERY_LETTERS)
               and total_collected < total_limit):

            if max_runtime is not None and time.time() - start_time > max_runtime:
                logger.info("Max runtime reached mid-category -- stopping.")
                all_done = False
                # Save letter index for resume
                letter_indices[str(cat_id)] = letter_idx
                save_checkpoint({
                    "completed_categories": list(completed_categories),
                    "letter_indices": letter_indices,
                    "total_collected": total_collected,
                })
                break

            if quota_ceiling > 0 and get_quota_used() >= quota_ceiling:
                logger.info("Quota ceiling reached mid-category -- stopping.")
                all_done = False
                letter_indices[str(cat_id)] = letter_idx
                save_checkpoint({
                    "completed_categories": list(completed_categories),
                    "letter_indices": letter_indices,
                    "total_collected": total_collected,
                })
                break

            letter = QUERY_LETTERS[letter_idx]

            try:
                search_results = search_videos_paginated(
                    youtube=youtube,
                    query=letter,
                    published_after="2026-01-01T00:00:00Z",
                    order="date",
                    max_pages=2 if test_mode else 10,
                    videoCategoryId=str(cat_id),
                )

                if not search_results:
                    logger.info("  letter '%s': no results", letter)
                    letter_idx += 1
                    continue

                channel_ids = extract_channel_ids_from_search(search_results)
                new_ids = [cid for cid in channel_ids if cid not in seen_ids]

                if not new_ids:
                    logger.info("  letter '%s': %d results, 0 new channels", letter, len(search_results))
                    letter_idx += 1
                    continue

                # Get full channel details
                channel_details = get_channel_full_details(
                    youtube=youtube,
                    channel_ids=new_ids,
                    stream_type="category_quota",
                    discovery_language="global",
                    discovery_keyword="videoCategoryId=%d" % cat_id,
                )

                batch_new = []
                for channel in channel_details:
                    cid = channel['channel_id']
                    if cid not in seen_ids:
                        seen_ids.add(cid)
                        batch_new.append(channel)
                        current_count += 1
                        total_collected += 1

                if batch_new:
                    with open(output_path, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
                        for ch in batch_new:
                            row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
                            writer.writerow(row)

                logger.info("  letter '%s': %d results, %d new (%s total, %d in category)",
                             letter, len(search_results), len(batch_new),
                             total_collected, current_count)

            except QuotaExhaustedError:
                logger.warning("Quota exhausted -- stopping. Will resume next run.")
                all_done = False
                letter_indices[str(cat_id)] = letter_idx
                save_checkpoint({
                    "completed_categories": list(completed_categories),
                    "letter_indices": letter_indices,
                    "total_collected": total_collected,
                })
                return total_collected

            except Exception as e:
                logger.error("  letter '%s': error: %s", letter, e)

            letter_idx += 1

        else:
            # Inner while completed without break (either target hit or letters exhausted)
            if current_count >= per_category_target:
                logger.info("  Category %s reached target (%d)", cat_name, current_count)
                completed_categories.add(cat_id)
            elif letter_idx >= len(QUERY_LETTERS):
                logger.info("  Category %s exhausted all letters (%d channels)", cat_name, current_count)
                completed_categories.add(cat_id)

        # Update category count and save checkpoint after each category
        category_counts[cat_id] = current_count
        letter_indices[str(cat_id)] = letter_idx
        save_checkpoint({
            "completed_categories": list(completed_categories),
            "letter_indices": letter_indices,
            "total_collected": total_collected,
        })

        # Check if we broke out of the inner while due to runtime/quota
        if not all_done:
            break

    if all_done:
        clear_checkpoint()

    return total_collected


def main():
    """Main entry point for Category Quota Sampler."""
    parser = argparse.ArgumentParser(description="Category Quota Sampler")
    parser.add_argument('--test', action='store_true',
                        help='Run in test mode (20 per category, 100 total)')
    parser.add_argument('--limit', type=int, default=75000,
                        help='Hard cap on total channels (default 75000)')
    parser.add_argument('--per-category', type=int, default=5000,
                        help='Floor target per category (default 5000)')
    parser.add_argument('--max-runtime', type=int, default=None,
                        help='Stop after N seconds (launchd safety)')
    parser.add_argument('--reserve-quota', type=int, default=2000,
                        help='Stop this many units before daily limit')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    logger.info("=" * 60)
    logger.info("CATEGORY QUOTA SAMPLER")
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        output_path = config.get_output_path("topic_stratified", "category_quota")

        total = discover_category_quota(
            youtube=youtube,
            per_category_target=args.per_category,
            total_limit=args.limit,
            test_mode=args.test,
            output_path=output_path,
            max_runtime=args.max_runtime,
            reserve_quota=args.reserve_quota,
            daily_quota_limit=load_config().get('daily_quota_limit', 0),
        )

        logger.info("")
        logger.info("=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info("Total channels collected: %d", total)

    except Exception as e:
        logger.error("Collection failed: %s", e)
        raise


if __name__ == "__main__":
    main()
