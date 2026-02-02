import sys
import os
import youtube_api

def run_test_v3():
    print("🧪 STARTING DIAGNOSTIC TEST V3 (High-Volume Targeted Video Search)")
    print("------------------------------------------------------------------")
    print("Hypothesis: New channels exist but are rare. We need targeted queries & volume.")
    
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # Jan 1, 2026, First 12 hours (Broader window)
    start_time = "2026-01-01T00:00:00Z"
    end_time = "2026-01-01T12:00:00Z"
    
    # Targeted queries for new channels
    queries = ["Welcome to my channel", "My first video", "Intro", "Introduction", "Vlog 1"]
    
    total_videos_found = 0
    total_new_channels = 0
    
    print(f"\n🔎 Scanning Window: {start_time} -> {end_time}")
    
    unique_channel_ids = set()
    
    for q in queries:
        print(f"\nTesting Query: '{q}'")
        try:
            request = youtube.search().list(
                part="snippet",
                type="video",
                publishedAfter=start_time,
                publishedBefore=end_time,
                q=q,
                maxResults=50, # Max per page
                regionCode="US" # Trying US again to match your likely target, or remove if 0
            )
            response = youtube_api.execute_request(request)
            videos = response.get('items', [])
            print(f"   Found {len(videos)} videos.")
            
            for v in videos:
                unique_channel_ids.add(v['snippet']['channelId'])
                
        except Exception as e:
            print(f"   ❌ Error searching '{q}': {e}")
            
    if not unique_channel_ids:
        print("❌ No videos found across all queries.")
        return

    print(f"\n🕵️  Checking {len(unique_channel_ids)} unique channels for creation date...")
    
    # Batch process channel checks
    channels_checked = 0
    
    # Process in chunks of 50
    chunk_size = 50
    channel_list = list(unique_channel_ids)
    
    for i in range(0, len(channel_list), chunk_size):
        chunk = channel_list[i:i + chunk_size]
        
        ch_req = youtube.channels().list(
            part="snippet,statistics",
            id=",".join(chunk)
        )
        ch_res = youtube_api.execute_request(ch_req)
        items = ch_res.get('items', [])
        
        for ch in items:
            created_at = ch['snippet']['publishedAt']
            # Strict check: Created AFTER Jan 1 2026
            if created_at >= "2026-01-01":
                print(f"   🎉 NEW CHANNEL FOUND: {ch['snippet']['title']}")
                print(f"      Created: {created_at} | Videos: {ch['statistics']['videoCount']}")
                total_new_channels += 1
            channels_checked += 1
            
    print("\n------------------------------------------------")
    print(f"📊 FINAL STATISTICS")
    print(f"   Total Unique Uploaders Checked: {channels_checked}")
    print(f"   Total New Channels (Jan 2026+): {total_new_channels}")
    
    if channels_checked > 0:
        yield_rate = (total_new_channels / channels_checked) * 100
        print(f"   Yield Rate: {yield_rate:.2f}%")
        
        # Feasibility check
        if yield_rate > 0.5:
             print("✅ VERDICT: VIABLE. The yield is good enough to build the cohort.")
        elif yield_rate > 0:
             print("⚠️ VERDICT: HARD MODE. Yield is low, but possible with massive quota.")
        else:
             print("❌ VERDICT: FAILED. 0% yield on targeted queries.")

if __name__ == "__main__":
    run_test_v3()
