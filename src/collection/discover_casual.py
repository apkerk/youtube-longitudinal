"""
discover_casual.py
------------------
Stream D: Casual Uploaders (Amateur Control Group)

Discovers channels that upload with default/unedited file names, indicating
casual or amateur uploading behavior (IMG_, MVI_, DSC_, etc.).

This serves as a control group for creators who are not treating YouTube
as a serious entrepreneurial endeavor.

Supports checkpoint/resume: progress is saved after each query batch so
interrupted runs can continue without re-consuming API quota.

Target: 5,000 channels (realistic ceiling with expanded patterns)
Method: Raw file name queries (~40 device/app default patterns)
Filter: None (any age channel)

Usage:
    python -m src.collection.discover_casual [--test] [--limit N]

Author: Katie Apker
Last Updated: Feb 17, 2026
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

CHECKPOINT_PATH = config.STREAM_DIRS["stream_d"] / ".discovery_checkpoint.json"


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'discover_casual_{config.get_date_stamp()}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )


def load_checkpoint(output_path: Path) -> tuple:
    """Load discovery checkpoint and rebuild state from partial CSV."""
    completed_queries: Set[str] = set()
    channels_by_id: Dict[str, Dict] = {}

    if not CHECKPOINT_PATH.exists():
        return completed_queries, channels_by_id

    with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
        ckpt = json.load(f)

    completed_queries = set(ckpt.get("completed_queries", []))

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
        f"{len(completed_queries)} queries completed"
    )
    return completed_queries, channels_by_id


def save_checkpoint(completed_queries: Set[str], output_path: Path, channel_count: int) -> None:
    """Save discovery checkpoint."""
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "completed_queries": list(completed_queries),
            "output_path": str(output_path),
            "channel_count": channel_count,
            "timestamp": datetime.utcnow().isoformat(),
        }, f)


def clear_checkpoint() -> None:
    """Remove checkpoint file after successful completion."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared")


def discover_casual_channels(
    youtube,
    target_count: int = 5000,
    test_mode: bool = False,
    output_path: Optional[Path] = None,
) -> List[Dict]:
    """
    Discover casual uploaders using raw file name patterns.

    Writes channels incrementally to output_path after each query batch.
    Supports checkpoint/resume via CHECKPOINT_PATH.

    Args:
        youtube: Authenticated YouTube API service
        target_count: Target number of channels to collect
        test_mode: If True, uses reduced targets for testing
        output_path: Path to write CSV output (required)

    Returns:
        List of channel data dictionaries
    """
    if test_mode:
        target_count = min(target_count, 100)
        logger.info("TEST MODE: Limited to 100 channels")

    # Load checkpoint or start fresh
    completed_queries, channels_by_id = load_checkpoint(output_path)
    seen_channel_ids: Set[str] = set(channels_by_id.keys())

    # If fresh start, write CSV header
    if not completed_queries:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
            writer.writeheader()

    queries = config.CASUAL_QUERIES
    per_query_target = max(50, target_count // len(queries))

    logger.info(f"Target: {target_count} channels")
    logger.info(f"Queries: {len(queries)} filename patterns")
    logger.info(f"Per-query target: {per_query_target}")
    logger.info(f"Already collected: {len(channels_by_id)} channels")

    # Recent time window (last 30 days)
    now = datetime.utcnow()
    published_after = (now - timedelta(days=30)).isoformat() + 'Z'
    published_before = now.isoformat() + 'Z'

    for idx, query in enumerate(queries):
        if len(channels_by_id) >= target_count:
            logger.info(f"Reached target of {target_count} channels")
            break

        if query in completed_queries:
            continue

        logger.info(f"[{idx+1}/{len(queries)}] Searching: '{query}'")

        batch_new_channels: List[Dict] = []
        query_channels = 0

        try:
            # Search by date to get recent casual uploads
            search_results = search_videos_paginated(
                youtube=youtube,
                query=query,
                published_after=published_after,
                published_before=published_before,
                max_pages=3 if test_mode else 15,
                order="date"
            )

            if not search_results:
                completed_queries.add(query)
                save_checkpoint(completed_queries, output_path, len(channels_by_id))
                continue

            channel_ids = extract_channel_ids_from_search(search_results)
            new_channel_ids = [
                cid for cid in channel_ids
                if cid not in seen_channel_ids
            ]

            if not new_channel_ids:
                completed_queries.add(query)
                save_checkpoint(completed_queries, output_path, len(channels_by_id))
                continue

            # Limit per query for diversity
            batch_ids = new_channel_ids[:per_query_target]

            channel_details = get_channel_full_details(
                youtube=youtube,
                channel_ids=batch_ids,
                stream_type="stream_d",
                discovery_language="global",
                discovery_keyword=query
            )

            for channel in channel_details:
                cid = channel['channel_id']
                if cid not in channels_by_id:
                    channels_by_id[cid] = channel
                    seen_channel_ids.add(cid)
                    batch_new_channels.append(channel)
                    query_channels += 1

            logger.info(f"  Found {query_channels} new channels "
                       f"(total: {len(channels_by_id)})")

        except Exception as e:
            logger.error(f"  Error searching '{query}': {e}")

        # Append this query's new channels to CSV
        if batch_new_channels:
            with open(output_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
                for ch in batch_new_channels:
                    row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
                    writer.writerow(row)

        # Save checkpoint after this query
        completed_queries.add(query)
        save_checkpoint(completed_queries, output_path, len(channels_by_id))

    clear_checkpoint()

    channels = list(channels_by_id.values())
    logger.info(f"Discovery complete: {len(channels)} total channels")
    return channels


def save_channels_to_csv(channels: List[Dict], output_path: Path) -> None:
    """Save channel data to CSV file (full write, overwrites existing)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
        writer.writeheader()

        for channel in channels:
            row = {field: channel.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
            writer.writerow(row)

    logger.info(f"Saved {len(channels)} channels to {output_path}")


def main():
    """Main entry point for Stream D collection."""
    parser = argparse.ArgumentParser(description="Stream D: Casual Uploaders")
    parser.add_argument('--test', action='store_true', help='Run in test mode (100 channels)')
    parser.add_argument('--limit', type=int, default=5000, help='Target channel count')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    logger.info("=" * 60)
    logger.info("STREAM D: CASUAL UPLOADERS (AMATEUR)")
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        output_path = config.get_output_path("stream_d", "initial")

        channels = discover_casual_channels(
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

        # Distribution by video count (casualness indicator)
        video_buckets = {'1 video': 0, '2-5': 0, '6-20': 0, '21-100': 0, '>100': 0}

        for ch in channels:
            vids = ch.get('video_count', 0) or 0
            if isinstance(vids, str):
                try:
                    vids = int(vids)
                except ValueError:
                    vids = 0
            if vids == 1:
                video_buckets['1 video'] += 1
            elif vids <= 5:
                video_buckets['2-5'] += 1
            elif vids <= 20:
                video_buckets['6-20'] += 1
            elif vids <= 100:
                video_buckets['21-100'] += 1
            else:
                video_buckets['>100'] += 1

        for bucket, count in video_buckets.items():
            logger.info(f"  {bucket} videos: {count}")

        # Discovery query distribution
        by_query: Dict[str, int] = {}
        for ch in channels:
            q = ch.get('discovery_keyword', 'Unknown')
            by_query[q] = by_query.get(q, 0) + 1

        logger.info("  By discovery query:")
        for q, count in sorted(by_query.items(), key=lambda x: -x[1])[:10]:
            logger.info(f"    {q}: {count}")

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
