"""
discover_ai_creators.py
-----------------------
AI Creator Census: Discover channels creating AI-related content.

Follows the same video-first search pattern as discover_intent.py:
search for videos -> extract channel IDs -> get channel details -> save.

Unlike the new creator cohort streams, this has NO date filter.
We want all AI creators regardless of when they started.

Usage:
    python -m src.collection.discover_ai_creators [--test] [--limit N]
"""

import argparse
import csv
import logging
import sys
from datetime import datetime, timedelta
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


def discover_ai_creators(
    youtube,
    target_count: int = 5000,
    test_mode: bool = False
) -> List[Dict]:
    """
    Discover channels creating AI-related content across search terms.

    Args:
        youtube: Authenticated YouTube API service
        target_count: Target number of channels to collect
        test_mode: If True, uses reduced targets for testing

    Returns:
        List of channel data dictionaries
    """
    if test_mode:
        target_count = min(target_count, 100)
        logger.info("TEST MODE: Limited to 100 channels")

    # All discovered channels (keyed by channel_id to deduplicate)
    channels_by_id: Dict[str, Dict] = {}

    # Track channel IDs we've already processed
    seen_channel_ids: Set[str] = set()

    # Generate 30-day time windows going back 12 months
    time_windows = _generate_ai_time_windows()

    # AI search terms (simple list, not language-keyed dict)
    search_terms = config.AI_SEARCH_TERMS

    # Calculate per-term target
    per_term_target = max(10, target_count // len(search_terms))

    logger.info(f"Target: {target_count} channels")
    logger.info(f"Search terms: {len(search_terms)}")
    logger.info(f"Per-term target: {per_term_target}")
    logger.info(f"Time windows: {len(time_windows)} (30-day spans, 12 months)")

    for idx, term in enumerate(search_terms):
        if len(channels_by_id) >= target_count:
            logger.info(f"Reached target of {target_count} channels")
            break

        logger.info(f"[{idx+1}/{len(search_terms)}] Searching: '{term}'")

        term_channels = 0

        # Search across multiple time windows
        for window_start, window_end in time_windows:
            if term_channels >= per_term_target:
                break

            try:
                # Search for videos with this term, ordered by relevance
                search_results = search_videos_paginated(
                    youtube=youtube,
                    query=term,
                    published_after=window_start,
                    published_before=window_end,
                    max_pages=3 if test_mode else 10,
                    order="relevance"
                )

                if not search_results:
                    continue

                # Extract unique channel IDs
                channel_ids = extract_channel_ids_from_search(search_results)

                # Filter to only new channel IDs
                new_channel_ids = [
                    cid for cid in channel_ids
                    if cid not in seen_channel_ids
                ]

                if not new_channel_ids:
                    continue

                # Get full channel details
                channel_details = get_channel_full_details(
                    youtube=youtube,
                    channel_ids=new_channel_ids,
                    stream_type="ai_census",
                    discovery_language="English",
                    discovery_keyword=term
                )

                # NO date filter — we want ALL channels regardless of creation date

                # Add to collection
                for channel in channel_details:
                    cid = channel['channel_id']
                    if cid not in channels_by_id:
                        channels_by_id[cid] = channel
                        seen_channel_ids.add(cid)
                        term_channels += 1

                logger.info(f"  -> Found {len(channel_details)} channels "
                           f"(term total: {term_channels}, overall: {len(channels_by_id)})")

            except Exception as e:
                logger.error(f"  Error searching '{term}': {e}")
                continue

    channels = list(channels_by_id.values())
    logger.info(f"Discovery complete: {len(channels)} total channels")

    return channels


def _generate_ai_time_windows() -> List[Tuple[str, str]]:
    """
    Generate 30-day time windows going back 12 months.

    Unlike discover_intent's 48-hour windows (which target recent uploads),
    these broader windows cast a wider net for established AI creators.

    Returns:
        List of (start_iso, end_iso) tuples
    """
    windows = []
    now = datetime.utcnow()

    # 30-day windows going back 12 months (roughly 12 windows)
    for months_back in range(0, 12):
        window_end = now - timedelta(days=months_back * 30)
        window_start = window_end - timedelta(days=30)

        windows.append((
            window_start.isoformat() + 'Z',
            window_end.isoformat() + 'Z'
        ))

    return windows


def save_channels_to_csv(channels: List[Dict], output_path: Path) -> None:
    """
    Save channel data to CSV file.

    Args:
        channels: List of channel dictionaries
        output_path: Path to output CSV file
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
        writer.writeheader()

        for channel in channels:
            # Ensure all expected fields are present
            row = {field: channel.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
            writer.writerow(row)

    logger.info(f"Saved {len(channels)} channels to {output_path}")


def main() -> None:
    """Main entry point for AI Creator Census collection."""
    parser = argparse.ArgumentParser(description="AI Creator Census: Discover AI content creators")
    parser.add_argument('--test', action='store_true', help='Run in test mode (100 channels)')
    parser.add_argument('--limit', type=int, default=5000, help='Target channel count')
    args = parser.parse_args()

    # Ensure directories exist
    config.ensure_directories()

    logger.info("=" * 60)
    logger.info("AI CREATOR CENSUS: DISCOVERY")
    logger.info("=" * 60)

    try:
        # Authenticate
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        # Discover channels
        channels = discover_ai_creators(
            youtube=youtube,
            target_count=args.limit,
            test_mode=args.test
        )

        if not channels:
            logger.warning("No channels discovered!")
            return

        # Save to CSV
        output_path = config.AI_CENSUS_DIR / f"initial_{config.get_date_stamp()}.csv"
        save_channels_to_csv(channels, output_path)

        # Summary by discovery keyword
        logger.info("=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total channels: {len(channels)}")

        by_keyword: Dict[str, int] = {}
        for ch in channels:
            kw = ch.get('discovery_keyword', 'Unknown')
            by_keyword[kw] = by_keyword.get(kw, 0) + 1

        for kw, count in sorted(by_keyword.items(), key=lambda x: -x[1]):
            logger.info(f"  {kw}: {count}")

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
