"""
discover_deep_random.py
-----------------------
Sample C: The "Deep Random" Survivorship Control
Method: Random Prefix Sampling (Zhou et al., 2011)
Goal: Find ~2.5k "True Random" videos/day (The "Dark Matter").

Strategy:
1. Generate random 3-character prefixes (e.g., "x7z").
2. Search. Most will return 0 results. Keep trying.
3. Collect whatever is returned to establish the Zero Baseline.
"""

import os
import sys
import argparse
import random
import string
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import youtube_api

def get_random_prefix(length=3):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def search_prefix(youtube, prefix, start_time, end_time, limit=50):
    """
    Search for videos using a random prefix.
    """
    videos = []
    try:
        request = youtube.search().list(
            part="snippet",
            type="video",
            q=prefix,
            publishedAfter=start_time,
            publishedBefore=end_time,
            order="date", # Force chronological
            maxResults=limit,
            regionCode=None # Global search for deep random, or "US" if strictly US-based
        )
        response = youtube_api.execute_request(request)
        videos = response.get('items', [])
    except Exception as e:
        print(f"Error searching '{prefix}': {e}")
        
    return videos

def get_deep_stats(youtube, channel_ids):
    """
    Get stats for deep random channels.
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
                    'last_active_window': datetime.now().strftime("%Y-%m-%d"),
                    'sample_type': 'baseline_deep_random'
                }
                data_list.append(data)
                
        except Exception as e:
            print(f"Error fetching stats: {e}")
            
    return data_list

def main():
    parser = argparse.ArgumentParser(description="Discover Deep Random Channels")
    parser.add_argument("--batches", type=int, default=10, help="Number of random prefixes to try")
    args = parser.parse_args()

    print(f"🚀 STARTING DEEP RANDOM DISCOVERY (Sample C) - {args.batches} Batches...")
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"FATAL: {e}")
        return

    # Use a tight recent window
    now = datetime.utcnow()
    start_time = (now - timedelta(hours=1)).isoformat() + "Z"
    end_time = now.isoformat() + "Z"
    
    all_data = []
    
    print(f"🔎 Scanning Window: {start_time} -> {end_time}")
    
    # We loop through "batches" of random prefixes
    # Since yield is low, we might need many attempts.
    
    hits = 0
    attempts = 0
    
    pbar = tqdm(total=args.batches, desc="Fishing")
    
    while attempts < args.batches:
        prefix = get_random_prefix()
        videos = search_prefix(youtube, prefix, start_time, end_time)
        
        attempts += 1
        pbar.update(1)
        
        if videos:
            ids = [v['snippet']['channelId'] for v in videos]
            batch_stats = get_deep_stats(youtube, ids)
            all_data.extend(batch_stats)
            hits += 1
            pbar.set_postfix({'hits': hits, 'collected': len(all_data)})
            
    pbar.close()

    # Save Results
    if all_data:
        df = pd.DataFrame(all_data)
        
        filename = f"baseline_deep_random_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed', filename)
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        df.to_csv(path, index=False)
        print(f"\n✅ SUCCESS: Captured {len(df)} deep random channels to {path}")
        print(df[['title', 'sub_count', 'view_count']].head())
    else:
        print("\n❌ No channels captured (Dark matter is elusive). Increase batches.")

if __name__ == "__main__":
    main()
