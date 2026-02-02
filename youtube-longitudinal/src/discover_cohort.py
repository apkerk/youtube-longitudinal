"""
discover_cohort.py
------------------
Sample A: The "Intentional Entrant" Cohort
Method: Video-First Targeted Search
Goal: Find ~17k new "intentional" channels/day.

Strategy:
1. Search for videos using "Intent Keywords" (Welcome, Intro, etc.).
2. Extract channel IDs from videos.
3. Check channel details.
4. Filter for channels created in the target window (Jan 2026).
"""

import os
import sys
import argparse
import time
from datetime import datetime, timedelta
import pandas as pd
from googleapiclient.errors import HttpError
from tqdm import tqdm

# Add src to path to import youtube_api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import youtube_api

# --- CONFIGURATION ---
TARGET_KEYWORDS = [
    "Welcome to my channel",
    "My first video",
    "Intro",
    "Introduction",
    "Vlog 1",
    "Channel Trailer",
    "Get to know me",
    "Channel Introduction"
]

def search_videos_by_keyword(youtube, keyword, start_time, end_time, max_results=50):
    """
    Search for VIDEOS using a specific keyword.
    Returns: List of video items (snippet).
    """
    videos = []
    next_page_token = None
    
    # Minimal fields to save quota (100 units per call)
    # We only need snippets to identify channels
    try:
        request = youtube.search().list(
            part="snippet",
            type="video",
            q=keyword,
            publishedAfter=start_time,
            publishedBefore=end_time,
            order="date", # Force chronological
            maxResults=max_results,
            regionCode="US", # Focus on your target market
            pageToken=next_page_token
        )
        response = youtube_api.execute_request(request)
        videos.extend(response.get('items', []))
        
    except Exception as e:
        print(f"Error searching '{keyword}': {e}")
        
    return videos

def filter_new_channels(youtube, channel_ids, cutoff_date="2026-01-01"):
    """
    Check list of channel IDs. Return detailed data for those created >= cutoff.
    """
    new_channels = []
    
    # Deduplicate
    unique_ids = list(set(channel_ids))
    
    # Process in chunks of 50 (1 unit per call)
    for chunk in youtube_api.chunks(unique_ids, 50):
        try:
            request = youtube.channels().list(
                part="snippet,statistics,brandingSettings,status",
                id=",".join(chunk)
            )
            response = youtube_api.execute_request(request)
            
            for item in response.get('items', []):
                created_at = item['snippet']['publishedAt']
                
                # THE CRITICAL FILTER
                if created_at >= cutoff_date:
                    # Capturing Intent Signals
                    stats = item['statistics']
                    snippet = item['snippet']
                    branding = item.get('brandingSettings', {})
                    
                    data = {
                        'channel_id': item['id'],
                        'title': snippet.get('title'),
                        'published_at': created_at,
                        'video_count': int(stats.get('videoCount', 0)),
                        'view_count': int(stats.get('viewCount', 0)),
                        'sub_count': int(stats.get('subscriberCount', 0)),
                        'country': snippet.get('country'),
                        'intent_banner': 'image' in branding,
                        'intent_keywords': len(branding.get('channel', {}).get('keywords', '')) > 0,
                        'intent_desc_len': len(snippet.get('description', '')),
                        'discovery_method': 'targeted_keyword'
                    }
                    new_channels.append(data)
                    
        except Exception as e:
            print(f"Error checking channels: {e}")
            
    return new_channels

def main():
    parser = argparse.ArgumentParser(description="Discover New Intentional Creators")
    parser.add_argument("--hours", type=int, default=1, help="Number of hours to process")
    parser.add_argument("--start_offset", type=int, default=0, help="Hours back to start from")
    args = parser.parse_args()

    print(f"🚀 STARTING COHORT DISCOVERY (Targeted) for {args.hours} hours...")
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"FATAL: {e}")
        return

    # Define Time Window
    # For a real run, you loop through days. Here we do "now" or specific window.
    # Hardcoding Jan 1 2026 for simulation based on your tests
    base_time = datetime(2026, 1, 1, 0, 0, 0) # Start of study
    
    # Using 'hours' to iterate forward
    all_new_channels = []
    
    for h in range(args.hours):
        current_start = base_time + timedelta(hours=args.start_offset + h)
        current_end = current_start + timedelta(hours=1)
        
        t_start = current_start.isoformat() + "Z"
        t_end = current_end.isoformat() + "Z"
        
        print(f"\n🔎 Processing Window: {t_start} -> {t_end}")
        
        potential_channel_ids = []
        
        # 1. Video Search (The Dragnet)
        for kw in tqdm(TARGET_KEYWORDS, desc="Keywords"):
            videos = search_videos_by_keyword(youtube, kw, t_start, t_end)
            ids = [v['snippet']['channelId'] for v in videos]
            potential_channel_ids.extend(ids)
            
        print(f"   found {len(potential_channel_ids)} video hits.")
        
        if not potential_channel_ids:
            continue
            
        # 2. Channel Filter (The Sieve)
        print("   🕵️ Checking creation dates...")
        batch_new = filter_new_channels(youtube, potential_channel_ids)
        print(f"   🎉 Yielded {len(batch_new)} NEW Intentional Channels.")
        
        all_new_channels.extend(batch_new)

    # 3. Save Results
    if all_new_channels:
        df = pd.DataFrame(all_new_channels)
        
        # Save to 'processed'
        filename = f"cohort_new_creators_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed', filename)
        
        # Ensure dir exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        df.to_csv(path, index=False)
        print(f"\n✅ SUCCESS: Saved {len(df)} channels to {path}")
        print(df[['title', 'published_at', 'video_count']].head())
    else:
        print("\n❌ No new channels found in this run.")

if __name__ == "__main__":
    main()
