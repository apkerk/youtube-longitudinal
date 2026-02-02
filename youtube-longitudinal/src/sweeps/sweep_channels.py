"""
sweep_channels.py
-----------------
Longitudinal Sweep Script

Performs periodic data collection sweeps on existing channel pools.
Collects updated metrics and detects new video uploads.

Features:
- Checkpoint/resume on interruption
- New video detection
- Status change tracking (deleted, private, terminated)
- Policy flag change detection (made_for_kids)
- Configurable frequency per stream

Usage:
    python -m src.sweeps.sweep_channels --stream stream_a
    python -m src.sweeps.sweep_channels --all

Author: Katie Apker
Last Updated: Feb 02, 2026
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    get_channel_stats_only,
    get_video_details_batch,
    detect_new_videos,
)
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOGS_DIR / f'sweep_{config.get_date_stamp()}.log')
    ]
)
logger = logging.getLogger(__name__)


class ChannelSweeper:
    """
    Handles longitudinal sweeps of channel pools.
    """
    
    def __init__(self, youtube, stream_name: str):
        """
        Initialize sweeper for a specific stream.
        
        Args:
            youtube: Authenticated YouTube API service
            stream_name: Stream identifier (stream_a, stream_b, etc.)
        """
        self.youtube = youtube
        self.stream_name = stream_name
        self.stream_dir = config.STREAM_DIRS[stream_name]
        self.checkpoint_path = self.stream_dir / ".sweep_checkpoint.json"
        
    def get_latest_data_file(self) -> Optional[Path]:
        """Find the most recent data file for this stream."""
        files = sorted(self.stream_dir.glob("*.csv"), reverse=True)
        return files[0] if files else None
        
    def load_channel_list(self) -> List[Dict]:
        """
        Load channel list from the most recent data file.
        
        Returns:
            List of channel dictionaries with at least channel_id
        """
        latest_file = self.get_latest_data_file()
        if not latest_file:
            logger.warning(f"No data file found for {self.stream_name}")
            return []
            
        logger.info(f"Loading channels from {latest_file.name}")
        
        channels = []
        with open(latest_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                channels.append(row)
                
        return channels
        
    def load_checkpoint(self) -> Dict:
        """Load checkpoint data for resume capability."""
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'processed_ids': [], 'results': []}
        
    def save_checkpoint(self, data: Dict) -> None:
        """Save checkpoint data."""
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
    def clear_checkpoint(self) -> None:
        """Remove checkpoint file after successful completion."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
            
    def sweep(self, detect_videos: bool = True, resume: bool = True) -> Dict:
        """
        Perform a sweep of all channels in this stream.
        
        Args:
            detect_videos: Whether to detect and fetch new videos
            resume: Whether to resume from checkpoint
            
        Returns:
            Dictionary with sweep results and stats
        """
        # Load channels
        channels = self.load_channel_list()
        if not channels:
            return {'success': False, 'error': 'No channels to sweep'}
            
        logger.info(f"Starting sweep of {len(channels)} channels")
        
        # Load checkpoint if resuming
        checkpoint = self.load_checkpoint() if resume else {'processed_ids': [], 'results': []}
        processed_ids = set(checkpoint['processed_ids'])
        results = checkpoint['results']
        
        # Build lookup for previous stats
        previous_stats = {ch['channel_id']: ch for ch in channels}
        
        # Filter to unprocessed channels
        remaining_ids = [
            ch['channel_id'] for ch in channels 
            if ch['channel_id'] not in processed_ids
        ]
        
        if processed_ids:
            logger.info(f"Resuming: {len(processed_ids)} already processed, {len(remaining_ids)} remaining")
            
        # Process in batches
        new_videos = []
        batch_size = 50
        
        for i in range(0, len(remaining_ids), batch_size):
            batch = remaining_ids[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} channels)")
            
            try:
                # Get current stats
                current_stats = get_channel_stats_only(self.youtube, batch)
                
                for stats in current_stats:
                    channel_id = stats['channel_id']
                    prev = previous_stats.get(channel_id, {})
                    
                    # Check for made_for_kids change
                    prev_mfk = prev.get('made_for_kids')
                    curr_mfk = stats.get('made_for_kids')
                    mfk_changed = (prev_mfk is not None and prev_mfk != curr_mfk)
                    
                    stats['made_for_kids_changed'] = mfk_changed
                    results.append(stats)
                    
                    # Detect new videos if enabled
                    if detect_videos and stats.get('status') == 'active':
                        prev_video_count = int(prev.get('video_count', 0))
                        curr_video_count = int(stats.get('video_count', 0))
                        
                        if curr_video_count > prev_video_count:
                            # Get uploads playlist ID (convert channel ID to playlist format)
                            uploads_playlist = f"UU{channel_id[2:]}"
                            
                            new_video_ids = detect_new_videos(
                                youtube=self.youtube,
                                channel_id=channel_id,
                                uploads_playlist_id=uploads_playlist,
                                last_video_count=prev_video_count,
                                current_video_count=curr_video_count
                            )
                            
                            if new_video_ids:
                                new_videos.extend(new_video_ids)
                                logger.info(f"  Detected {len(new_video_ids)} new videos from {channel_id}")
                    
                    processed_ids.add(channel_id)
                    
                # Save checkpoint after each batch
                checkpoint['processed_ids'] = list(processed_ids)
                checkpoint['results'] = results
                self.save_checkpoint(checkpoint)
                
            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                # Continue to next batch
                
        # Fetch details for new videos
        video_details = []
        if new_videos:
            logger.info(f"Fetching details for {len(new_videos)} new videos")
            video_details = get_video_details_batch(
                self.youtube, 
                new_videos, 
                trigger_type="new_video_detection"
            )
            
        # Calculate summary stats
        summary = self._calculate_summary(results, previous_stats)
        
        # Save results
        self._save_sweep_results(results)
        
        if video_details:
            self._save_new_videos(video_details)
            
        # Clear checkpoint on success
        self.clear_checkpoint()
        
        return {
            'success': True,
            'channels_processed': len(results),
            'new_videos_detected': len(video_details),
            'summary': summary
        }
        
    def _calculate_summary(self, results: List[Dict], previous: Dict[str, Dict]) -> Dict:
        """Calculate summary statistics for the sweep."""
        summary = {
            'total_channels': len(results),
            'active': 0,
            'not_found': 0,
            'made_for_kids_changed': 0,
            'video_count_increased': 0,
            'video_count_decreased': 0,
            'subscriber_increased': 0,
            'subscriber_decreased': 0,
        }
        
        for r in results:
            if r.get('status') == 'active':
                summary['active'] += 1
            elif r.get('status') == 'not_found':
                summary['not_found'] += 1
                
            if r.get('made_for_kids_changed'):
                summary['made_for_kids_changed'] += 1
                
            prev = previous.get(r['channel_id'], {})
            
            prev_videos = int(prev.get('video_count', 0))
            curr_videos = int(r.get('video_count', 0) or 0)
            if curr_videos > prev_videos:
                summary['video_count_increased'] += 1
            elif curr_videos < prev_videos:
                summary['video_count_decreased'] += 1
                
            prev_subs = int(prev.get('subscriber_count', 0))
            curr_subs = int(r.get('subscriber_count', 0) or 0)
            if curr_subs > prev_subs:
                summary['subscriber_increased'] += 1
            elif curr_subs < prev_subs:
                summary['subscriber_decreased'] += 1
                
        return summary
        
    def _save_sweep_results(self, results: List[Dict]) -> None:
        """Save sweep results to CSV."""
        date_stamp = config.get_date_stamp()
        output_path = self.stream_dir / f"sweep_{date_stamp}.csv"
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_SWEEP_FIELDS)
            writer.writeheader()
            
            for r in results:
                row = {field: r.get(field) for field in config.CHANNEL_SWEEP_FIELDS}
                writer.writerow(row)
                
        logger.info(f"💾 Saved sweep results to {output_path}")
        
    def _save_new_videos(self, videos: List[Dict]) -> None:
        """Save new video details to CSV."""
        date_stamp = config.get_date_stamp()
        output_path = config.VIDEOS_DIR / f"new_videos_{date_stamp}.csv"
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.VIDEO_FIELDS)
            writer.writeheader()
            
            for v in videos:
                row = {field: v.get(field) for field in config.VIDEO_FIELDS}
                writer.writerow(row)
                
        logger.info(f"💾 Saved {len(videos)} new videos to {output_path}")


