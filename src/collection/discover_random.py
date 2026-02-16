"""
discover_random.py
------------------
Stream C: Searchable Random Sample

Discovers a quasi-random sample of YouTube channels using random prefix
sampling (Zhou et al., 2011). Generates random 3-character prefixes and
searches for videos matching those strings.

This provides a diverse sample for population-level comparisons, though
biased toward searchable/discoverable content.

Target: 50,000 channels
Method: Random prefix sampling (3 chars: a-z, 0-9)
Filter: None (any age channel)

Usage:
    python -m src.collection.discover_random [--test] [--limit N]

Author: Katie Apker
Last Updated: Feb 02, 2026
"""

import argparse
import csv
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Generator

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
        logging.FileHandler(config.LOGS_DIR / f'discover_random_{config.get_date_stamp()}.log')
    ]
)
logger = logging.getLogger(__name__)


def generate_random_prefix(length: int = 3) -> str:
    """
    Generate a random prefix string.
    
    Args:
        length: Number of characters in prefix
        
    Returns:
        Random string of alphanumeric characters
    """
    chars = config.RANDOM_PREFIX_CHARS
    return ''.join(random.choice(chars) for _ in range(length))


def prefix_generator(target_count: int, chars_per_prefix: int = 3) -> Generator[str, None, None]:
    """
    Generate unique random prefixes until target is reached.
    
    Args:
        target_count: Approximate number of prefixes needed
        chars_per_prefix: Characters per prefix
        
    Yields:
        Unique random prefix strings
    """
    generated = set()
    attempts = 0
    max_attempts = target_count * 10
    
    while len(generated) < target_count and attempts < max_attempts:
        prefix = generate_random_prefix(chars_per_prefix)
        if prefix not in generated:
            generated.add(prefix)
            yield prefix
        attempts += 1


def discover_random_channels(
    youtube,
    target_count: int = 50000,
    test_mode: bool = False
) -> List[Dict]:
    """
    Discover channels using random prefix sampling.
    
    Args:
        youtube: Authenticated YouTube API service
        target_count: Target number of channels to collect
        test_mode: If True, uses reduced targets for testing
        
    Returns:
        List of channel data dictionaries
    """
    if test_mode:
        target_count = min(target_count, 100)
        logger.info("🧪 TEST MODE: Limited to 100 channels")
    
    channels_by_id: Dict[str, Dict] = {}
    seen_channel_ids: Set[str] = set()
    
    # Estimate prefixes needed (assuming ~10-30 channels per prefix)
    estimated_prefixes = target_count // 15
    
    logger.info(f"🎯 Target: {target_count} channels")
    logger.info(f"📝 Estimated prefixes needed: {estimated_prefixes}")
    
    # Recent time window
    now = datetime.utcnow()
    published_after = (now - timedelta(days=90)).isoformat() + 'Z'
    published_before = now.isoformat() + 'Z'
    
    prefix_count = 0
    
    for prefix in prefix_generator(estimated_prefixes * 2):  # Buffer for failures
        if len(channels_by_id) >= target_count:
            logger.info(f"✅ Reached target of {target_count} channels")
            break
            
        prefix_count += 1
        
        if prefix_count % 50 == 0:
            logger.info(f"[Prefix {prefix_count}] Total channels: {len(channels_by_id)}")
            
        try:
            # Search with random prefix
            search_results = search_videos_paginated(
                youtube=youtube,
                query=prefix,
                published_after=published_after,
                published_before=published_before,
                max_pages=1 if test_mode else 3,
                order="date"  # Diverse by recency
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
                
            # Limit batch size for efficiency
            batch_ids = new_channel_ids[:30]
            
            channel_details = get_channel_full_details(
                youtube=youtube,
                channel_ids=batch_ids,
                stream_type="stream_c",
                discovery_language="global",
                discovery_keyword=prefix
            )
            
            for channel in channel_details:
                cid = channel['channel_id']
                if cid not in channels_by_id:
                    channels_by_id[cid] = channel
                    seen_channel_ids.add(cid)
            
        except Exception as e:
            logger.error(f"  ⚠️ Error searching '{prefix}': {e}")
            continue
    
    channels = list(channels_by_id.values())
    logger.info(f"✅ Discovery complete: {len(channels)} total channels")
    logger.info(f"📊 Prefixes used: {prefix_count}")
    
    return channels


def save_channels_to_csv(channels: List[Dict], output_path: Path) -> None:
    """Save channel data to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
        writer.writeheader()
        
        for channel in channels:
            row = {field: channel.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
            writer.writerow(row)
            
    logger.info(f"💾 Saved {len(channels)} channels to {output_path}")


def main():
    """Main entry point for Stream C collection."""
    parser = argparse.ArgumentParser(description="Stream C: Searchable Random Sample")
    parser.add_argument('--test', action='store_true', help='Run in test mode (100 channels)')
    parser.add_argument('--limit', type=int, default=50000, help='Target channel count')
    args = parser.parse_args()
    
    config.ensure_directories()
    
    logger.info("=" * 60)
    logger.info("🚀 STREAM C: SEARCHABLE RANDOM SAMPLE")
    logger.info("=" * 60)
    
    try:
        youtube = get_authenticated_service()
        logger.info("✅ Authenticated with YouTube API")
        
        channels = discover_random_channels(
            youtube=youtube,
            target_count=args.limit,
            test_mode=args.test
        )
        
        if not channels:
            logger.warning("⚠️ No channels discovered!")
            return
        
        output_path = config.get_output_path("stream_c", "initial")
        save_channels_to_csv(channels, output_path)
        
        logger.info("=" * 60)
        logger.info("📊 COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total channels: {len(channels)}")
        
        # Distribution by channel age
        now = datetime.utcnow()
        age_buckets = {'<30d': 0, '30d-1y': 0, '1y-5y': 0, '>5y': 0}
        
        for ch in channels:
            pub = ch.get('published_at')
            if pub:
                try:
                    pub_date = datetime.fromisoformat(pub.replace('Z', '+00:00'))
                    age_days = (now - pub_date.replace(tzinfo=None)).days
                    
                    if age_days < 30:
                        age_buckets['<30d'] += 1
                    elif age_days < 365:
                        age_buckets['30d-1y'] += 1
                    elif age_days < 365 * 5:
                        age_buckets['1y-5y'] += 1
                    else:
                        age_buckets['>5y'] += 1
                except:
                    pass
                    
        for bucket, count in age_buckets.items():
            logger.info(f"  Age {bucket}: {count}")
            
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()

