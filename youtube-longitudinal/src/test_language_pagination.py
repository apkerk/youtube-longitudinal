"""
test_language_pagination.py
---------------------------
Additional Sampling Experiments:

EXP-006: Language Bias Detection
- Do English keywords miss non-English new creators?

EXP-008: Pagination Depth Bias  
- Do deeper search results have different bias profiles?

Quota Cost Estimate: ~3,000 units
"""

import sys
import os
import statistics
from datetime import datetime
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import youtube_api


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# =============================================================================
# EXPERIMENT 6: LANGUAGE BIAS DETECTION
# =============================================================================

def run_language_experiment(youtube) -> list:
    """
    Compare yield rates across different languages.
    Tests whether English-only keywords miss significant creator populations.
    """
    print("\n" + "="*60)
    print("📊 EXPERIMENT 6: LANGUAGE BIAS DETECTION")
    print("="*60)
    print("Question: Are English intent keywords missing non-English creators?")
    
    # Intent keywords in multiple languages
    language_keywords = {
        "English": [
            "Welcome to my channel",
            "My first video",
            "Introduction"
        ],
        "Spanish": [
            "Bienvenidos a mi canal",
            "Mi primer video",
            "Introducción"
        ],
        "Portuguese": [
            "Bem-vindos ao meu canal",
            "Meu primeiro vídeo",
            "Introdução"
        ],
        "Hindi (Romanized)": [
            "Mere channel mein aapka swagat hai",
            "Mera pehla video",
            "Introduction hindi"
        ],
        "French": [
            "Bienvenue sur ma chaîne",
            "Ma première vidéo",
            "Introduction"
        ],
        "German": [
            "Willkommen auf meinem Kanal",
            "Mein erstes Video",
            "Vorstellung"
        ],
        "Korean (Romanized)": [
            "제 채널에 오신 것을 환영합니다",
            "첫 번째 영상",
            "자기소개"
        ],
        "Japanese (Romanized)": [
            "チャンネル登録よろしく",
            "初投稿",
            "自己紹介"
        ]
    }
    
    results = []
    cutoff_date = "2026-01-01"
    
    for language, keywords in language_keywords.items():
        print(f"\n🌍 Testing: {language}")
        
        unique_channel_ids = set()
        total_videos = 0
        
        for kw in keywords:
            try:
                req = youtube.search().list(
                    part="snippet",
                    type="video",
                    q=kw,
                    order="date",
                    maxResults=50,
                    publishedAfter="2026-01-01T00:00:00Z",
                    publishedBefore="2026-01-31T00:00:00Z",
                    regionCode=None  # Global search for fair comparison
                )
                res = youtube_api.execute_request(req)
                videos = res.get('items', [])
                total_videos += len(videos)
                
                for v in videos:
                    unique_channel_ids.add(v['snippet']['channelId'])
                    
                print(f"   '{kw[:30]}...': {len(videos)} videos")
                
            except Exception as e:
                print(f"   Error on '{kw[:20]}...': {e}")
        
        # Check channel creation dates
        new_channels = 0
        total_checked = 0
        
        if unique_channel_ids:
            for chunk in chunks(list(unique_channel_ids), 50):
                try:
                    req = youtube.channels().list(
                        part="snippet",
                        id=",".join(chunk)
                    )
                    res = youtube_api.execute_request(req)
                    
                    for ch in res.get('items', []):
                        total_checked += 1
                        if ch['snippet']['publishedAt'] >= cutoff_date:
                            new_channels += 1
                            
                except Exception as e:
                    print(f"   Error checking channels: {e}")
        
        yield_rate = (new_channels / total_checked * 100) if total_checked > 0 else 0
        
        results.append({
            'Language': language,
            'Keywords_Tested': len(keywords),
            'Videos_Found': total_videos,
            'Channels_Checked': total_checked,
            'New_Channels': new_channels,
            'Yield_%': round(yield_rate, 2)
        })
        
        print(f"   → {new_channels}/{total_checked} new channels ({yield_rate:.1f}% yield)")
    
    return results


# =============================================================================
# EXPERIMENT 8: PAGINATION DEPTH BIAS
# =============================================================================