def run_sweep_for_stream(stream_name: str, detect_videos: bool = True) -> Dict:
    """
    Run a sweep for a single stream.
    
    Args:
        stream_name: Stream to sweep
        detect_videos: Whether to detect new videos
        
    Returns:
        Sweep results dictionary
    """
    logger.info(f"🔄 Starting sweep for {stream_name}")
    
    try:
        youtube = get_authenticated_service()
        sweeper = ChannelSweeper(youtube, stream_name)
        results = sweeper.sweep(detect_videos=detect_videos)
        
        logger.info(f"✅ Completed sweep for {stream_name}")
        logger.info(f"   Channels: {results.get('channels_processed', 0)}")
        logger.info(f"   New videos: {results.get('new_videos_detected', 0)}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Sweep failed for {stream_name}: {e}")
        return {'success': False, 'error': str(e)}


def main():
    """Main entry point for sweep operations."""
    parser = argparse.ArgumentParser(description="Longitudinal Channel Sweep")
    parser.add_argument('--stream', type=str, choices=list(config.STREAM_DIRS.keys()),
                        help='Specific stream to sweep')
    parser.add_argument('--all', action='store_true', help='Sweep all streams')
    parser.add_argument('--no-videos', action='store_true', 
                        help='Skip new video detection')
    args = parser.parse_args()
    
    # Ensure directories exist
    config.ensure_directories()
    
    logger.info("=" * 60)
    logger.info("🔄 LONGITUDINAL SWEEP")
    logger.info(f"📅 {datetime.utcnow().isoformat()}")
    logger.info("=" * 60)
    
    detect_videos = not args.no_videos
    
    if args.all:
        # Sweep all streams
        all_results = {}
        for stream_name in config.STREAM_DIRS.keys():
            results = run_sweep_for_stream(stream_name, detect_videos)
            all_results[stream_name] = results
            
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 SWEEP SUMMARY")
        logger.info("=" * 60)
        for stream, res in all_results.items():
            status = "✅" if res.get('success') else "❌"
            logger.info(f"{status} {stream}: {res.get('channels_processed', 0)} channels")
            
    elif args.stream:
        run_sweep_for_stream(args.stream, detect_videos)
        
    else:
        parser.print_help()
        logger.warning("Please specify --stream or --all")


if __name__ == "__main__":
    main()

