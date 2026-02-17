"""
discover_ai_creators.py
-----------------------
AI Creator Census: Discover channels creating AI-related content.

Follows the same video-first search pattern as discover_intent.py:
search for videos -> extract channel IDs -> get channel details -> save.

Unlike the new creator cohort streams, this has NO date filter.
We want all AI creators regardless of when they started.

Supports checkpoint/resume: if interrupted, re-run the same command
and it picks up where it left off.

Usage:
    python -m src.collection.discover_ai_creators [--test] [--limit N]
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    search_videos_paginated,
    extract_channel_ids_from_search,
    get_channel_full_details,
)
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOGS_DIR / f'discover_ai_creators_{config.get_date_stamp()}.log')
    ]
)
logger = logging.getLogger(__name__)

CHECKPOINT_PATH = config.AI_CENSUS_DIR / '.discover_checkpoint.json'


def _load_checkpoint() -> dict:
    """Load checkpoint state if it exists."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, 'r') as f:
            cp = json.load(f)
        logger.info(f"Resuming from checkpoint: {len(cp.get('seen_channel_ids', []))} channels seen, "
                     f"{len(cp.get('completed_terms', []))} terms completed")
        return cp
    return {'seen_channel_ids': [], 'completed_terms': []}


def _save_checkpoint(seen_channel_ids: Set[str], completed_terms: List[str]) -> None:
    """Save checkpoint state."""
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_PATH, 'w') as f:
        json.dump({
            'seen_channel_ids': list(seen_channel_ids),
            'completed_terms': completed_terms,
            'saved_at': datetime.now(timezone.utc).isoformat(),
        }, f)


