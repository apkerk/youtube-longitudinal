"""
discover_visible.py
-------------------
Sample B: The "Visible Market" Baseline
Method: Video-First "Vowel Rotation" Search
Goal: Find ~50k active channels/day (Old + New) as a market control group.

Strategy:
1. Search for neutral queries ("a", "e", "video", etc.).
2. Extract channel IDs.
3. Save basic stats (Subscriber count, View count) to establish the "Market Baseline".
"""

import os
import sys
import argparse
import random
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import youtube_api

# --- VISUAL COVERAGE DICTIONARY ---
# Weighted to maximize randomness.
# Includes "Raw File" queries (IMG, MVI) to capture casual/amateur uploads per user request.
BASE_QUERIES = [
    "a", "e", "i", "o", "u", 
    "video", "shou", 
    "IMG", "MVI", "DSC", "MOV", "2026", "100"
]

def search_random_videos(youtube, start_time, end_time, limit=50):
    """
    Search for videos using a random neutral query.
    """
    videos = []
    
    # Rotate queries randomly to avoid caching/bias
    query = random.choice(BASE_QUERIES)
    
    try:
        request = youtube.search().list(
            part="snippet",
            type="video",
            q=query,
            publishedAfter=start_time,
            publishedBefore=end_time,
            order="date", # Force chronological
            maxResults=limit,
            regionCode="US"
        )
        response = youtube_api.execute_request(request)
        videos = response.get('items', [])
        
    except Exception as e:
        print(f"Error searching '{query}': {e}")
        
    return videos, query

def get_baseline_stats(youtube, channel_ids):
    """
    Get stats for active channels. No creation date filter (we want all active).
    """
    baseline_data = []
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
                    'published_at': snippet.get('publishedAt'), # DO NOT FILTER ON THIS
                    'video_count': int(stats.get('videoCount', 0)),
                    'view_count': int(stats.get('viewCount', 0)),
                    'sub_count': int(stats.get('subscriberCount', 0)),
                    'last_active_window': datetime.now().strftime("%Y-%m-%d"),
                    'sample_type': 'baseline_visible'
                }
                baseline_data.append(data)
                
        except Exception as e:
            print(f"Error fetching stats: {e}")
            
    return baseline_data

def main():
    parser = argparse.ArgumentParser(description="Discover Active Baseline Channels")
    parser.add_argument("--batches", type=int, default=5, help="Number of search batches to run")
    args = parser.parse_args()

    print(f"🚀 STARTING BASELINE DISCOVERY (Randomized) - {args.batches} Batches...")
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"FATAL: {e}")
        return

    # Use a tight recent window to ensure they are CURRENTLY active
    now = datetime.utcnow()
    start_time = (now - timedelta(hours=1)).isoformat() + "Z"
    end_time = now.isoformat() + "Z"
    
    all_active_channels = []
    
    print(f"🔎 Scanning Activity Window: {start_time} -> {end_time}")
    
    for _ in tqdm(range(args.batches), desc="Sampling"):
        # 1. Search Random Videos
        videos, q_used = search_random_videos(youtube, start_time, end_time)
        ids = [v['snippet']['channelId'] for v in videos]
        
        if not ids:
            continue
            
        # 2. Get Stats (No Filtering, just recording)
        batch_data = get_baseline_stats(youtube, ids)
        all_active_channels.extend(batch_data)
        
    # 3. Save Results
    if all_active_channels:
        df = pd.DataFrame(all_active_channels)
        
        filename = f"baseline_active_sample_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed', filename)
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        df.to_csv(path, index=False)
        print(f"\n✅ SUCCESS: Captured {len(df)} active channels to {path}")
        print(df[['title', 'sub_count', 'view_count']].head())
    else:
        print("\n❌ No active channels captured.")

if __name__ == "__main__":
    main()
