import sys
import os
import discover_cohort
import youtube_api

def run_test():
    print("🧪 STARTING DIAGNOSTIC TEST")
    print("-------------------------")
    
    # 1. Authenticate
    try:
        youtube = youtube_api.get_authenticated_service()
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # STEP 0: SANITY CHECK (Does the API work at all?)
    print("\n[Step 0] Sanity Check: Searching for 'Google' (No date limits)...")
    try:
        sanity_req = youtube.search().list(
            part="snippet",
            q="Google",
            type="channel",
            maxResults=3
        )
        sanity_res = sanity_req.execute()
        print(f"✅ Sanity Check Passed! Found {len(sanity_res.get('items', []))} channels.")
        for item in sanity_res.get('items', []):
            print(f"   - Found: {item['snippet']['title']}")
    except Exception as e:
        print(f"❌ Sanity Check Failed: {e}")
        return

    # STEP 1: COHORT DISCOVERY (The Real Test)
    # Trying multiple strategies since Wildcard failed
    print("\n[Step 1] Testing Time-Window Search (Jan 1, 2026, 00:00-06:00)")
    start_time = "2026-01-01T00:00:00Z"
    end_time = "2026-01-01T06:00:00Z"
    
    strategies = [
        {"name": "Common Letter 'a'", "q": "a"},
        {"name": "Common Word 'video'", "q": "video"},
        {"name": "Empty Query + Date Sort", "q": "", "order": "date"}
    ]
    
    found_any = False
    
    for strat in strategies:
        print(f"\n🔎 Testing Strategy: {strat['name']}")
        try:
            # Build args dynamically
            kwargs = {
                "part": "snippet",
                "type": "channel",
                "publishedAfter": start_time,
                "publishedBefore": end_time,
                "maxResults": 10,
                "regionCode": None
            }
            if strat.get("q"):
                kwargs["q"] = strat["q"]
            if strat.get("order"):
                kwargs["order"] = strat["order"]
                
            request = youtube.search().list(**kwargs)
            response = youtube_api.execute_request(request)
            results = response.get('items', [])
            
            print(f"   found {len(results)} raw channels.")
            
            if results:
                found_any = True
                print("   ✅ SUCCESS! Capturing first result...")
                
                # 4. Run Filter on the first batch found
                print(f"🕵️  Filtering {len(results)} channels for viability...")
                channel_ids = [ch['snippet']['channelId'] for ch in results]
                viable_channels = discover_cohort.get_channel_details(youtube, channel_ids)
                
                print(f"🎉 Test Passed with strategy: {strat['name']}")
                
                # 5. Show Preview
                if viable_channels:
                    print("\n--- PREVIEW OF CAPTURED DATA ---")
                    for ch in viable_channels[:3]:
                        print(f"Name: {ch['title']}")
                        print(f"  - Created: {ch['published_at']}")
                        print(f"  - Videos: {ch['video_count']}")
                        print("--------------------------------")
                return # Exit after first success
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    if not found_any:
        print("\n❌ All strategies failed to find channels.")

if __name__ == "__main__":
    run_test()
