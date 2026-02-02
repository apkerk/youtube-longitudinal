import sys
import os
import youtube_api

def run_test_v2():
    print("🧪 STARTING DIAGNOSTIC TEST V2 (Video-First Strategy)")
    print("---------------------------------------------------")
    print("Hypothesis: Direct channel search is restricted. Searching for VIDEOS instead.")
    
    # 1. Authenticate
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # 2. Setup Window (Jan 1, 2026, 00:00-01:00)
    start_time = "2026-01-01T00:00:00Z"
    end_time = "2026-01-01T02:00:00Z" # 2 hours
    
    print(f"\n🔎 Scanning for VIDEOS: {start_time} -> {end_time}")
    
    try:
        # Search for VIDEOS (type='video')
        # Using a broad query to catch anything
        request = youtube.search().list(
            part="snippet",
            type="video",
            publishedAfter=start_time,
            publishedBefore=end_time,
            q="a", # 'a' is in almost every title
            maxResults=20,
            regionCode=None
        )
        response = youtube_api.execute_request(request)
        videos = response.get('items', [])
        
        print(f"✅ Video Search Complete. Found {len(videos)} videos.")
        
        if not videos:
            print("❌ No videos found either. The date filter might be completely blocked for this key/IP.")
            return

        # 3. Check Channel Creation Dates
        print("\n🕵️  Checking if these videos belong to NEW channels...")
        
        channel_ids = list(set([v['snippet']['channelId'] for v in videos]))
        
        # Get Channel Details
        ch_req = youtube.channels().list(
            part="snippet,statistics",
            id=",".join(channel_ids)
        )
        ch_res = youtube_api.execute_request(ch_req)
        channels = ch_res.get('items', [])
        
        new_channels_found = 0
        
        for ch in channels:
            created_at = ch['snippet']['publishedAt']
            title = ch['snippet']['title']
            
            # Simple check: Is creation date >= Jan 1 2026?
            if created_at >= "2026-01-01":
                print(f"🎉 FOUND NEW CREATOR: {title}")
                print(f"   - Created: {created_at}")
                print(f"   - Video Count: {ch['statistics']['videoCount']}")
                new_channels_found += 1
            else:
                print(f"   (Old Channel): {title} (Created {created_at})")
                
        print(f"\n📊 Summary: Found {new_channels_found} new channels out of {len(channels)} active uploaders.")
        
        if new_channels_found > 0:
            print("\n✅ CONCLUSION: Video-First Discovery WORKS. We should pivot the strategy.")
        else:
            print("\n⚠️ CONCLUSION: Videos found, but all from old channels. Might need to search deeper or filter better.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_test_v2()
