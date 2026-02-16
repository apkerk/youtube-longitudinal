"""
discover_cohort_multilingual.py
-------------------------------
Stream A (Enhanced): The "Intentional Entrant" Cohort - MULTILINGUAL VERSION
Method: Video-First Targeted Search across 8 languages
Goal: Find ~50k new "intentional" channels/day globally.

Rationale (from EXP-006, Feb 02, 2026):
- English-only keywords capture only 14% of findable new creators
- Multilingual approach expands population by 7.1x
- Hindi has HIGHEST yield (35.3%), even higher than English (30.9%)

Language Priority (by yield rate):
1. Hindi (35.3%)
2. English (30.9%)
3. Spanish (29.3%)
4. Japanese (24.5%)
5. German (24.0%)
6. Portuguese (23.1%)
7. Korean (22.5%)
8. French (18.3%)

Usage:
    python discover_cohort_multilingual.py --hours 24 --languages all
    python discover_cohort_multilingual.py --hours 24 --languages "English,Hindi,Spanish"

Quota Cost: ~25 units per new channel found
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from tqdm import tqdm

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import youtube_api


# --- MULTILINGUAL INTENT KEYWORDS ---
# Organized by language, ordered by yield rate (highest first)

INTENT_KEYWORDS = {
    "Hindi": [
        "Mere channel mein aapka swagat hai",  # Welcome to my channel
        "Mera pehla video",                     # My first video
        "Introduction hindi",
        "Namaste doston",                       # Hello friends
        "Channel trailer hindi",
    ],
    "English": [
        "Welcome to my channel",
        "My first video",
        "Introduction",
        "Intro",
        "Vlog 1",
        "Channel Trailer",
        "Get to know me",
        "Channel Introduction",
    ],
    "Spanish": [
        "Bienvenidos a mi canal",               # Welcome to my channel
        "Mi primer video",                      # My first video
        "Introducción",
        "Vlog 1 español",
        "Conóceme",                             # Get to know me
    ],
    "Japanese": [
        "チャンネル登録よろしく",                # Please subscribe
        "初投稿",                               # First upload
        "自己紹介",                             # Self-introduction
        "はじめまして",                         # Nice to meet you
    ],
    "German": [
        "Willkommen auf meinem Kanal",          # Welcome to my channel
        "Mein erstes Video",                    # My first video
        "Vorstellung",                          # Introduction
        "Kanal Trailer",
    ],
    "Portuguese": [
        "Bem-vindos ao meu canal",              # Welcome to my channel
        "Meu primeiro vídeo",                   # My first video
        "Introdução",
        "Me conhecendo",                        # Getting to know me
    ],
    "Korean": [
        "제 채널에 오신 것을 환영합니다",       # Welcome to my channel
        "첫 번째 영상",                         # First video
        "자기소개",                             # Self-introduction
        "채널 소개",                            # Channel introduction
    ],
    "French": [
        "Bienvenue sur ma chaîne",              # Welcome to my channel
        "Ma première vidéo",                    # My first video
        "Introduction",
        "Présentation",                         # Presentation
    ],
}


def search_videos_by_keyword(
    youtube,
    keyword: str,
    start_time: str,
    end_time: str,
    max_results: int = 50
) -> List[Dict]:
    """
    Search for videos using a specific keyword.
    
    Args:
        youtube: Authenticated YouTube API service
        keyword: Search query
        start_time: ISO format start time
        end_time: ISO format end time
        max_results: Max results per call
        
    Returns:
        List of video items from API response
    """
    videos = []
    
    try:
        request = youtube.search().list(
            part="snippet",
            type="video",
            q=keyword,
            publishedAfter=start_time,
            publishedBefore=end_time,
            order="date",  # Chronological to capture new uploads
            maxResults=max_results,
            regionCode=None  # Global search for multilingual
        )
        response = youtube_api.execute_request(request)
        videos = response.get('items', [])
        
    except Exception as e:
        print(f"Error searching '{keyword[:30]}...': {e}")
        
    return videos


def filter_new_channels(
    youtube,
    channel_ids: List[str],
    cutoff_date: str = "2026-01-01"
) -> List[Dict]:
    """
    Check list of channel IDs. Return detailed data for those created >= cutoff.
    
    Args:
        youtube: Authenticated YouTube API service
        channel_ids: List of channel IDs to check
        cutoff_date: ISO date string for minimum creation date
        
    Returns:
        List of channel data dictionaries for new channels only
    """
    new_channels = []
    unique_ids = list(set(channel_ids))
    
    for chunk in youtube_api.chunks(unique_ids, 50):
        try:
            request = youtube.channels().list(
                part="snippet,statistics,brandingSettings,status",
                id=",".join(chunk)
            )
            response = youtube_api.execute_request(request)
            
            for item in response.get('items', []):
                created_at = item['snippet']['publishedAt']
                
                # THE CRITICAL FILTER: Only keep new channels
                if created_at >= cutoff_date:
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
                        'description_length': len(snippet.get('description', '')),
                        'has_custom_banner': 'image' in branding,
                        'has_keywords': len(branding.get('channel', {}).get('keywords', '')) > 0,
                        'scraped_at': datetime.utcnow().isoformat(),
                        'stream_type': 'intentional_cohort',
                        'discovery_method': 'multilingual_intent_keyword'
                    }
                    new_channels.append(data)
                    
        except Exception as e:
            print(f"Error checking channels: {e}")
            
    return new_channels


def main():
    parser = argparse.ArgumentParser(
        description="Discover New Intentional Creators (Multilingual)"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours to scan (default: 24)"
    )
    parser.add_argument(
        "--languages",
        type=str,
        default="all",
        help="Comma-separated languages or 'all' (default: all)"
    )
    parser.add_argument(
        "--cutoff_date",
        type=str,
        default="2026-01-01",
        help="Minimum channel creation date (default: 2026-01-01)"
    )
    args = parser.parse_args()
    
    # Parse languages
    if args.languages.lower() == "all":
        selected_languages = list(INTENT_KEYWORDS.keys())
    else:
        selected_languages = [lang.strip() for lang in args.languages.split(",")]
    
    # Count total keywords
    total_keywords = sum(
        len(INTENT_KEYWORDS[lang]) 
        for lang in selected_languages 
        if lang in INTENT_KEYWORDS
    )
    
    print("🌍 STARTING MULTILINGUAL COHORT DISCOVERY (Stream A Enhanced)")
    print("=" * 60)
    print(f"Languages: {', '.join(selected_languages)}")
    print(f"Total Keywords: {total_keywords}")
    print(f"Hours to scan: {args.hours}")
    print(f"Cutoff Date: {args.cutoff_date}")
    
    # Estimate quota
    est_searches = total_keywords * args.hours  # 1 search per keyword per hour
    est_quota = est_searches * 100 + est_searches * 2  # search + channel checks
    print(f"Estimated quota: ~{est_quota:,} units")
    print("=" * 60)
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"❌ FATAL: {e}")
        return
    
    # Define time window
    now = datetime.utcnow()
    base_time = now - timedelta(hours=args.hours)
    
    all_new_channels = []
    language_stats = {}
    
    # Process each hour
    for hour_offset in range(args.hours):
        hour_start = base_time + timedelta(hours=hour_offset)
        hour_end = hour_start + timedelta(hours=1)
        
        t_start = hour_start.isoformat() + "Z"
        t_end = hour_end.isoformat() + "Z"
        
        print(f"\n⏰ Hour {hour_offset + 1}/{args.hours}: {hour_start.strftime('%Y-%m-%d %H:%M')}")
        
        potential_channel_ids = []
        
        # Search each language
        for language in selected_languages:
            if language not in INTENT_KEYWORDS:
                print(f"   ⚠️ Unknown language: {language}")
                continue
            
            keywords = INTENT_KEYWORDS[language]
            
            if language not in language_stats:
                language_stats[language] = {'videos': 0, 'new_channels': 0}
            
            for kw in keywords:
                videos = search_videos_by_keyword(youtube, kw, t_start, t_end)
                language_stats[language]['videos'] += len(videos)
                
                ids = [v['snippet']['channelId'] for v in videos]
                potential_channel_ids.extend(ids)
        
        if not potential_channel_ids:
            continue
        
        # Filter for new channels
        batch_new = filter_new_channels(
            youtube, 
            potential_channel_ids, 
            cutoff_date=args.cutoff_date
        )
        
        # Track by language (approximate - based on order)
        for ch in batch_new:
            all_new_channels.append(ch)
        
        print(f"   Found {len(potential_channel_ids)} videos → {len(batch_new)} new channels")
    
    # Deduplicate
    seen_ids = set()
    unique_channels = []
    for ch in all_new_channels:
        if ch['channel_id'] not in seen_ids:
            seen_ids.add(ch['channel_id'])
            unique_channels.append(ch)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 COLLECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total channels found: {len(all_new_channels)}")
    print(f"Unique new channels: {len(unique_channels)}")
    
    print(f"\n📈 Language Performance:")
    for lang, stats in sorted(language_stats.items(), key=lambda x: x[1]['videos'], reverse=True):
        print(f"   {lang}: {stats['videos']} videos")
    
    # Save results
    if unique_channels:
        df = pd.DataFrame(unique_channels)
        
        # Create output path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"cohort_multilingual_{timestamp}.csv"
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(project_root, 'data', 'processed')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\n✅ SUCCESS: Saved {len(df)} channels to {output_path}")
        
        # Show stats
        print(f"\n📊 New Creator Statistics:")
        print(f"   Median Videos: {df['video_count'].median():.0f}")
        print(f"   Median Views: {df['view_count'].median():,.0f}")
        print(f"   Median Subs: {df['sub_count'].median():,.0f}")
        
        # Country distribution
        if 'country' in df.columns:
            countries = df['country'].value_counts().head(10)
            print(f"\n🌍 Top Countries:")
            for country, count in countries.items():
                if pd.notna(country):
                    print(f"   {country}: {count}")
    else:
        print("\n❌ No new channels found. Try a different time window.")


if __name__ == "__main__":
    main()

