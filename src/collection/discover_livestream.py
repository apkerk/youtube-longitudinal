"""
discover_livestream.py
----------------------
Livestream Creators — channels that have completed livestreams.

Livestreaming is a distinct creator modality with different engagement dynamics
(real-time interaction, longer sessions, different monetization). Livestream-first
creators may have different growth trajectories than video-first creators.

Uses the eventType=completed search parameter to find channels with completed
livestreams, then fetches full channel details.

Supports checkpoint/resume: progress is saved after each time-window batch so
interrupted runs can continue without re-consuming API quota.

Target: 25,000 channels
Method: search.list(eventType=completed, type=video, order=date)
Filter: None (any age channel)

Usage:
    python -m src.collection.discover_livestream [--test] [--limit N]

Author: Katie Apker
Last Updated: Feb 18, 2026
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    search_videos_paginated,
    extract_channel_ids_from_search,
    get_channel_full_details,
)
import config

logger = logging.getLogger(__name__)

CHECKPOINT_PATH = config.STREAM_DIRS["livestream"] / ".discovery_checkpoint.json"

# Time windows to cycle through (30-day windows going back 12 months)
# Gives diversity across upload dates
NUM_WINDOWS = 12
WINDOW_DAYS = 30


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'discover_livestream_{config.get_date_stamp()}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )


def get_time_windows(num_windows: int = NUM_WINDOWS) -> List[tuple]:
    """Generate time windows (30-day chunks going back from now)."""
    windows = []
    now = datetime.utcnow()
    for i in range(num_windows):
        end = now - timedelta(days=i * WINDOW_DAYS)
        start = end - timedelta(days=WINDOW_DAYS)
        windows.append((
            start.isoformat() + 'Z',
            end.isoformat() + 'Z',
            f"window_{i}"
        ))
    return windows


def load_checkpoint(output_path: Path) -> tuple:
    """Load discovery checkpoint and rebuild state from partial CSV."""
    completed_windows: Set[str] = set()
    channels_by_id: Dict[str, Dict] = {}

    if not CHECKPOINT_PATH.exists():
        return completed_windows, channels_by_id

    with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
        ckpt = json.load(f)

    completed_windows = set(ckpt.get("completed_queries", []))

    saved_path = Path(ckpt.get("output_path", ""))
    if saved_path.exists() and saved_path == output_path:
        with open(saved_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get('channel_id', '').strip()
                if cid:
                    channels_by_id[cid] = row

    logger.info(
        f"Resumed from checkpoint: {len(channels_by_id)} channels, "
        f"{len(completed_windows)} windows completed"
    )
    return completed_windows, channels_by_id


def save_checkpoint(completed_windows: Set[str], output_path: Path, channel_count: int) -> None:
    """Save discovery checkpoint."""
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "completed_queries": list(completed_windows),
            "output_path": str(output_path),
            "channel_count": channel_count,
            "timestamp": datetime.utcnow().isoformat(),
        }, f)


def clear_checkpoint() -> None:
    """Remove checkpoint file after successful completion."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared")


