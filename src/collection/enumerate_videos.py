"""
enumerate_videos.py
-------------------
Build complete video inventory for a set of channels.

For each channel, paginates the uploads playlist to collect every video ID.
Supports checkpoint/resume for interrupted runs.

Usage:
    python -m src.collection.enumerate_videos \
        --channel-list data/channels/gender_gap/channel_ids.csv \
        [--output path] [--test] [--limit N]

Author: Katie Apker
Last Updated: Feb 16, 2026
"""

import argparse
import csv
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import get_authenticated_service, get_all_video_ids
import config

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'enumerate_videos_{config.get_date_stamp()}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )


def load_channel_ids(filepath: Path) -> List[str]:
    """
    Read channel IDs from a CSV file with a channel_id column.

    Args:
        filepath: Path to CSV containing channel_id column

    Returns:
        List of channel ID strings
    """
    channel_ids = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get('channel_id', '').strip()
            if cid:
                channel_ids.append(cid)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for cid in channel_ids:
        if cid not in seen:
            seen.add(cid)
            unique.append(cid)

    logger.info(f"Loaded {len(unique)} unique channel IDs from {filepath.name}")
    return unique


def load_checkpoint(checkpoint_path: Path) -> Dict:
    """
    Load checkpoint from JSON file.

    Args:
        checkpoint_path: Path to checkpoint JSON

    Returns:
        Checkpoint dict with 'completed_channels' list
    """
    if checkpoint_path.exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded checkpoint: {len(data.get('completed_channels', []))} channels already done")
            return data
    return {'completed_channels': []}


def save_checkpoint(checkpoint_path: Path, data: Dict) -> None:
    """
    Save checkpoint to JSON file.

    Args:
        checkpoint_path: Path to checkpoint JSON
        data: Checkpoint dict to save
    """
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def enumerate_all_channels(
    youtube,
    channel_ids: List[str],
    output_path: Path,
    checkpoint_path: Path,
    test_mode: bool = False,
    limit: int = None,
) -> int:
    """
    Enumerate all video IDs for a list of channels. Writes results to CSV
    incrementally and checkpoints after each channel.

    Args:
        youtube: Authenticated YouTube API service
        channel_ids: List of channel IDs to process
        output_path: Path to output CSV
        checkpoint_path: Path to checkpoint JSON
        test_mode: If True, default limit to 5 channels
        limit: Max number of channels to process

    Returns:
        Total number of videos enumerated
    """
    if test_mode and limit is None:
        limit = 5

    if limit is not None:
        channel_ids = channel_ids[:limit]

    # Load checkpoint
    checkpoint = load_checkpoint(checkpoint_path)
    completed_set = set(checkpoint['completed_channels'])

    # Filter to remaining channels
    remaining = [cid for cid in channel_ids if cid not in completed_set]
    resuming = len(completed_set) > 0

    if resuming:
        logger.info(f"Resuming: {len(completed_set)} done, {len(remaining)} remaining")

    # Determine file write mode: append if resuming and output exists, else write fresh
    if resuming and output_path.exists():
        file_mode = 'a'
        write_header = False
    else:
        file_mode = 'w'
        write_header = True

    total_videos = 0

    with open(output_path, file_mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=config.VIDEO_INVENTORY_FIELDS)
        if write_header:
            writer.writeheader()

        for idx, channel_id in enumerate(remaining):
            # Convert UC... to UU... for uploads playlist
            if channel_id.startswith('UC'):
                uploads_playlist_id = 'UU' + channel_id[2:]
            else:
                logger.warning(f"Unexpected channel ID format: {channel_id}, skipping")
                completed_set.add(channel_id)
                checkpoint['completed_channels'] = list(completed_set)
                save_checkpoint(checkpoint_path, checkpoint)
                continue

            try:
                videos, _ = get_all_video_ids(youtube, uploads_playlist_id, channel_id)

                scraped_at = datetime.utcnow().isoformat()
                for video in videos:
                    row = {
                        'video_id': video.get('video_id'),
                        'channel_id': video.get('channel_id'),
                        'published_at': video.get('published_at'),
                        'title': video.get('title'),
                        'scraped_at': scraped_at,
                    }
                    writer.writerow(row)

                total_videos += len(videos)

            except Exception as e:
                logger.error(f"Error enumerating {channel_id}: {e}")

            # Mark channel as done and checkpoint
            completed_set.add(channel_id)
            checkpoint['completed_channels'] = list(completed_set)
            save_checkpoint(checkpoint_path, checkpoint)

            # Progress logging every 100 channels
            channels_done = len(completed_set)
            total_to_do = len(channel_ids)
            if (idx + 1) % 100 == 0 or (idx + 1) == len(remaining):
                logger.info(
                    f"Progress: {channels_done}/{total_to_do} channels "
                    f"({total_videos} videos so far)"
                )

    return total_videos


def main():
    """CLI entry point for video enumeration."""
    parser = argparse.ArgumentParser(
        description="Build complete video inventory for a set of channels"
    )
    parser.add_argument(
        '--channel-list', type=str, required=True,
        help='Path to CSV with channel_id column'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Output CSV path (default: data/video_inventory/gender_gap_inventory.csv)'
    )
    parser.add_argument('--test', action='store_true', help='Test mode (5 channels)')
    parser.add_argument('--limit', type=int, default=None, help='Max channels to process')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    # Resolve paths
    channel_list_path = Path(args.channel_list)
    if not channel_list_path.is_absolute():
        channel_list_path = config.PROJECT_ROOT / channel_list_path

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = config.PROJECT_ROOT / output_path
    else:
        output_path = config.VIDEO_INVENTORY_DIR / "gender_gap_inventory.csv"

    # Derive checkpoint name from output file so parallel runs don't collide
    checkpoint_name = f".enumerate_{output_path.stem}_checkpoint.json"
    checkpoint_path = config.VIDEO_INVENTORY_DIR / checkpoint_name

    logger.info("=" * 60)
    logger.info("VIDEO INVENTORY ENUMERATION")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"Channel list: {channel_list_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Test mode: {args.test}")
    if args.limit:
        logger.info(f"Limit: {args.limit}")
    logger.info("=" * 60)

    if not channel_list_path.exists():
        logger.error(f"Channel list not found: {channel_list_path}")
        sys.exit(1)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        channel_ids = load_channel_ids(channel_list_path)

        if not channel_ids:
            logger.warning("No channel IDs found in input file")
            return

        total_videos = enumerate_all_channels(
            youtube=youtube,
            channel_ids=channel_ids,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
            test_mode=args.test,
            limit=args.limit,
        )

        # Clear checkpoint on successful completion
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.info("Cleared checkpoint file (run complete)")

        logger.info("=" * 60)
        logger.info("ENUMERATION COMPLETE")
        logger.info(f"Channels processed: {len(channel_ids)}")
        logger.info(f"Total videos found: {total_videos}")
        logger.info(f"Output: {output_path}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Enumeration failed: {e}")
        raise


if __name__ == "__main__":
    main()