def _remove_checkpoint() -> None:
    """Remove checkpoint file after successful completion."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint removed (collection complete)")


def _load_existing_output(output_path: Path) -> Dict[str, Dict]:
    """Load channels from an existing partial output CSV."""
    channels_by_id: Dict[str, Dict] = {}
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get('channel_id')
                if cid:
                    channels_by_id[cid] = row
        logger.info(f"Loaded {len(channels_by_id)} channels from existing output")
    return channels_by_id


def _append_channels_to_csv(channels: List[Dict], output_path: Path, write_header: bool = False) -> None:
    """Append channel rows to the output CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mode = 'w' if write_header else 'a'
    with open(output_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
        if write_header:
            writer.writeheader()
        for channel in channels:
            row = {field: channel.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
            writer.writerow(row)


def discover_ai_creators(
    youtube,
    output_path: Path,
    target_count: int = 50000,
    test_mode: bool = False,
    months_back: int = 18,
    sort_orders: List[str] = None,
) -> int:
    """
    Discover channels creating AI-related content across search terms.
    Writes incrementally to CSV with checkpoint/resume.

    For each search term, iterates over multiple sort orders (e.g., relevance
    and date) to surface different channels per term. Each (term, sort_order)
    combo is a separate checkpoint unit.

    Args:
        youtube: Authenticated YouTube API service
        output_path: Path to output CSV
        target_count: Target number of channels to collect
        test_mode: If True, uses reduced targets for testing
        months_back: How many months back to search (default 18)
        sort_orders: List of YouTube sort orders to cycle through per term

    Returns:
        Total number of channels collected
    """
    if sort_orders is None:
        sort_orders = ["relevance", "date"]

    if test_mode:
        target_count = min(target_count, 100)
        logger.info("TEST MODE: Limited to 100 channels")

    # Load checkpoint
    checkpoint = _load_checkpoint()
    completed_terms = checkpoint.get('completed_terms', [])

    # Always load existing output to avoid overwriting prior results
    channels_by_id = _load_existing_output(output_path)
    seen_channel_ids: Set[str] = set(checkpoint.get('seen_channel_ids', []))
    seen_channel_ids.update(channels_by_id.keys())

    needs_header = not output_path.exists() or len(channels_by_id) == 0

    # Generate 30-day time windows
    time_windows = _generate_ai_time_windows(months_back=months_back)

    search_terms = config.AI_SEARCH_TERMS

    # Build work units: (term, sort_order) combos
    work_units = [(term, order) for term in search_terms for order in sort_orders]

    # Per-term target (across all sort orders for that term)
    per_term_target = max(10, target_count // len(search_terms))

    logger.info(f"Target: {target_count} channels")
    logger.info(f"Already collected: {len(channels_by_id)}")
    logger.info(f"Search terms: {len(search_terms)}, sort orders: {sort_orders}")
    logger.info(f"Work units: {len(work_units)} ({len(completed_terms)} already done)")
    logger.info(f"Per-term target: {per_term_target}")
    logger.info(f"Time windows: {len(time_windows)} (30-day spans, {months_back} months)")

    for idx, (term, order) in enumerate(work_units):
        if len(channels_by_id) >= target_count:
            logger.info(f"Reached target of {target_count} channels")
            break

        # Checkpoint key is "term||order" to track (term, sort_order) combos
        unit_key = f"{term}||{order}"

        if unit_key in completed_terms:
            continue

        logger.info(f"[{idx+1}/{len(work_units)}] Searching: '{term}' (order={order})")

        term_channels = 0
        term_new_channels: List[Dict] = []

        for window_start, window_end in time_windows:
            if term_channels >= per_term_target:
                break
            if len(channels_by_id) >= target_count:
                break

            try:
                search_results = search_videos_paginated(
                    youtube=youtube,
                    query=term,
                    published_after=window_start,
                    published_before=window_end,
                    max_pages=3 if test_mode else 10,
                    order=order
                )

                if not search_results:
                    continue

                channel_ids = extract_channel_ids_from_search(search_results)
                new_channel_ids = [
                    cid for cid in channel_ids
                    if cid not in seen_channel_ids
                ]

                if not new_channel_ids:
                    continue

                channel_details = get_channel_full_details(
                    youtube=youtube,
                    channel_ids=new_channel_ids,
                    stream_type="ai_census",
                    discovery_language="English",
                    discovery_keyword=term
                )

                for channel in channel_details:
                    cid = channel['channel_id']
                    if cid not in channels_by_id:
                        channels_by_id[cid] = channel
                        seen_channel_ids.add(cid)
                        term_channels += 1
                        term_new_channels.append(channel)

                logger.info(f"  -> Found {len(channel_details)} channels "
                           f"(unit total: {term_channels}, overall: {len(channels_by_id)})")

            except Exception as e:
                logger.error(f"  Error searching '{term}' (order={order}): {e}")
                continue

        # Write this unit's channels to CSV
        if term_new_channels:
            _append_channels_to_csv(term_new_channels, output_path, write_header=needs_header)
            needs_header = False
            logger.info(f"  Wrote {len(term_new_channels)} channels to {output_path.name}")

        # Checkpoint after each work unit
        completed_terms.append(unit_key)
        _save_checkpoint(seen_channel_ids, completed_terms)

    total = len(channels_by_id)
    logger.info(f"Discovery complete: {total} total channels")

    # Clean up checkpoint on success
    _remove_checkpoint()

    return total


def _generate_ai_time_windows(months_back: int = 18) -> List[Tuple[str, str]]:
    """
    Generate 30-day time windows going back N months.

    Args:
        months_back: Number of months to look back (default 18)

    Returns:
        List of (start_iso, end_iso) tuples
    """
    windows = []
    now = datetime.now(timezone.utc)

    for m in range(0, months_back):
        window_end = now - timedelta(days=m * 30)
        window_start = window_end - timedelta(days=30)

        windows.append((
            window_start.isoformat(),
            window_end.isoformat()
        ))

    return windows


def main() -> None:
    """Main entry point for AI Creator Census collection."""
    parser = argparse.ArgumentParser(description="AI Creator Census: Discover AI content creators")
    parser.add_argument('--test', action='store_true', help='Run in test mode (100 channels)')
    parser.add_argument('--limit', type=int, default=50000, help='Target channel count')
    parser.add_argument('--months-back', type=int, default=18, help='Months of history to search (default 18)')
    parser.add_argument('--sort-orders', type=str, default='relevance,date',
                        help='Comma-separated sort orders to cycle per term (default: relevance,date)')
    args = parser.parse_args()

    sort_orders = [s.strip() for s in args.sort_orders.split(',')]

    config.ensure_directories()

    logger.info("=" * 60)
    logger.info("AI CREATOR CENSUS: DISCOVERY (SCALED)")
    logger.info("=" * 60)
    logger.info(f"Months back: {args.months_back}")
    logger.info(f"Sort orders: {sort_orders}")

    output_path = config.AI_CENSUS_DIR / f"initial_{config.get_date_stamp()}.csv"

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        total = discover_ai_creators(
            youtube=youtube,
            output_path=output_path,
            target_count=args.limit,
            test_mode=args.test,
            months_back=args.months_back,
            sort_orders=sort_orders,
        )

        if total == 0:
            logger.warning("No channels discovered!")
            return

        # Summary by discovery keyword
        logger.info("=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total channels: {total}")
        logger.info(f"Output: {output_path}")

        # Read back for keyword summary
        by_keyword: Dict[str, int] = {}
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                kw = row.get('discovery_keyword', 'Unknown')
                by_keyword[kw] = by_keyword.get(kw, 0) + 1

        for kw, count in sorted(by_keyword.items(), key=lambda x: -x[1]):
            logger.info(f"  {kw}: {count}")

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
