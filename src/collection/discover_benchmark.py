"""
discover_benchmark.py
---------------------
Stream B: Algorithm Favorites (Benchmark)

Discovers established channels that YouTube's algorithm surfaces prominently.
Uses vowel searches (a, e, i, o, u) which return algorithm-favored content.

This stream serves as a benchmark for typical "successful" YouTube channels
to compare against new creator trajectories.

Target: 2,000 channels
Method: Vowel search (algorithm favorites)
Filter: None (any age channel)

Usage:
    python -m src.collection.discover_benchmark [--test] [--limit N]

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
from typing import Dict, List, Set

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
        logging.FileHandler(config.LOGS_DIR / f'discover_benchmark_{config.get_date_stamp()}.log')
    ]
)
logger = logging.getLogger(__name__)


def discover_benchmark_channels(
    youtube,
    target_count: int = 2000,
    test_mode: bool = False
) -> List[Dict]:
    """
    Discover algorithm-favored channels via vowel search.
    
    Args:
        youtube: Authenticated YouTube API service
        target_count: Target number of channels to collect
        test_mode: If True, uses reduced targets for testing
        
    Returns:
        List of channel data dictionaries
    """
    if test_mode:
        target_count = min(target_count, 50)
        logger.info("🧪 TEST MODE: Limited to 50 channels")
    
    channels_by_id: Dict[str, Dict] = {}
    seen_channel_ids: Set[str] = set()
    
    # Use benchmark queries (vowels)
    queries = config.BENCHMARK_QUERIES
    per_query_target = target_count // len(queries)
    
    logger.info(f"🎯 Target: {target_count} channels")
    logger.info(f"📝 Queries: {queries}")
    logger.info(f"📊 Per-query target: {per_query_target}")
    
    # Recent time window (last 30 days of video uploads)
    now = datetime.utcnow()
    published_after = (now - timedelta(days=30)).isoformat() + 'Z'
    published_before = now.isoformat() + 'Z'
    
    for idx, query in enumerate(queries):
        if len(channels_by_id) >= target_count:
            logger.info(f"✅ Reached target of {target_count} channels")
            break
            
        logger.info(f"[{idx+1}/{len(queries)}] Searching: '{query}'")
        
        try:
            # Search with relevance order (algorithm favorites)
            search_results = search_videos_paginated(
                youtube=youtube,
                query=query,
                published_after=published_after,
                published_before=published_before,
                max_pages=5 if test_mode else 20,
                order="relevance"  # Algorithm favorites
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
                
            # Get full channel details (no date filter for benchmark)
            channel_details = get_channel_full_details(
                youtube=youtube,
                channel_ids=new_channel_ids[:per_query_target],  # Limit per query
                stream_type="stream_b",
                discovery_language="global",
                discovery_keyword=query
            )
            
            for channel in channel_details:
                cid = channel['channel_id']
                if cid not in channels_by_id:
                    channels_by_id[cid] = channel
                    seen_channel_ids.add(cid)
                    
            logger.info(f"  → Found {len(channel_details)} channels "
                       f"(total: {len(channels_by_id)})")
            
        except Exception as e:
            logger.error(f"  ⚠️ Error searching '{query}': {e}")
            continue
    
    channels = list(channels_by_id.values())
    logger.info(f"✅ Discovery complete: {len(channels)} total channels")
    
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
    """Main entry point for Stream B collection."""
    parser = argparse.ArgumentParser(description="Stream B: Algorithm Favorites (Benchmark)")
    parser.add_argument('--test', action='store_true', help='Run in test mode (50 channels)')
    parser.add_argument('--limit', type=int, default=2000, help='Target channel count')
    args = parser.parse_args()
    
    config.ensure_directories()
    
    logger.info("=" * 60)
    logger.info("🚀 STREAM B: ALGORITHM FAVORITES (BENCHMARK)")
    logger.info("=" * 60)
    
    try:
        youtube = get_authenticated_service()
        logger.info("✅ Authenticated with YouTube API")
        
        channels = discover_benchmark_channels(
            youtube=youtube,
            target_count=args.limit,
            test_mode=args.test
        )
        
        if not channels:
            logger.warning("⚠️ No channels discovered!")
            return
        
        output_path = config.get_output_path("stream_b", "initial")
        save_channels_to_csv(channels, output_path)
        
        logger.info("=" * 60)
        logger.info("📊 COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total channels: {len(channels)}")
        
        # Stats by subscriber tier
        tiers = {'<1K': 0, '1K-10K': 0, '10K-100K': 0, '100K-1M': 0, '>1M': 0}
        for ch in channels:
            subs = ch.get('subscriber_count', 0) or 0
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
        logger.error(f"❌ Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()

