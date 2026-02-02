"""
test_sampling_battery.py
------------------------
Comprehensive Sampling Strategy Test Battery

Runs multiple experiments and outputs results in a format 
ready to paste into SAMPLING_EXPERIMENTS.md.

Experiments:
1. Bias Profile Comparison (Vowels vs Raw vs Random Prefix)
2. New Creator Yield Rate (Intent Keywords)
3. Non-Intent Yield Rate (Content Keywords)
4. Channel ID Enumeration Hit Rate
5. Region Code Impact

Quota Cost Estimate: ~5,000 units (safe for testing)
"""

import sys
import os
import random
import string
import statistics
from datetime import datetime
from typing import Optional, Callable
import pandas as pd

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import youtube_api


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_random_prefix(length: int = 3) -> str:
    """Generate a random alphanumeric prefix."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_channel_id() -> str:
    """Generate a candidate YouTube channel ID (UC + 22 base64 chars)."""
    chars = string.ascii_letters + string.digits + '-_'
    suffix = ''.join(random.choices(chars, k=22))
    return f"UC{suffix}"


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# =============================================================================
# EXPERIMENT 1: BIAS PROFILE COMPARISON
# =============================================================================

def run_bias_profile_experiment(youtube, n_batches: int = 3) -> dict:
    """
    Compare bias profiles across different query strategies.
    
    Returns dict with results for each strategy.
    """
    print("\n" + "="*60)
    print("📊 EXPERIMENT 1: BIAS PROFILE COMPARISON")
    print("="*60)
    
    strategies = {
        "High-Vis (Vowels)": ["a", "e", "i", "o", "u"],
        "Raw/Amateur (IMG)": ["IMG", "MVI", "DSC", "MOV", "VID_"],
        "Random Prefix": get_random_prefix,  # callable
        "Common Words": ["video", "2026", "new"]
    }
    
    results = []
    
    for label, queries in strategies.items():
        print(f"\n🔎 Testing: {label}")
        
        all_videos = []
        hits = 0
        attempts = 0
        
        for _ in range(n_batches):
            # Get query (either from list or callable)
            if callable(queries):
                q = queries()
            else:
                q = random.choice(queries)
            
            attempts += 1
            
            try:
                req = youtube.search().list(
                    part="snippet",
                    q=q,
                    type="video",
                    order="date",
                    maxResults=50,
                    publishedAfter="2026-01-01T00:00:00Z",
                    publishedBefore="2026-01-15T00:00:00Z",
                    regionCode=None  # Global for fair comparison
                )
                res = youtube_api.execute_request(req)
                items = res.get('items', [])
                
                if items:
                    hits += 1
                    all_videos.extend(items)
                    print(f"   Query '{q}': {len(items)} videos")
                else:
                    print(f"   Query '{q}': 0 videos")
                    
            except Exception as e:
                print(f"   Error on '{q}': {e}")
        
        if not all_videos:
            results.append({
                'Strategy': label,
                'N': 0,
                'Median_Views': None,
                'Zero_View_%': None,
                'Median_Subs': None,
                'Big_Channel_%': None,
                'Hit_Rate_%': (hits / attempts * 100) if attempts > 0 else 0
            })
            continue
        
        # Get video stats
        vid_ids = [v['id']['videoId'] for v in all_videos]
        ch_ids = list(set([v['snippet']['channelId'] for v in all_videos]))
        
        video_stats = {}
        for chunk in chunks(vid_ids, 50):
            try:
                r = youtube.videos().list(part="statistics", id=",".join(chunk))
                resp = youtube_api.execute_request(r)
                for item in resp.get('items', []):
                    video_stats[item['id']] = int(item['statistics'].get('viewCount', 0))
            except Exception as e:
                print(f"   Error fetching video stats: {e}")
        
        channel_stats = {}
        for chunk in chunks(ch_ids, 50):
            try:
                r = youtube.channels().list(part="statistics", id=",".join(chunk))
                resp = youtube_api.execute_request(r)
                for item in resp.get('items', []):
                    channel_stats[item['id']] = int(item['statistics'].get('subscriberCount', 0))
            except Exception as e:
                print(f"   Error fetching channel stats: {e}")
        
        # Compile data
        views = [video_stats.get(v['id']['videoId'], 0) for v in all_videos]
        subs = [channel_stats.get(v['snippet']['channelId'], 0) for v in all_videos]
        
        results.append({
            'Strategy': label,
            'N': len(all_videos),
            'Median_Views': statistics.median(views) if views else 0,
            'Zero_View_%': round((sum(1 for v in views if v == 0) / len(views)) * 100, 1) if views else 0,
            'Median_Subs': statistics.median(subs) if subs else 0,
            'Big_Channel_%': round((sum(1 for s in subs if s > 1000) / len(subs)) * 100, 1) if subs else 0,
            'Hit_Rate_%': round((hits / attempts * 100), 1) if attempts > 0 else 0
        })
    
    return results


# =============================================================================
# EXPERIMENT 2: NEW CREATOR YIELD RATE
# =============================================================================

def run_yield_experiment(youtube, queries: list, label: str, cutoff_date: str = "2026-01-01") -> dict:
    """
    Measure yield rate: what % of videos belong to NEW channels?
    """
    print(f"\n🔎 Testing: {label}")
    
    unique_channel_ids = set()
    
    for q in queries:
        try:
            req = youtube.search().list(
                part="snippet",
                type="video",
                q=q,
                order="date",
                maxResults=50,
                publishedAfter="2026-01-01T00:00:00Z",
                publishedBefore="2026-01-15T00:00:00Z",
                regionCode="US"
            )
            res = youtube_api.execute_request(req)
            videos = res.get('items', [])
            
            for v in videos:
                unique_channel_ids.add(v['snippet']['channelId'])
            
            print(f"   Query '{q}': {len(videos)} videos, {len(unique_channel_ids)} unique channels so far")
            
        except Exception as e:
            print(f"   Error on '{q}': {e}")
    
    if not unique_channel_ids:
        return {'Label': label, 'Channels_Checked': 0, 'New_Channels': 0, 'Yield_%': 0}
    
    # Check channel creation dates
    new_channels = 0
    total_checked = 0
    
    for chunk in chunks(list(unique_channel_ids), 50):
        try:
            req = youtube.channels().list(
                part="snippet",
                id=",".join(chunk)
            )
            res = youtube_api.execute_request(req)
            
            for ch in res.get('items', []):
                total_checked += 1
                created_at = ch['snippet']['publishedAt']
                if created_at >= cutoff_date:
                    new_channels += 1
                    
        except Exception as e:
            print(f"   Error checking channels: {e}")
    
    yield_rate = (new_channels / total_checked * 100) if total_checked > 0 else 0
    
    return {
        'Label': label,
        'Channels_Checked': total_checked,
        'New_Channels': new_channels,
        'Yield_%': round(yield_rate, 2)
    }


def run_yield_experiments(youtube) -> list:
    """
    Run yield experiments for both intent and non-intent keywords.
    """
    print("\n" + "="*60)
    print("📊 EXPERIMENT 2 & 3: NEW CREATOR YIELD RATES")
    print("="*60)
    
    # Intent keywords (Stream A)
    intent_keywords = [
        "Welcome to my channel",
        "My first video",
        "Intro",
        "Introduction",
        "Vlog 1",
        "Channel Trailer",
        "Get to know me"
    ]
    
    # Non-intent keywords (Stream A')
    non_intent_keywords = [
        "gameplay",
        "let's play",
        "tutorial",
        "recipe",
        "review",
        "unboxing",
        "haul"
    ]
    
    results = []
    results.append(run_yield_experiment(youtube, intent_keywords, "Intent Keywords (Stream A)"))
    results.append(run_yield_experiment(youtube, non_intent_keywords, "Non-Intent Keywords (Stream A')"))
    
    return results


# =============================================================================
# EXPERIMENT 4: CHANNEL ID ENUMERATION
# =============================================================================

def run_channel_id_experiment(youtube, n_attempts: int = 100) -> dict:
    """
    Test hit rate for randomly generated channel IDs.
    """
    print("\n" + "="*60)
    print("📊 EXPERIMENT 4: CHANNEL ID ENUMERATION HIT RATE")
    print("="*60)
    print(f"   Generating {n_attempts} random channel IDs...")
    
    hits = 0
    checked = 0
    
    # Generate random IDs and check in batches
    random_ids = [generate_random_channel_id() for _ in range(n_attempts)]
    
    for chunk in chunks(random_ids, 50):
        try:
            req = youtube.channels().list(
                part="id",
                id=",".join(chunk)
            )
            res = youtube_api.execute_request(req)
            
            found = len(res.get('items', []))
            hits += found
            checked += len(chunk)
            
            if found > 0:
                print(f"   🎯 Found {found} valid channel(s) in batch!")
                
        except Exception as e:
            print(f"   Error: {e}")
            checked += len(chunk)
    
    hit_rate = (hits / checked * 100) if checked > 0 else 0
    
    print(f"\n   Results: {hits}/{checked} hits ({hit_rate:.4f}%)")
    
    return {
        'Attempts': checked,
        'Hits': hits,
        'Hit_Rate_%': round(hit_rate, 4)
    }


# =============================================================================
# EXPERIMENT 5: REGION CODE IMPACT
# =============================================================================

def run_region_experiment(youtube) -> list:
    """
    Compare results with different region codes.
    """
    print("\n" + "="*60)
    print("📊 EXPERIMENT 5: REGION CODE IMPACT")
    print("="*60)
    
    query = "Welcome to my channel"
    regions = [None, "US", "GB", "IN", "BR", "DE"]  # None = global
    
    results = []
    
    for region in regions:
        region_label = region if region else "Global (None)"
        print(f"\n🔎 Testing region: {region_label}")
        
        try:
            req = youtube.search().list(
                part="snippet",
                type="video",
                q=query,
                order="date",
                maxResults=50,
                publishedAfter="2026-01-01T00:00:00Z",
                publishedBefore="2026-01-15T00:00:00Z",
                regionCode=region
            )
            res = youtube_api.execute_request(req)
            videos = res.get('items', [])
            
            # Get view counts
            if videos:
                vid_ids = [v['id']['videoId'] for v in videos]
                stats_req = youtube.videos().list(part="statistics", id=",".join(vid_ids[:50]))
                stats_res = youtube_api.execute_request(stats_req)
                
                views = [int(item['statistics'].get('viewCount', 0)) for item in stats_res.get('items', [])]
                median_views = statistics.median(views) if views else 0
            else:
                median_views = 0
            
            results.append({
                'Region': region_label,
                'Videos_Found': len(videos),
                'Median_Views': median_views
            })
            
            print(f"   Found {len(videos)} videos, median views: {median_views:,.0f}")
            
        except Exception as e:
            print(f"   Error: {e}")
            results.append({
                'Region': region_label,
                'Videos_Found': 0,
                'Median_Views': 0
            })
    
    return results


# =============================================================================
# MAIN: RUN ALL EXPERIMENTS
# =============================================================================

def main():
    print("🧪 SAMPLING METHODOLOGY TEST BATTERY")
    print("====================================")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Estimated quota cost: ~5,000 units")
    print()
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"❌ Authentication Error: {e}")
        return
    
    all_results = {}
    
    # Experiment 1: Bias Profile
    all_results['bias_profile'] = run_bias_profile_experiment(youtube, n_batches=3)
    
    # Experiments 2 & 3: Yield Rates
    all_results['yield_rates'] = run_yield_experiments(youtube)
    
    # Experiment 4: Channel ID Enumeration
    all_results['channel_id_enum'] = run_channel_id_experiment(youtube, n_attempts=100)
    
    # Experiment 5: Region Impact
    all_results['region_impact'] = run_region_experiment(youtube)
    
    # =============================================================================
    # FINAL OUTPUT (Copy-Paste Ready)
    # =============================================================================
    
    print("\n")
    print("="*60)
    print("📋 RESULTS SUMMARY (Copy to SAMPLING_EXPERIMENTS.md)")
    print("="*60)
    
    # Bias Profile Table
    print("\n### EXP-001/003: Bias Profile Comparison")
    print("| Strategy | N | Median Views | Zero-View % | Median Subs | Big Channel % | Hit Rate % |")
    print("|----------|---|--------------|-------------|-------------|---------------|------------|")
    for r in all_results['bias_profile']:
        mv = f"{r['Median_Views']:,.0f}" if r['Median_Views'] else "N/A"
        ms = f"{r['Median_Subs']:,.0f}" if r['Median_Subs'] else "N/A"
        print(f"| {r['Strategy']} | {r['N']} | {mv} | {r['Zero_View_%']} | {ms} | {r['Big_Channel_%']} | {r['Hit_Rate_%']} |")
    
    # Yield Rate Table
    print("\n### EXP-002/010: New Creator Yield Rates")
    print("| Keyword Type | Channels Checked | New Channels | Yield Rate % |")
    print("|--------------|------------------|--------------|--------------|")
    for r in all_results['yield_rates']:
        print(f"| {r['Label']} | {r['Channels_Checked']} | {r['New_Channels']} | {r['Yield_%']}% |")
    
    # Channel ID Enumeration
    print("\n### EXP-005: Channel ID Enumeration")
    r = all_results['channel_id_enum']
    print(f"- Attempts: {r['Attempts']}")
    print(f"- Hits: {r['Hits']}")
    print(f"- Hit Rate: {r['Hit_Rate_%']}%")
    
    # Region Impact
    print("\n### EXP-007: Region Code Impact")
    print("| Region | Videos Found | Median Views |")
    print("|--------|--------------|--------------|")
    for r in all_results['region_impact']:
        print(f"| {r['Region']} | {r['Videos_Found']} | {r['Median_Views']:,.0f} |")
    
    print("\n" + "="*60)
    print(f"✅ Test battery complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)


if __name__ == "__main__":
    main()

