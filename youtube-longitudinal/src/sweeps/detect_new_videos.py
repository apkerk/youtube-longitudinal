"""
detect_new_videos.py
--------------------
New Video Detection Logic

Identifies newly uploaded videos since last sweep by comparing video counts
and fetching the most recent videos from the uploads playlist.

Usage:
    Typically called from sweep_channels.py, but can be run standalone:
    python -m src.sweeps.detect_new_videos --channel-id UC... --last-count 10

Author: Katie Apker
Last Updated: Feb 02, 2026
"""

import argparse
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    detect_new_videos as api_detect_new_videos,
    get_video_details_batch,
)
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewVideoDetector:
    """
    Handles detection and collection of newly uploaded videos.
    """
    
    def __init__(self, youtube):
        """
        Initialize detector.
        
        Args:
            youtube: Authenticated YouTube API service
        """
        self.youtube = youtube
        
    def detect_for_channel(
        self,
        channel_id: str,
        uploads_playlist_id: str,
        last_video_count: int,
        current_video_count: int,
        known_video_ids: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Detect new videos for a single channel.
        
        Args:
            channel_id: Channel ID
            uploads_playlist_id: Uploads playlist ID
            last_video_count: Video count from previous sweep
            current_video_count: Current video count
            known_video_ids: Set of already-known video IDs
            
        Returns:
            List of new video IDs
        """
        return api_detect_new_videos(
            youtube=self.youtube,
            channel_id=channel_id,
            uploads_playlist_id=uploads_playlist_id,
            last_video_count=last_video_count,
            current_video_count=current_video_count,
            known_video_ids=list(known_video_ids) if known_video_ids else None
        )
        
    def fetch_video_details(
        self,
        video_ids: List[str],
        trigger_type: str = "new_video_detection"
    ) -> List[Dict]:
        """
        Fetch full details for a list of video IDs.
        
        Args:
            video_ids: List of video IDs
            trigger_type: Reason for fetching
            
        Returns:
            List of video detail dictionaries
        """
        return get_video_details_batch(
            youtube=self.youtube,
            video_ids=video_ids,
            trigger_type=trigger_type
        )
        
    def batch_detect_from_sweep_data(
        self,
        current_sweep: List[Dict],
        previous_sweep: List[Dict],
        stream_name: str
    ) -> Dict[str, List[str]]:
        """
        Batch detect new videos by comparing sweep data.
        
        Args:
            current_sweep: List of channel stats from current sweep
            previous_sweep: List of channel stats from previous sweep
            stream_name: Stream identifier
            
        Returns:
            Dictionary mapping channel_id to list of new video IDs
        """
        # Build lookup for previous stats
        previous_by_id = {ch['channel_id']: ch for ch in previous_sweep}
        
        new_videos_by_channel: Dict[str, List[str]] = {}
        
        for current in current_sweep:
            channel_id = current['channel_id']
            previous = previous_by_id.get(channel_id)
            
            if not previous:
                continue
                
            prev_count = int(previous.get('video_count', 0))
            curr_count = int(current.get('video_count', 0) or 0)
            
            if curr_count > prev_count:
                # Convert channel ID to uploads playlist ID
                uploads_playlist = f"UU{channel_id[2:]}"
                
                new_ids = self.detect_for_channel(
                    channel_id=channel_id,
                    uploads_playlist_id=uploads_playlist,
                    last_video_count=prev_count,
                    current_video_count=curr_count
                )
                
                if new_ids:
                    new_videos_by_channel[channel_id] = new_ids
                    logger.info(f"Channel {channel_id}: {len(new_ids)} new videos")
                    
        return new_videos_by_channel


def load_sweep_file(filepath: Path) -> List[Dict]:
    """Load a sweep CSV file into a list of dictionaries."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    """Standalone new video detection."""
    parser = argparse.ArgumentParser(description="New Video Detection")
    parser.add_argument('--channel-id', type=str, help='Single channel ID to check')
    parser.add_argument('--last-count', type=int, help='Last known video count')
    parser.add_argument('--current-sweep', type=str, help='Current sweep CSV file')
    parser.add_argument('--previous-sweep', type=str, help='Previous sweep CSV file')
    args = parser.parse_args()
    
    config.ensure_directories()
    youtube = get_authenticated_service()
    detector = NewVideoDetector(youtube)
    
    if args.channel_id and args.last_count is not None:
        # Single channel mode
        uploads_playlist = f"UU{args.channel_id[2:]}"
        
        # Get current video count (would need an API call in real usage)
        logger.info(f"Checking channel {args.channel_id}")
        
        # For demo, we'd need current count - skip for now
        logger.warning("Single channel mode requires current video count. Use --current-sweep and --previous-sweep for batch mode.")
        
    elif args.current_sweep and args.previous_sweep:
        # Batch mode from files
        current = load_sweep_file(Path(args.current_sweep))
        previous = load_sweep_file(Path(args.previous_sweep))
        
        new_videos = detector.batch_detect_from_sweep_data(
            current_sweep=current,
            previous_sweep=previous,
            stream_name="manual"
        )
        
        # Flatten and fetch details
        all_new_ids = []
        for channel_videos in new_videos.values():
            all_new_ids.extend(channel_videos)
            
        if all_new_ids:
            logger.info(f"Fetching details for {len(all_new_ids)} new videos")
            details = detector.fetch_video_details(all_new_ids)
            
            # Save to CSV
            output_path = config.VIDEOS_DIR / f"new_videos_{config.get_date_stamp()}.csv"
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=config.VIDEO_FIELDS)
                writer.writeheader()
                for v in details:
                    row = {field: v.get(field) for field in config.VIDEO_FIELDS}
                    writer.writerow(row)
                    
            logger.info(f"💾 Saved to {output_path}")
        else:
            logger.info("No new videos detected")
            
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

