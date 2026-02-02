import sys
import os
import youtube_api
import statistics

def get_view_stats(youtube, query, label):
    print(f"\n🧪 TESTING: {label}")
    print(f"   Query: '{query}' | Order: 'date'")
    
    try:
        req = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            order="date",
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

        # Get View Counts
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

        median_views = statistics.median(views)
        
        print(f"   📊 RESULTS ({len(views)} videos):")
        print(f"      Median Views: {median_views:,.0f}")
        print(f"      Min Views:    {min(views)}")
        print(f"      Max Views:    {max(views):,.0f}")
        
        # Check titles for "Raw" artifacts
        print(f"   📝 Sample Titles: {[v['snippet']['title'] for v in videos[:3]]}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

def run_bias_test_v2():
    print("🔬 API BIAS DIAGNOSTIC V2 (Raw File Search)")
    print("===========================================")
    print("Hypothesis: 'a' hits popular videos. 'IMG' hits raw uploads.\n")
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # 1. The "Raw File" Strategy (Should be low bias)
    get_view_stats(youtube, "IMG", "Raw File 'IMG'")
    get_view_stats(youtube, "MVI", "Raw File 'MVI'")
    get_view_stats(youtube, "DSC", "Raw File 'DSC'")
    
    # 2. The "Common Word" Strategy (Control)
    get_view_stats(youtube, "video", "Common Word 'video'")

if __name__ == "__main__":
    run_bias_test_v2()
