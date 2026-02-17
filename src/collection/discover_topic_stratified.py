"""
discover_topic_stratified.py
----------------------------
Topic-Stratified Discovery — channels sampled across YouTube's topic categories.

Current streams discover channels through keyword searches, which bias toward
certain content types. Topic stratification ensures representation across
categories that keyword searches miss (e.g., automotive, pets, sports).

Cycles through all topic IDs in config.YOUTUBE_PARENT_TOPICS using the topicId
search parameter. Allocates proportionally across topics to build a balanced
sample.

Supports checkpoint/resume: progress is saved after each topic batch so
interrupted runs can continue without re-consuming API quota.

Target: 30-40,000 channels
Method: search.list(topicId=X, type=video, order=date) across all topic categories
Filter: None (any age channel)

Usage:
    python -m src.collection.discover_topic_stratified [--test] [--limit N]

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

CHECKPOINT_PATH = config.STREAM_DIRS["topic_stratified"] / ".discovery_checkpoint.json"


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'discover_topic_stratified_{config.get_date_stamp()}.log'

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
    completed_topics: Set[str] = set()
    channels_by_id: Dict[str, Dict] = {}

    if not CHECKPOINT_PATH.exists():
        return completed_topics, channels_by_id

    with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
        ckpt = json.load(f)

    completed_topics = set(ckpt.get("completed_queries", []))

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
        f"{len(completed_topics)} topics completed"
    )
    return completed_topics, channels_by_id


def save_checkpoint(completed_topics: Set[str], output_path: Path, channel_count: int) -> None:
    """Save discovery checkpoint."""
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "completed_queries": list(completed_topics),
            "output_path": str(output_path),
            "channel_count": channel_count,
            "timestamp": datetime.utcnow().isoformat(),
        }, f)


def clear_checkpoint() -> None:
    """Remove checkpoint file after successful completion."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared")


def discover_topic_stratified_channels(
    youtube,
    target_count: int = 40000,
    test_mode: bool = False,
    output_path: Optional[Path] = None,
) -> List[Dict]:
    """
    Discover channels stratified across YouTube topic categories.

    Iterates through all topic IDs in YOUTUBE_PARENT_TOPICS, allocating a
    proportional per-topic target. For each topic, searches for recent videos
    with that topicId and extracts unique channels.

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

    completed_topics, channels_by_id = load_checkpoint(output_path)
    seen_channel_ids: Set[str] = set(channels_by_id.keys())

    if not completed_topics:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
            writer.writeheader()

    # Build topic list from config
    topics = list(config.YOUTUBE_PARENT_TOPICS.items())  # [(topic_id, topic_name), ...]
    num_topics = len(topics)
    per_topic_target = max(50, target_count // num_topics)

    # Recent time window (last 90 days for diversity)
    now = datetime.utcnow()
    published_after = (now - timedelta(days=90)).isoformat() + 'Z'
    published_before = now.isoformat() + 'Z'

    logger.info(f"Target: {target_count} channels")
    logger.info(f"Topics: {num_topics}")
    logger.info(f"Per-topic target: {per_topic_target}")
    logger.info(f"Already collected: {len(channels_by_id)} channels")

    for idx, (topic_id, topic_name) in enumerate(topics):
        if len(channels_by_id) >= target_count:
            logger.info(f"Reached target of {target_count} channels")
            break

        if topic_id in completed_topics:
            continue

        logger.info(f"[{idx+1}/{num_topics}] Topic: {topic_name} ({topic_id})")

        batch_new_channels: List[Dict] = []

        try:
            # Search with topicId — no query string needed
            search_results = search_videos_paginated(
                youtube=youtube,
                published_after=published_after,
                published_before=published_before,
                max_pages=2 if test_mode else 10,
                order="date",
                topicId=topic_id,
            )

            if not search_results:
                logger.info(f"  No results for topic {topic_name}")
                completed_topics.add(topic_id)
                save_checkpoint(completed_topics, output_path, len(channels_by_id))
                continue

            channel_ids = extract_channel_ids_from_search(search_results)
            new_channel_ids = [
                cid for cid in channel_ids
                if cid not in seen_channel_ids
            ]

            if not new_channel_ids:
                completed_topics.add(topic_id)
                save_checkpoint(completed_topics, output_path, len(channels_by_id))
                continue

            # Cap per topic for balance
            batch_ids = new_channel_ids[:per_topic_target]

            channel_details = get_channel_full_details(
                youtube=youtube,
                channel_ids=batch_ids,
                stream_type="topic_stratified",
                discovery_language="global",
                discovery_keyword=f"topicId={topic_name}"
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
            logger.error(f"  Error for topic {topic_name}: {e}")

        if batch_new_channels:
            with open(output_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
                for ch in batch_new_channels:
                    row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
                    writer.writerow(row)

        completed_topics.add(topic_id)
        save_checkpoint(completed_topics, output_path, len(channels_by_id))

    clear_checkpoint()

    channels = list(channels_by_id.values())
    logger.info(f"Discovery complete: {len(channels)} total channels")
    return channels


def main():
    """Main entry point for Topic-Stratified collection."""
    parser = argparse.ArgumentParser(description="Topic-Stratified Discovery")
    parser.add_argument('--test', action='store_true', help='Run in test mode (50 channels)')
    parser.add_argument('--limit', type=int, default=40000, help='Target channel count')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    logger.info("=" * 60)
    logger.info("TOPIC-STRATIFIED DISCOVERY")
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        output_path = config.get_output_path("topic_stratified", "initial")

        channels = discover_topic_stratified_channels(
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

        # Topic distribution (core metric for this stream)
        by_topic: Dict[str, int] = {}
        for ch in channels:
            kw = ch.get('discovery_keyword', 'Unknown')
            by_topic[kw] = by_topic.get(kw, 0) + 1

        logger.info(f"  Channels across {len(by_topic)} topics:")
        for topic, count in sorted(by_topic.items(), key=lambda x: -x[1]):
            logger.info(f"    {topic}: {count}")

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
