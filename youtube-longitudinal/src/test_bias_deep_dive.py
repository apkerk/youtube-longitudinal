"""
test_bias_deep_dive.py
----------------------
Bias Investigation Tool
Goal: Empirically compare the "Bias Profile" of different search strategies.

Strategies Tested:
1. High-Visibility (Queries: a, e, i, o, u)
2. Raw/Amateur (Queries: IMG, MVI, DSC)
3. Random Prefix (Queries: 3-char random strings e.g. 'x7z')

Metrics:
- Median View Count
- Median Subscriber Count
- % Zero-View Videos (True "Dark Matter")
"""

import sys
import os
import random
import string
import statistics
import pandas as pd

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import youtube_api

def get_random_string(length=3):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def run_strategy(youtube, label, queries, n_batches=3):
    print(f"\n🔎 Testing Strategy: {label}")
    
    all_videos = []
    
    for _ in range(n_batches):
        q = random.choice(queries) if isinstance(queries, list) else queries()
        try:
            # 1. Search (Date Ordered)
            req = youtube.search().list(
                part="snippet",
                q=q,
                type="video",
                order="date",
                maxResults=50,
                publishedAfter="2026-01-01T00:00:00Z",
                publishedBefore="2026-01-01T12:00:00Z",
                regionCode=None
            )
            res = youtube_api.execute_request(req)
            items = res.get('items', [])
            all_videos.extend(items)
        except Exception as e:
            print(f"Error on q='{q}': {e}")
            
    if not all_videos:
        return None

    # 2. Get Details (Views & Subs)
    # Need channel details for subs, video details for views
    vid_ids = [v['id']['videoId'] for v in all_videos]
    ch_ids = [v['snippet']['channelId'] for v in all_videos]
    
    # Batch fetching video stats
    video_stats = {}
    for chunk in youtube_api.chunks(vid_ids, 50):
        r = youtube.videos().list(part="statistics", id=",".join(chunk))
        resp = youtube_api.execute_request(r)
        for i in resp.get('items', []):
            video_stats[i['id']] = int(i['statistics'].get('viewCount', 0))

    # Batch fetching channel stats
    channel_stats = {}
    for chunk in youtube_api.chunks(list(set(ch_ids)), 50):
        r = youtube.channels().list(part="statistics", id=",".join(chunk))
        resp = youtube_api.execute_request(r)
        for i in resp.get('items', []):
            channel_stats[i['id']] = int(i['statistics'].get('subscriberCount', 0))

    # 3. Aggregate Data
    data_points = []
    for v in all_videos:
        vid = v['id']['videoId']
        cid = v['snippet']['channelId']
        views = video_stats.get(vid, 0)
        subs = channel_stats.get(cid, 0)
        
        data_points.append({
            'views': views,
            'subs': subs
        })
        
    df = pd.DataFrame(data_points)
    
    return {
        'Strategy': label,
        'N': len(df),
        'Median_Views': df['views'].median(),
        'Mean_Views': df['views'].mean(),
        'Zero_View_%': (len(df[df['views'] == 0]) / len(df)) * 100,
        'Median_Subs': df['subs'].median(),
        'Big_Channel_%': (len(df[df['subs'] > 1000]) / len(df)) * 100 # % > 1k subs
    }

def main():
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"Auth Error: {e}")
        return

    results = []
    
    # 1. High-Vis (Vowels)
    res_hv = run_strategy(youtube, "High-Vis (Vowels)", ["a", "e", "i", "o", "u"])
    if res_hv: results.append(res_hv)
    
    # 2. Raw/Amateur (IMG/MVI)
    res_raw = run_strategy(youtube, "Raw/Amateur (IMG)", ["IMG", "MVI", "DSC"])
    if res_raw: results.append(res_raw)
    
    # 3. Random Prefix (xyz)
    res_rnd = run_strategy(youtube, "Random Prefix (xyz)", get_random_string)
    if res_rnd: results.append(res_rnd)
    
    print("\n\n📊 FINAL BIAS COMPARISON")
    print("========================")
    if results:
        df_final = pd.DataFrame(results)
        # Reorder columns for readability
        cols = ['Strategy', 'N', 'Median_Views', 'Mean_Views', 'Zero_View_%', 'Median_Subs', 'Big_Channel_%']
        # Round floats
        print(df_final[cols].round(1).to_string(index=False))
    else:
        print("No results collected.")

if __name__ == "__main__":
    main()
