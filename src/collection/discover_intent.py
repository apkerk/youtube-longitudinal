"""
discover_intent.py
------------------
Stream A: Intent Creators Collection

Discovers new YouTube channels created in 2026 that are intentionally starting
their creator journey. Uses intent keywords across 8 languages to find channels
that explicitly introduce themselves ("Welcome to my channel", "My first video").

Supports checkpoint/resume: progress is saved after each keyword batch so
interrupted runs can continue without re-consuming API quota.

Target: 200,000 channels
Languages: Hindi, English, Spanish, Japanese, German, Portuguese, Korean, French
Filter: Channel created >= Jan 1, 2026

Usage:
    python -m src.collection.discover_intent [--test] [--limit N] [--skip-first-video]

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
from typing import Dict, List, Set, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    search_videos_paginated,
    extract_channel_ids_from_search,
    get_channel_full_details,
    get_oldest_video,
    filter_channels_by_date,
)
import config

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'discover_intent_{config.get_date_stamp()}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

CHECKPOINT_PATH = config.STREAM_DIRS["stream_a"] / ".discovery_checkpoint.json"


def load_checkpoint(output_path: Path) -> tuple:
    """
    Load discovery checkpoint and rebuild state from partial CSV.

    Returns:
        Tuple of (completed_keyword_keys, channels_by_id)
    """
    completed_keywords: Set[str] = set()
    channels_by_id: Dict[str, Dict] = {}

    if not CHECKPOINT_PATH.exists():
        return completed_keywords, channels_by_id

    with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
        ckpt = json.load(f)

    completed_keywords = set(ckpt.get("completed_keywords", []))

    # Rebuild channel state from partial output CSV
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
        f"{len(completed_keywords)} keywords completed"
    )
    return completed_keywords, channels_by_id


def save_checkpoint(completed_keywords: Set[str], output_path: Path, channel_count: int) -> None:
    """Save discovery checkpoint."""
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "completed_keywords": list(completed_keywords),
            "output_path": str(output_path),
            "channel_count": channel_count,
            "timestamp": datetime.utcnow().isoformat(),
        }, f)


def clear_checkpoint() -> None:
    """Remove checkpoint file after successful completion."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared")


