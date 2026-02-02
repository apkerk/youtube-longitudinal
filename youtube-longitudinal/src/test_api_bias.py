import sys
import os
import youtube_api
import statistics

def get_view_stats(youtube, query, order, label):
    print(f"\n🧪 TESTING: {label}")
    print(f"   Query: '{query}' | Order: '{order}'")
    
    # 1. Search
    req = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        order=order,
        maxResults=50,
        publishedAfter="2026-01-01T00:00:00Z",
        publishedBefore="2026-01-01T12:00:00Z",
        regionCode=None
    )
    res = youtube_api.execute_request(req)
    videos = res.get('items', [])
    
    if not videos:
        print("   ❌ No videos found.")
        return
        
    # 2. Get View Counts
    vid_ids = [v['id']['videoId'] for v in videos]
    stats_req = youtube.videos().list(
        part="statistics",
        id=",".join(vid_ids)
    )
    stats_res = youtube_api.execute_request(stats_req)
    
    views = []
    for item in stats_res.get('items', []):
        v = int(item['statistics'].get('viewCount', 0))
        views.append(v)
        
    if not views:
        print("   ❌ No stats found.")
        return

    # 3. Calculate Stats
    median_views = statistics.median(views)
    mean_views = statistics.mean(views)
    min_views = min(views)
    max_views = max(views)
    
    print(f"   📊 RESULTS ({len(views)} videos):")
    print(f"      Median Views: {median_views:,.0f}")
    print(f"      Mean Views:   {mean_views:,.0f}")
    print(f"      Min Views:    {min_views}")
    print(f"      Max Views:    {max_views:,.0f}")
    
    if median_views < 100:
        print("   ✅ VERDICT: LOW BIAS. Capturing long-tail/new content.")
    else:
        print("   ⚠️ VERDICT: HIGH BIAS. Capturing already-popular content.")

def run_bias_test():
    print("🔬 API BIAS DIAGNOSTIC")
    print("======================")
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # Scenario 1: The "Standard" Search (Biased?)
    get_view_stats(youtube, "a", "relevance", "Standard Search (Relevance)")
    
    # Scenario 2: Our Proposed Baseline (Unbiased?)
    get_view_stats(youtube, "a", "date", "Proposed Baseline (Date Sort)")
    
    # Scenario 3: Our Proposed Cohort (Targeted)
    get_view_stats(youtube, "Welcome to my channel", "date", "Proposed Cohort (Targeted)")

if __name__ == "__main__":
    run_bias_test()
