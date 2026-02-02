"""
discover_amateur.py
-------------------
Stream D: The "Amateur/Casual" Baseline
Method: Raw File Query Search (IMG, MVI, DSC, MOV, VID_)
Goal: Find ~30k casual/amateur uploads per day as a "zero-effort" baseline.

Rationale:
- Many casual users upload videos with default camera filenames
- These represent uploads with NO SEO optimization or strategic intent
- Provides contrast to Stream A (intentional) and Stream B (algorithm favorites)
- Median views ~214 (vs 1.16M for vowel search) - captures true long tail

Experimental Validation:
- EXP-003 (Feb 02, 2026): Raw/Amateur queries showed 59% big channel rate
  vs 94% for vowel search, confirming reduced algorithmic bias

Usage:
    python discover_amateur.py --batches 100
    
Quota Cost: ~4 units per channel (search + check)
"""

import os
import sys
import argparse
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from tqdm import tqdm

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import youtube_api


# --- CONFIGURATION ---
# Raw file prefixes from common cameras and phones
RAW_FILE_QUERIES = [
    # Camera defaults
    "IMG_",      # iPhone, many cameras
    "MVI_",      # Canon video
    "DSC_",      # Sony, Nikon
    "MOV_",      # QuickTime
    "VID_",      # Android
    "DSCF",      # Fujifilm
    "P_",        # Some Android phones
    "GOPR",      # GoPro
    "DJI_",      # DJI drones
    
    # Screen recordings (common casual uploads)
    "Screen Recording",
    "Untitled",
    "New Recording",
    
    # Date-based defaults (common pattern)
    "20260",     # Catches 2026-01-XX style filenames
    "video_2026",
]


def search_amateur_videos(
    youtube,
    query: str,
    start_time: str,
    end_time: str,
    max_results: int = 50
) -> List[Dict]:
    """
    Search for videos using raw file queries.
    
    Args:
        youtube: Authenticated YouTube API service
        query: The raw file prefix to search for
        start_time: ISO format start time
        end_time: ISO format end time
        max_results: Maximum results per query
        
    Returns:
        List of video items from API response
    """
    videos = []
    
    try:
        request = youtube.search().list(
            part="snippet",
            type="video",
            q=query,
            publishedAfter=start_time,
            publishedBefore=end_time,
            order="date",  # Chronological to avoid popularity bias
            maxResults=max_results,
            regionCode=None  # Global search for amateur content
        )
        response = youtube_api.execute_request(request)
        videos = response.get('items', [])
        
    except Exception as e:
        print(f"Error searching '{query}': {e}")
        
    return videos


def get_channel_stats(youtube, channel_ids: List[str]) -> List[Dict]:
    """
    Get basic stats for channels. No filtering - we want ALL amateur content.
    
    Args:
        youtube: Authenticated YouTube API service
        channel_ids: List of channel IDs to check
        
    Returns:
        List of channel data dictionaries
    """
    data_list = []
    unique_ids = list(set(channel_ids))
    
    for chunk in youtube_api.chunks(unique_ids, 50):
        try:
            request = youtube.channels().list(
                part="snippet,statistics",
                id=",".join(chunk)
            )
            response = youtube_api.execute_request(request)
            
            for item in response.get('items', []):
                stats = item['statistics']
                snippet = item['snippet']
                
                data = {
                    'channel_id': item['id'],
                    'title': snippet.get('title'),
                    'published_at': snippet.get('publishedAt'),
                    'video_count': int(stats.get('videoCount', 0)),
                    'view_count': int(stats.get('viewCount', 0)),
                    'sub_count': int(stats.get('subscriberCount', 0)),
                    'country': snippet.get('country'),
                    'scraped_at': datetime.utcnow().isoformat(),
                    'stream_type': 'amateur_baseline',
                    'discovery_method': 'raw_file_query'
                }
                data_list.append(data)
                
        except Exception as e:
            print(f"Error fetching channel stats: {e}")
            
    return data_list


def main():
    parser = argparse.ArgumentParser(
        description="Discover Amateur/Casual Channels (Stream D)"
    )
    parser.add_argument(
        "--batches",
        type=int,
        default=50,
        help="Number of search batches to run (default: 50)"
    )
    parser.add_argument(
        "--hours_back",
        type=int,
        default=24,
        help="Hours back to search from now (default: 24)"
    )
    args = parser.parse_args()
    
    print("🎬 STARTING AMATEUR DISCOVERY (Stream D)")
    print("=" * 50)
    print(f"Batches: {args.batches}")
    print(f"Window: Last {args.hours_back} hours")
    print(f"Queries: {len(RAW_FILE_QUERIES)} raw file patterns")
    
    # Estimate quota
    est_quota = args.batches * (100 + 2)  # search + channel check per batch
    print(f"Estimated quota: ~{est_quota:,} units")
    print("=" * 50)
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"❌ FATAL: {e}")
        return
    
    # Define time window
    now = datetime.utcnow()
    start_time = (now - timedelta(hours=args.hours_back)).isoformat() + "Z"
    end_time = now.isoformat() + "Z"
    
    print(f"\n🔎 Scanning Window: {start_time} -> {end_time}")
    
    all_channels = []
    query_stats = {}
    
    for batch_num in tqdm(range(args.batches), desc="Sampling"):
        # Rotate through queries randomly
        query = random.choice(RAW_FILE_QUERIES)
        
        # Search for videos
        videos = search_amateur_videos(youtube, query, start_time, end_time)
        
        if not videos:
            continue
        
        # Track query performance
        if query not in query_stats:
            query_stats[query] = {'searches': 0, 'videos': 0, 'channels': 0}
        query_stats[query]['searches'] += 1
        query_stats[query]['videos'] += len(videos)
        
        # Extract channel IDs
        channel_ids = [v['snippet']['channelId'] for v in videos]
        
        # Get channel stats (no filtering)
        batch_data = get_channel_stats(youtube, channel_ids)
        query_stats[query]['channels'] += len(batch_data)
        
        all_channels.extend(batch_data)
    
    # Deduplicate by channel_id
    seen_ids = set()
    unique_channels = []
    for ch in all_channels:
        if ch['channel_id'] not in seen_ids:
            seen_ids.add(ch['channel_id'])
            unique_channels.append(ch)
    
    print(f"\n📊 COLLECTION SUMMARY")
    print("=" * 50)
    print(f"Total channels collected: {len(all_channels)}")
    print(f"Unique channels: {len(unique_channels)}")
    
    # Query performance
    print(f"\n📈 Query Performance:")
    for q, stats in sorted(query_stats.items(), key=lambda x: x[1]['channels'], reverse=True):
        print(f"   {q}: {stats['channels']} channels from {stats['searches']} searches")
    
    # Save results
    if unique_channels:
        df = pd.DataFrame(unique_channels)
        
        # Create output path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"amateur_baseline_{timestamp}.csv"
        
        # Use project data directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(project_root, 'data', 'processed')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\n✅ SUCCESS: Saved {len(df)} channels to {output_path}")
        
        # Show sample stats
        print(f"\n📊 Sample Statistics:")
        print(f"   Median Views: {df['view_count'].median():,.0f}")
        print(f"   Median Subs: {df['sub_count'].median():,.0f}")
        print(f"   Channels with >1k subs: {len(df[df['sub_count'] > 1000])} ({len(df[df['sub_count'] > 1000])/len(df)*100:.1f}%)")
        
        print(f"\n📝 Sample Titles:")
        for title in df['title'].head(5):
            print(f"   - {title}")
    else:
        print("\n❌ No channels captured. Try increasing batches.")


if __name__ == "__main__":
    main()