def discover_intent_channels(
    youtube,
    target_count: int = 200000,
    test_mode: bool = False,
    output_path: Optional[Path] = None,
) -> List[Dict]:
    """
    Discover intent-signaling new creators across 8 languages.

    Writes channels incrementally to output_path after each keyword batch.
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
    completed_keywords, channels_by_id = load_checkpoint(output_path)
    seen_channel_ids: Set[str] = set(channels_by_id.keys())

    # If fresh start, write CSV header
    if not completed_keywords:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
            writer.writeheader()

    # Generate time windows and keywords
    time_windows = generate_time_windows()
    intent_keywords = config.get_all_intent_keywords()

    per_keyword_target = max(10, target_count // len(intent_keywords))

    logger.info(f"Target: {target_count} channels")
    logger.info(f"Keywords: {len(intent_keywords)} across 8 languages")
    logger.info(f"Per-keyword target: {per_keyword_target}")
    logger.info(f"Already collected: {len(channels_by_id)} channels")

    for idx, (keyword, language) in enumerate(intent_keywords):
        if len(channels_by_id) >= target_count:
            logger.info(f"Reached target of {target_count} channels")
            break

        keyword_key = f"{keyword}|{language}"
        if keyword_key in completed_keywords:
            continue

        logger.info(f"[{idx+1}/{len(intent_keywords)}] Searching: '{keyword}' ({language})")

        batch_new_channels: List[Dict] = []
        keyword_channels = 0

        for window_start, window_end in time_windows:
            if keyword_channels >= per_keyword_target:
                break

            try:
                search_results = search_videos_paginated(
                    youtube=youtube,
                    query=keyword,
                    published_after=window_start,
                    published_before=window_end,
                    max_pages=3 if test_mode else 10,
                    order="date"
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
                    stream_type="stream_a",
                    discovery_language=language,
                    discovery_keyword=keyword
                )

                new_channels = filter_channels_by_date(
                    channels=channel_details,
                    cutoff_date=config.COHORT_CUTOFF_DATE
                )

                for channel in new_channels:
                    cid = channel['channel_id']
                    if cid not in channels_by_id:
                        channels_by_id[cid] = channel
                        seen_channel_ids.add(cid)
                        batch_new_channels.append(channel)
                        keyword_channels += 1

                logger.info(f"  Found {len(new_channels)} new 2026+ channels "
                           f"(total: {len(channels_by_id)})")

            except Exception as e:
                logger.error(f"  Error searching '{keyword}': {e}")
                continue

        # Append this keyword's new channels to CSV
        if batch_new_channels:
            with open(output_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
                for ch in batch_new_channels:
                    row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
                    writer.writerow(row)

        # Save checkpoint after this keyword
        completed_keywords.add(keyword_key)
        save_checkpoint(completed_keywords, output_path, len(channels_by_id))

    clear_checkpoint()

    channels = list(channels_by_id.values())
    logger.info(f"Discovery complete: {len(channels)} total channels")
    return channels


def generate_time_windows() -> List[tuple]:
    """
    Generate time windows for searching.
    Uses overlapping 48-hour windows going back 30 days.

    Returns:
        List of (start_iso, end_iso) tuples
    """
    windows = []
    now = datetime.utcnow()

    for days_back in range(0, 30, 2):
        window_end = now - timedelta(days=days_back)
        window_start = window_end - timedelta(hours=48)

        cutoff = datetime.fromisoformat(config.COHORT_CUTOFF_DATE)
        if window_start >= cutoff:
            windows.append((
                window_start.isoformat() + 'Z',
                window_end.isoformat() + 'Z'
            ))

    return windows


def enrich_with_first_video(youtube, channels: List[Dict]) -> List[Dict]:
    """
    Enrich channel data with first video information.

    Note: This is expensive (1 API call per channel minimum).
    Only run for initial collection, not sweeps.

    Args:
        youtube: Authenticated YouTube API service
        channels: List of channel dictionaries

    Returns:
        Channels with first_video_date/id/title populated
    """
    logger.info(f"Enriching {len(channels)} channels with first video data...")

    enriched = 0
    for idx, channel in enumerate(channels):
        if idx % 100 == 0:
            logger.info(f"  Progress: {idx}/{len(channels)}")

        uploads_playlist = channel.get('uploads_playlist_id')
        if uploads_playlist:
            oldest = get_oldest_video(youtube, uploads_playlist)
            if oldest:
                channel['first_video_date'] = oldest.get('first_video_date')
                channel['first_video_id'] = oldest.get('first_video_id')
                channel['first_video_title'] = oldest.get('first_video_title')
                enriched += 1

    logger.info(f"Enriched {enriched} channels with first video data")
    return channels


def save_channels_to_csv(channels: List[Dict], output_path: Path) -> None:
    """
    Save channel data to CSV file (full write, overwrites existing).

    Args:
        channels: List of channel dictionaries
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
        writer.writeheader()

        for channel in channels:
            row = {field: channel.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
            writer.writerow(row)

    logger.info(f"Saved {len(channels)} channels to {output_path}")


def main():
    """Main entry point for Stream A collection."""
    parser = argparse.ArgumentParser(description="Stream A: Intent Creators Collection")
    parser.add_argument('--test', action='store_true', help='Run in test mode (100 channels)')
    parser.add_argument('--limit', type=int, default=200000, help='Target channel count')
    parser.add_argument('--skip-first-video', action='store_true',
                        help='Skip first video enrichment (saves API quota)')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    logger.info("=" * 60)
    logger.info("STREAM A: INTENT CREATORS COLLECTION")
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        # Determine output path upfront (needed for checkpoint)
        output_path = config.get_output_path("stream_a", "initial")

        # Discover channels (writes incrementally with checkpoint)
        channels = discover_intent_channels(
            youtube=youtube,
            target_count=args.limit,
            test_mode=args.test,
            output_path=output_path,
        )

        if not channels:
            logger.warning("No channels discovered!")
            return

        # Optionally enrich with first video (requires full CSV rewrite)
        if not args.skip_first_video:
            channels = enrich_with_first_video(youtube, channels)
            save_channels_to_csv(channels, output_path)

        # Summary
        logger.info("=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total channels: {len(channels)}")

        by_language = {}
        for ch in channels:
            lang = ch.get('discovery_language', 'Unknown')
            by_language[lang] = by_language.get(lang, 0) + 1

        for lang, count in sorted(by_language.items(), key=lambda x: -x[1]):
            logger.info(f"  {lang}: {count}")

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
