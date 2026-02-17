"""
discover_trending.py
--------------------
Trending Tracker — daily log of channels appearing on YouTube's trending charts.

Trending represents a different selection mechanism than search. It captures
what's culturally salient: viral content, news events, entertainment. Cross-
referencing trending channels against other streams reveals which creators
break through to cultural visibility.

This is NOT a one-shot discovery. It runs daily and produces two outputs:
1. Trending log (append-only): every video sighting with date, region, position
2. Channel details: full CHANNEL_INITIAL_FIELDS for newly seen channels only

Uses videos.list(chart=mostPopular) which returns video resources directly
(1 unit/call, not 100 like search.list). Iterates through 51 region codes.

Target: Accumulating daily (no fixed target)
Method: videos.list(chart=mostPopular) across 51 region codes
Cadence: Run daily via launchd/cron

Usage:
    python -m src.collection.discover_trending [--test] [--limit-regions N] [--date YYYY-MM-DD]

Author: Katie Apker
Last Updated: Feb 18, 2026
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    get_trending_videos,
    get_channel_full_details,
)
import config

logger = logging.getLogger(__name__)

TRENDING_DIR = config.STREAM_DIRS["trending"]
CHECKPOINT_PATH = TRENDING_DIR / ".trending_checkpoint.json"


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'discover_trending_{config.get_date_stamp()}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )


def get_trending_log_path(date_str: str) -> Path:
    """Get path for the daily trending log file."""
    return TRENDING_DIR / f"trending_log_{date_str}.csv"


def get_channel_details_path() -> Path:
    """Get path for the cumulative channel details file."""
    return TRENDING_DIR / "channel_details.csv"


def load_known_channel_ids() -> Set[str]:
    """Load channel IDs already in the cumulative channel details file."""
    details_path = get_channel_details_path()
    known = set()
    if details_path.exists():
        with open(details_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get('channel_id', '').strip()
                if cid:
                    known.add(cid)
    return known


def load_checkpoint(date_str: str) -> Set[str]:
    """Load completed regions for today's run."""
    if not CHECKPOINT_PATH.exists():
        return set()

    with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
        ckpt = json.load(f)

    if ckpt.get("date") != date_str:
        return set()

    return set(ckpt.get("completed_regions", []))


def save_checkpoint(date_str: str, completed_regions: Set[str], channel_count: int) -> None:
    """Save checkpoint for today's run."""
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "date": date_str,
            "completed_regions": list(completed_regions),
            "channel_count": channel_count,
            "timestamp": datetime.utcnow().isoformat(),
        }, f)


