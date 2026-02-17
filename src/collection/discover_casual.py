"""
discover_casual.py
------------------
Stream D: Casual Uploaders (Amateur Control Group)

Discovers channels that upload with default/unedited file names, indicating
casual or amateur uploading behavior (IMG_, MVI_, DSC_, etc.).

This serves as a control group for creators who are not treating YouTube
as a serious entrepreneurial endeavor.

Target: 25,000 channels
Method: Raw file name queries
Filter: None (any age channel)

Usage:
    python -m src.collection.discover_casual [--test] [--limit N]

Author: Katie Apker
Last Updated: Feb 02, 2026
"""

import argparse
import csv
import logging
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

logger = logging.getLogger(__name__)


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


def discover_casual_channels(
    youtube,
    target_count: int = 25000,
    test_mode: bool = False
) -> List[Dict]:
    """
    Discover casual uploaders using raw file name patterns.
    
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
    
    # Use casual queries (raw file patterns)
    queries = config.CASUAL_QUERIES
    per_query_target = target_count // len(queries)
    
    logger.info(f"🎯 Target: {target_count} channels")
    logger.info(f"📝 Queries: {queries}")
    logger.info(f"📊 Per-query target: {per_query_target}")
    
    # Recent time window (last 30 days)
    now = datetime.utcnow()
    published_after = (now - timedelta(days=30)).isoformat() + 'Z'
    published_before = now.isoformat() + 'Z'
    
    for idx, query in enumerate(queries):
        if len(channels_by_id) >= target_count:
            logger.info(f"✅ Reached target of {target_count} channels")
            break
            
        logger.info(f"[{idx+1}/{len(queries)}] Searching: '{query}'")
        
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
                continue
                
            channel_ids = extract_channel_ids_from_search(search_results)
            new_channel_ids = [
                cid for cid in channel_ids 
                if cid not in seen_channel_ids
            ]
            
            if not new_channel_ids:
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
                    query_channels += 1
                    
            logger.info(f"  → Found {query_channels} new channels "
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
    """Main entry point for Stream D collection."""
    parser = argparse.ArgumentParser(description="Stream D: Casual Uploaders")
    parser.add_argument('--test', action='store_true', help='Run in test mode (100 channels)')
    parser.add_argument('--limit', type=int, default=25000, help='Target channel count')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    logger.info("=" * 60)
    logger.info("🚀 STREAM D: CASUAL UPLOADERS (AMATEUR)")
    logger.info("=" * 60)
    
    try:
        youtube = get_authenticated_service()
        logger.info("✅ Authenticated with YouTube API")
        
        channels = discover_casual_channels(
            youtube=youtube,
            target_count=args.limit,
            test_mode=args.test
        )
        
        if not channels:
            logger.warning("⚠️ No channels discovered!")
            return
        
        output_path = config.get_output_path("stream_d", "initial")
        save_channels_to_csv(channels, output_path)
        
        logger.info("=" * 60)
        logger.info("📊 COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total channels: {len(channels)}")
        
        # Distribution by video count (casualness indicator)
        video_buckets = {'1 video': 0, '2-5': 0, '6-20': 0, '21-100': 0, '>100': 0}
        
        for ch in channels:
            vids = ch.get('video_count', 0) or 0
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
        by_query = {}
        for ch in channels:
            q = ch.get('discovery_keyword', 'Unknown')
            by_query[q] = by_query.get(q, 0) + 1
            
        logger.info("  By discovery query:")
        for q, count in sorted(by_query.items(), key=lambda x: -x[1])[:5]:
            logger.info(f"    {q}: {count}")
            
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()