def run_pagination_experiment(youtube) -> list:
    """
    Test whether deeper search results have different bias profiles.
    Hypothesis: Page 1 results are algorithm-optimized, deeper pages are more random.
    """
    print("\n" + "="*60)
    print("📊 EXPERIMENT 8: PAGINATION DEPTH BIAS")
    print("="*60)
    print("Question: Do deeper search results have less algorithmic bias?")
    
    query = "a"  # Neutral query with lots of results
    results = []
    
    # We'll paginate through multiple pages
    page_token = None
    page_num = 0
    max_pages = 5  # Go 5 pages deep (250 results)
    
    while page_num < max_pages:
        page_num += 1
        print(f"\n📄 Page {page_num} (results {(page_num-1)*50 + 1}-{page_num*50})")
        
        try:
            req = youtube.search().list(
                part="snippet",
                type="video",
                q=query,
                order="date",
                maxResults=50,
                publishedAfter="2026-01-01T00:00:00Z",
                publishedBefore="2026-01-31T00:00:00Z",
                regionCode=None,
                pageToken=page_token
            )
            res = youtube_api.execute_request(req)
            videos = res.get('items', [])
            page_token = res.get('nextPageToken')
            
            if not videos:
                print("   No more results")
                break
            
            # Get video stats
            vid_ids = [v['id']['videoId'] for v in videos]
            ch_ids = list(set([v['snippet']['channelId'] for v in videos]))
            
            # Video views
            views = []
            for chunk in chunks(vid_ids, 50):
                try:
                    r = youtube.videos().list(part="statistics", id=",".join(chunk))
                    resp = youtube_api.execute_request(r)
                    for item in resp.get('items', []):
                        views.append(int(item['statistics'].get('viewCount', 0)))
                except:
                    pass
            
            # Channel subs
            subs = []
            for chunk in chunks(ch_ids, 50):
                try:
                    r = youtube.channels().list(part="statistics", id=",".join(chunk))
                    resp = youtube_api.execute_request(r)
                    for item in resp.get('items', []):
                        subs.append(int(item['statistics'].get('subscriberCount', 0)))
                except:
                    pass
            
            median_views = statistics.median(views) if views else 0
            median_subs = statistics.median(subs) if subs else 0
            big_channel_pct = (sum(1 for s in subs if s > 1000) / len(subs) * 100) if subs else 0
            
            results.append({
                'Page': page_num,
                'Rank_Range': f"{(page_num-1)*50 + 1}-{page_num*50}",
                'Videos': len(videos),
                'Median_Views': median_views,
                'Median_Subs': median_subs,
                'Big_Channel_%': round(big_channel_pct, 1)
            })
            
            print(f"   Median Views: {median_views:,.0f}")
            print(f"   Median Subs: {median_subs:,.0f}")
            print(f"   Big Channel %: {big_channel_pct:.1f}%")
            
            if not page_token:
                print("   (No more pages)")
                break
                
        except Exception as e:
            print(f"   Error: {e}")
            break
    
    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("🧪 ADDITIONAL SAMPLING EXPERIMENTS")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Running: EXP-006 (Language) + EXP-008 (Pagination)")
    print()
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"❌ Authentication Error: {e}")
        return
    
    all_results = {}
    
    # Experiment 6: Language Bias
    all_results['language'] = run_language_experiment(youtube)
    
    # Experiment 8: Pagination Depth
    all_results['pagination'] = run_pagination_experiment(youtube)
    
    # =============================================================================
    # FINAL OUTPUT
    # =============================================================================
    
    print("\n")
    print("="*60)
    print("📋 RESULTS SUMMARY (Copy to SAMPLING_EXPERIMENTS.md)")
    print("="*60)
    
    # Language Results
    print("\n### EXP-006: Language Bias Detection")
    print("| Language | Videos Found | Channels Checked | New Channels | Yield % |")
    print("|----------|--------------|------------------|--------------|---------|")
    for r in all_results['language']:
        print(f"| {r['Language']} | {r['Videos_Found']} | {r['Channels_Checked']} | {r['New_Channels']} | {r['Yield_%']}% |")
    
    # Calculate total potential if multilingual
    total_new = sum(r['New_Channels'] for r in all_results['language'])
    english_new = next((r['New_Channels'] for r in all_results['language'] if r['Language'] == 'English'), 0)
    if english_new > 0:
        expansion_factor = total_new / english_new
        print(f"\n**Key Finding:** Multilingual keywords find {expansion_factor:.1f}x more new creators than English alone.")
    
    # Pagination Results
    print("\n### EXP-008: Pagination Depth Bias")
    print("| Page | Rank Range | Videos | Median Views | Median Subs | Big Channel % |")
    print("|------|------------|--------|--------------|-------------|---------------|")
    for r in all_results['pagination']:
        print(f"| {r['Page']} | {r['Rank_Range']} | {r['Videos']} | {r['Median_Views']:,.0f} | {r['Median_Subs']:,.0f} | {r['Big_Channel_%']} |")
    
    # Check for trend
    if len(all_results['pagination']) >= 2:
        first_page_views = all_results['pagination'][0]['Median_Views']
        last_page_views = all_results['pagination'][-1]['Median_Views']
        if first_page_views > 0:
            change = ((last_page_views - first_page_views) / first_page_views) * 100
            direction = "decreases" if change < 0 else "increases"
            print(f"\n**Key Finding:** Median views {direction} by {abs(change):.0f}% from page 1 to page {len(all_results['pagination'])}.")
    
    print("\n" + "="*60)
    print(f"✅ Experiments complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)


if __name__ == "__main__":
    main()