def clear_checkpoint() -> None:
    """Remove checkpoint file after successful completion."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared")


def parse_trending_video(item: Dict, region_code: str, position: int, date_str: str) -> Dict:
    """Parse a trending video item into a trending log row."""
    snippet = item.get('snippet', {})
    statistics = item.get('statistics', {})

    category_id = snippet.get('categoryId', '')
    try:
        category_name = config.YOUTUBE_CATEGORIES.get(int(category_id), 'Unknown')
    except (ValueError, TypeError):
        category_name = 'Unknown'

    return {
        'trending_date': date_str,
        'region_code': region_code,
        'position': position,
        'video_id': item.get('id'),
        'channel_id': snippet.get('channelId'),
        'video_title': snippet.get('title'),
        'video_view_count': int(statistics.get('viewCount', 0)),
        'video_like_count': int(statistics.get('likeCount', 0)),
        'video_comment_count': int(statistics.get('commentCount', 0)),
        'video_published_at': snippet.get('publishedAt'),
        'category_id': category_id,
        'category_name': category_name,
        'scraped_at': datetime.utcnow().isoformat(),
    }


def run_trending_collection(
    youtube,
    date_str: str,
    test_mode: bool = False,
    limit_regions: Optional[int] = None,
) -> Dict:
    """
    Collect trending videos across all region codes for one day.

    Produces two outputs:
    - trending_log_{date}.csv: every video sighting (append within day)
    - channel_details.csv: cumulative file of unique channel details

    Args:
        youtube: Authenticated YouTube API service
        date_str: Date string (YYYY-MM-DD) for the collection
        test_mode: If True, limits to 3 regions
        limit_regions: Optional cap on number of regions to process

    Returns:
        Summary dict with counts
    """
    regions = config.TRENDING_REGION_CODES
    if test_mode:
        regions = regions[:3]
        logger.info(f"TEST MODE: Limited to {len(regions)} regions")
    elif limit_regions:
        regions = regions[:limit_regions]

    completed_regions = load_checkpoint(date_str)
    known_channel_ids = load_known_channel_ids()

    trending_log_path = get_trending_log_path(date_str)
    channel_details_path = get_channel_details_path()

    # Initialize trending log for today if fresh
    if not completed_regions:
        trending_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(trending_log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.TRENDING_LOG_FIELDS)
            writer.writeheader()

    # Initialize channel details file if it doesn't exist
    if not channel_details_path.exists():
        with open(channel_details_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
            writer.writeheader()

    total_videos = 0
    total_new_channels = 0
    new_channel_ids_today: Set[str] = set()

    logger.info(f"Date: {date_str}")
    logger.info(f"Regions: {len(regions)}")
    logger.info(f"Known channels: {len(known_channel_ids)}")
    logger.info(f"Completed regions (resumed): {len(completed_regions)}")

    for idx, region in enumerate(regions):
        if region in completed_regions:
            continue

        logger.info(f"[{idx+1}/{len(regions)}] Region: {region}")

        try:
            videos = get_trending_videos(
                youtube=youtube,
                region_code=region,
                max_pages=1 if test_mode else 4,
            )

            if not videos:
                logger.info(f"  No trending videos for {region}")
                completed_regions.add(region)
                save_checkpoint(date_str, completed_regions, total_new_channels)
                continue

            # Write trending log entries
            log_rows = []
            region_channel_ids: Set[str] = set()
            for pos, item in enumerate(videos, 1):
                row = parse_trending_video(item, region, pos, date_str)
                log_rows.append(row)
                cid = row['channel_id']
                if cid:
                    region_channel_ids.add(cid)

            with open(trending_log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=config.TRENDING_LOG_FIELDS)
                for row in log_rows:
                    writer.writerow(row)

            total_videos += len(log_rows)

            # Identify channels we haven't seen before
            truly_new = [
                cid for cid in region_channel_ids
                if cid not in known_channel_ids and cid not in new_channel_ids_today
            ]

            if truly_new:
                channel_details = get_channel_full_details(
                    youtube=youtube,
                    channel_ids=truly_new,
                    stream_type="trending",
                    discovery_language="global",
                    discovery_keyword=f"trending_{region}"
                )

                with open(channel_details_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
                    for ch in channel_details:
                        row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
                        writer.writerow(row)
                        new_channel_ids_today.add(ch['channel_id'])
                        known_channel_ids.add(ch['channel_id'])

                total_new_channels += len(channel_details)

            logger.info(f"  {len(videos)} videos, {len(truly_new)} new channels")

        except Exception as e:
            logger.error(f"  Error for region {region}: {e}")

        completed_regions.add(region)
        save_checkpoint(date_str, completed_regions, total_new_channels)

    clear_checkpoint()

    summary = {
        'date': date_str,
        'regions_processed': len(completed_regions),
        'total_video_sightings': total_videos,
        'new_channels_today': total_new_channels,
        'cumulative_unique_channels': len(known_channel_ids),
    }

    logger.info("=" * 60)
    logger.info("TRENDING COLLECTION SUMMARY")
    logger.info("=" * 60)
    for k, v in summary.items():
        logger.info(f"  {k}: {v}")

    return summary


def main():
    """Main entry point for Trending Tracker."""
    parser = argparse.ArgumentParser(description="Trending Tracker (Daily)")
    parser.add_argument('--test', action='store_true', help='Run in test mode (3 regions)')
    parser.add_argument('--limit-regions', type=int, default=None, help='Limit number of regions')
    parser.add_argument('--date', type=str, default=None,
                        help='Collection date (YYYY-MM-DD, default=today UTC)')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    date_str = args.date or datetime.utcnow().strftime("%Y-%m-%d")

    logger.info("=" * 60)
    logger.info("TRENDING TRACKER (DAILY)")
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        run_trending_collection(
            youtube=youtube,
            date_str=date_str,
            test_mode=args.test,
            limit_regions=args.limit_regions,
        )

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