def discover_livestream_channels(
    youtube,
    target_count: int = 25000,
    test_mode: bool = False,
    output_path: Optional[Path] = None,
) -> List[Dict]:
    """
    Discover channels with completed livestreams.

    Searches across multiple time windows using eventType=completed to find
    channels that have done livestreams. Writes incrementally after each window.

    Args:
        youtube: Authenticated YouTube API service
        target_count: Target number of channels to collect
        test_mode: If True, uses reduced targets for testing
        output_path: Path to write CSV output (required)

    Returns:
        List of channel data dictionaries
    """
    if test_mode:
        target_count = min(target_count, 50)
        logger.info("TEST MODE: Limited to 50 channels")

    completed_windows, channels_by_id = load_checkpoint(output_path)
    seen_channel_ids: Set[str] = set(channels_by_id.keys())

    if not completed_windows:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
            writer.writeheader()

    windows = get_time_windows(num_windows=3 if test_mode else NUM_WINDOWS)

    logger.info(f"Target: {target_count} channels")
    logger.info(f"Time windows: {len(windows)}")
    logger.info(f"Already collected: {len(channels_by_id)} channels")

    for idx, (pub_after, pub_before, window_label) in enumerate(windows):
        if len(channels_by_id) >= target_count:
            logger.info(f"Reached target of {target_count} channels")
            break

        if window_label in completed_windows:
            continue

        logger.info(f"[{idx+1}/{len(windows)}] Window: {pub_after[:10]} to {pub_before[:10]}")

        batch_new_channels: List[Dict] = []

        try:
            search_results = search_videos_paginated(
                youtube=youtube,
                published_after=pub_after,
                published_before=pub_before,
                max_pages=3 if test_mode else 10,
                order="date",
                eventType="completed",
            )

            if not search_results:
                completed_windows.add(window_label)
                save_checkpoint(completed_windows, output_path, len(channels_by_id))
                continue

            channel_ids = extract_channel_ids_from_search(search_results)
            new_channel_ids = [
                cid for cid in channel_ids
                if cid not in seen_channel_ids
            ]

            if not new_channel_ids:
                completed_windows.add(window_label)
                save_checkpoint(completed_windows, output_path, len(channels_by_id))
                continue

            channel_details = get_channel_full_details(
                youtube=youtube,
                channel_ids=new_channel_ids,
                stream_type="livestream",
                discovery_language="global",
                discovery_keyword="eventType=completed"
            )

            for channel in channel_details:
                cid = channel['channel_id']
                if cid not in channels_by_id:
                    channels_by_id[cid] = channel
                    seen_channel_ids.add(cid)
                    batch_new_channels.append(channel)

            logger.info(f"  Found {len(batch_new_channels)} new channels "
                       f"(total: {len(channels_by_id)})")

        except Exception as e:
            logger.error(f"  Error in window {window_label}: {e}")

        if batch_new_channels:
            with open(output_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
                for ch in batch_new_channels:
                    row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
                    writer.writerow(row)

        completed_windows.add(window_label)
        save_checkpoint(completed_windows, output_path, len(channels_by_id))

    clear_checkpoint()

    channels = list(channels_by_id.values())
    logger.info(f"Discovery complete: {len(channels)} total channels")
    return channels


def main():
    """Main entry point for Livestream Creators collection."""
    parser = argparse.ArgumentParser(description="Livestream Creators Discovery")
    parser.add_argument('--test', action='store_true', help='Run in test mode (50 channels)')
    parser.add_argument('--limit', type=int, default=25000, help='Target channel count')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    logger.info("=" * 60)
    logger.info("LIVESTREAM CREATORS DISCOVERY")
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        output_path = config.get_output_path("livestream", "initial")

        channels = discover_livestream_channels(
            youtube=youtube,
            target_count=args.limit,
            test_mode=args.test,
            output_path=output_path,
        )

        if not channels:
            logger.warning("No channels discovered!")
            return

        logger.info("=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total channels: {len(channels)}")

        tiers = {'<1K': 0, '1K-10K': 0, '10K-100K': 0, '100K-1M': 0, '>1M': 0}
        for ch in channels:
            subs = ch.get('subscriber_count', 0) or 0
            if isinstance(subs, str):
                try:
                    subs = int(subs)
                except ValueError:
                    subs = 0
            if subs < 1000:
                tiers['<1K'] += 1
            elif subs < 10000:
                tiers['1K-10K'] += 1
            elif subs < 100000:
                tiers['10K-100K'] += 1
            elif subs < 1000000:
                tiers['100K-1M'] += 1
            else:
                tiers['>1M'] += 1

        for tier, count in tiers.items():
            logger.info(f"  {tier} subs: {count}")

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
