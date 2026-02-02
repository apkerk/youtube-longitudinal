"""
discover_intent.py
------------------
Stream A: Intent Creators Collection

Discovers new YouTube channels created in 2026 that are intentionally starting
their creator journey. Uses intent keywords across 8 languages to find channels
that explicitly introduce themselves ("Welcome to my channel", "My first video").

Target: 200,000 channels
Languages: Hindi, English, Spanish, Japanese, German, Portuguese, Korean, French
Filter: Channel created >= Jan 1, 2026

Usage:
    python -m src.collection.discover_intent [--test] [--limit N]

Author: Katie Apker
Last Updated: Feb 02, 2026
"""

import argparse
import csv
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOGS_DIR / f'discover_intent_{config.get_date_stamp()}.log')
    ]
)
logger = logging.getLogger(__name__)


def discover_intent_channels(
    youtube,
    target_count: int = 200000,
    test_mode: bool = False
) -> List[Dict]:
    """
    Discover intent-signaling new creators across 8 languages.
    
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
    
    # All discovered channels (keyed by channel_id to deduplicate)
    channels_by_id: Dict[str, Dict] = {}
    
    # Track channel IDs we've already processed
    seen_channel_ids: Set[str] = set()
    
    # Calculate time windows for searching (rolling 24-48 hour windows)
    # This helps find newer channels that haven't been buried by algorithm
    time_windows = generate_time_windows()
    
    # Get all intent keywords as (keyword, language) tuples
    intent_keywords = config.get_all_intent_keywords()
    
    # Calculate per-keyword target
    per_keyword_target = max(10, target_count // len(intent_keywords))
    
    logger.info(f"🎯 Target: {target_count} channels")
    logger.info(f"📝 Keywords: {len(intent_keywords)} across 8 languages")
    logger.info(f"📊 Per-keyword target: {per_keyword_target}")
    
    # Iterate through keywords
    for idx, (keyword, language) in enumerate(intent_keywords):
        if len(channels_by_id) >= target_count:
            logger.info(f"✅ Reached target of {target_count} channels")
            break
            
        logger.info(f"[{idx+1}/{len(intent_keywords)}] Searching: '{keyword}' ({language})")
        
        keyword_channels = 0
        
        # Search across multiple time windows
        for window_start, window_end in time_windows:
            if keyword_channels >= per_keyword_target:
                break
                
            try:
                # Search for videos with this keyword
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
                    stream_type="stream_a",
                    discovery_language=language,
                    discovery_keyword=keyword
                )
                
                # Filter to channels created in 2026+
                new_channels = filter_channels_by_date(
                    channels=channel_details,
                    cutoff_date=config.COHORT_CUTOFF_DATE
                )
                
                # Add to collection
                for channel in new_channels:
                    cid = channel['channel_id']
                    if cid not in channels_by_id:
                        channels_by_id[cid] = channel
                        seen_channel_ids.add(cid)
                        keyword_channels += 1
                        
                logger.info(f"  → Found {len(new_channels)} new 2026+ channels "
                           f"(total: {len(channels_by_id)})")
                
            except Exception as e:
                logger.error(f"  ⚠️ Error searching '{keyword}': {e}")
                continue
    
    channels = list(channels_by_id.values())
    logger.info(f"✅ Discovery complete: {len(channels)} total channels")
    
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
    
    # Go back 30 days in 48-hour overlapping windows
    for days_back in range(0, 30, 2):
        window_end = now - timedelta(days=days_back)
        window_start = window_end - timedelta(hours=48)
        
        # Only include windows that start after cohort cutoff
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
    logger.info(f"📹 Enriching {len(channels)} channels with first video data...")
    
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
                
    logger.info(f"✅ Enriched {enriched} channels with first video data")
    return channels


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
            
    logger.info(f"💾 Saved {len(channels)} channels to {output_path}")


def main():
    """Main entry point for Stream A collection."""
    parser = argparse.ArgumentParser(description="Stream A: Intent Creators Collection")
    parser.add_argument('--test', action='store_true', help='Run in test mode (100 channels)')
    parser.add_argument('--limit', type=int, default=200000, help='Target channel count')
    parser.add_argument('--skip-first-video', action='store_true', 
                        help='Skip first video enrichment (saves API quota)')
    args = parser.parse_args()
    
    # Ensure directories exist
    config.ensure_directories()
    
    logger.info("=" * 60)
    logger.info("🚀 STREAM A: INTENT CREATORS COLLECTION")
    logger.info("=" * 60)
    
    try:
        # Authenticate
        youtube = get_authenticated_service()
        logger.info("✅ Authenticated with YouTube API")
        
        # Discover channels
        channels = discover_intent_channels(
            youtube=youtube,
            target_count=args.limit,
            test_mode=args.test
        )
        
        if not channels:
            logger.warning("⚠️ No channels discovered!")
            return
        
        # Optionally enrich with first video
        if not args.skip_first_video:
            channels = enrich_with_first_video(youtube, channels)
        
        # Save to CSV
        output_path = config.get_output_path("stream_a", "initial")
        save_channels_to_csv(channels, output_path)
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total channels: {len(channels)}")
        
        # Count by language
        by_language = {}
        for ch in channels:
            lang = ch.get('discovery_language', 'Unknown')
            by_language[lang] = by_language.get(lang, 0) + 1
        
        for lang, count in sorted(by_language.items(), key=lambda x: -x[1]):
            logger.info(f"  {lang}: {count}")
            
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()

