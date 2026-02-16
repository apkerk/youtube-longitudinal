"""
daily_stats.py
--------------
Daily panel statistics collection engine.

Collects current view/like/comment counts for all videos and
subscriber/view/video counts for all channels in the gender gap panel.
Detects new videos and appends them to the inventory.

Usage:
    python -m src.panels.daily_stats \
        --video-inventory data/video_inventory/gender_gap_inventory.csv \
        [--test] [--limit N]

Author: Katie Apker
Last Updated: Feb 16, 2026
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    get_video_stats_batch,
    get_channel_stats_only,
    detect_new_videos,
    chunks,
)
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOGS_DIR / f'daily_stats_{config.get_date_stamp()}.log')
    ]
)
logger = logging.getLogger(__name__)


class DailyStatsCollector:
    """
    Daily panel collection engine for the gender gap longitudinal study.

    Collects video-level and channel-level statistics, detects new videos,
    and appends them to the inventory. Supports checkpoint/resume.
    """

    def __init__(self, youtube, inventory_path: Path):
        """
        Args:
            youtube: Authenticated YouTube API service
            inventory_path: Path to video inventory CSV
        """
        self.youtube = youtube
        self.inventory_path = inventory_path
        self.today = datetime.utcnow().strftime("%Y-%m-%d")
        self.checkpoint_path = config.DAILY_PANELS_DIR / ".daily_stats_checkpoint.json"

    def load_inventory(self) -> Tuple[List[str], List[str]]:
        """
        Load video inventory CSV.

        Returns:
            Tuple of (video_ids, sorted unique channel_ids)
        """
        video_ids = []
        channel_ids_set = set()

        with open(self.inventory_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vid = row.get('video_id', '').strip()
                cid = row.get('channel_id', '').strip()
                if vid:
                    video_ids.append(vid)
                if cid:
                    channel_ids_set.add(cid)

        channel_ids = sorted(channel_ids_set)
        logger.info(f"Loaded inventory: {len(video_ids)} videos, {len(channel_ids)} channels")
        return video_ids, channel_ids

    def load_checkpoint(self) -> Dict:
        """
        Load checkpoint. Only valid if checkpoint date matches today.

        Returns:
            Checkpoint dict (fresh if stale or missing)
        """
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)

            if checkpoint.get('date') == self.today:
                logger.info(
                    f"Resuming from checkpoint: "
                    f"{checkpoint.get('video_batches_done', 0)} video batches done, "
                    f"channel_stats_done={checkpoint.get('channel_stats_done', False)}"
                )
                return checkpoint

            logger.info("Stale checkpoint found (different date), starting fresh")

        return {
            'date': self.today,
            'video_batches_done': 0,
            'channel_stats_done': False,
            'new_video_detection_done': False,
        }

    def save_checkpoint(self, checkpoint: Dict) -> None:
        """Save checkpoint to disk."""
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f)

    def clear_checkpoint(self) -> None:
        """Remove checkpoint file after successful completion."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()

    def collect_video_stats(
        self,
        video_ids: List[str],
        checkpoint: Dict,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        Batch-fetch video statistics with checkpoint/resume.

        Args:
            video_ids: Full list of video IDs
            checkpoint: Current checkpoint dict
            limit: If set, only process first N video IDs

        Returns:
            List of video stats dicts
        """
        if limit is not None:
            video_ids = video_ids[:limit]

        batches = list(chunks(video_ids, 50))
        total_batches = len(batches)
        start_batch = checkpoint.get('video_batches_done', 0)

        # If resuming, reload partial results from today's output file
        all_stats: List[Dict] = []
        if start_batch > 0:
            partial_path = config.get_daily_panel_path('video_stats', self.today)
            if partial_path.exists():
                with open(partial_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        all_stats.append(row)
                logger.info(f"Loaded {len(all_stats)} partial results from {partial_path.name}")

        logger.info(
            f"Collecting video stats: {total_batches} batches "
            f"(starting at batch {start_batch})"
        )

        for batch_idx in range(start_batch, total_batches):
            batch = batches[batch_idx]
            try:
                batch_stats = get_video_stats_batch(self.youtube, batch)
                all_stats.extend(batch_stats)
            except Exception as e:
                logger.error(f"Error fetching video stats batch {batch_idx}: {e}")

            # Update checkpoint after each batch
            checkpoint['video_batches_done'] = batch_idx + 1
            self.save_checkpoint(checkpoint)

            # Progress logging every 100 batches
            if (batch_idx + 1) % 100 == 0 or (batch_idx + 1) == total_batches:
                logger.info(
                    f"Video stats progress: {batch_idx + 1}/{total_batches} batches "
                    f"({len(all_stats)} stats collected)"
                )

        return all_stats

    def collect_channel_stats(self, channel_ids: List[str]) -> List[Dict]:
        """
        Fetch channel statistics. get_channel_stats_only handles batching internally.

        Args:
            channel_ids: List of channel IDs

        Returns:
            List of channel stats dicts
        """
        logger.info(f"Collecting channel stats for {len(channel_ids)} channels")
        stats = get_channel_stats_only(self.youtube, channel_ids)
        logger.info(f"Collected stats for {len(stats)} channels")
        return stats

    def detect_and_add_new_videos(
        self,
        channel_stats: List[Dict],
        previous_channel_stats_path: Optional[Path],
    ) -> List[Dict]:
        """
        Compare today's video_count with yesterday's. For channels with increases,
        detect new video IDs and append them to the inventory.

        Args:
            channel_stats: Today's channel stats
            previous_channel_stats_path: Path to yesterday's channel stats CSV (or None)

        Returns:
            List of newly detected video entries
        """
        if previous_channel_stats_path is None or not previous_channel_stats_path.exists():
            logger.info("No previous channel stats found, skipping new video detection")
            return []

        # Build lookup of yesterday's video counts
        prev_counts: Dict[str, int] = {}
        with open(previous_channel_stats_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get('channel_id', '').strip()
                vc = row.get('video_count')
                if cid and vc is not None:
                    try:
                        prev_counts[cid] = int(vc)
                    except (ValueError, TypeError):
                        pass

        # Load known video IDs from inventory for filtering
        known_video_ids: set = set()
        if self.inventory_path.exists():
            with open(self.inventory_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    vid = row.get('video_id', '').strip()
                    if vid:
                        known_video_ids.add(vid)

        new_entries: List[Dict] = []
        channels_with_new = 0

        for ch in channel_stats:
            cid = ch.get('channel_id', '')
            if not cid or ch.get('status') == 'not_found':
                continue

            curr_count = int(ch.get('video_count', 0) or 0)
            prev_count = prev_counts.get(cid)

            if prev_count is None or curr_count <= prev_count:
                continue

            # Channel has new videos. Detect them.
            uploads_playlist_id = f"UU{cid[2:]}" if cid.startswith('UC') else None
            if not uploads_playlist_id:
                continue

            try:
                new_video_ids = detect_new_videos(
                    youtube=self.youtube,
                    channel_id=cid,
                    uploads_playlist_id=uploads_playlist_id,
                    last_video_count=prev_count,
                    current_video_count=curr_count,
                    known_video_ids=list(known_video_ids),
                )

                if new_video_ids:
                    channels_with_new += 1
                    scraped_at = datetime.utcnow().isoformat()
                    for vid in new_video_ids:
                        entry = {
                            'video_id': vid,
                            'channel_id': cid,
                            'published_at': None,
                            'title': None,
                            'scraped_at': scraped_at,
                        }
                        new_entries.append(entry)
                        known_video_ids.add(vid)

            except Exception as e:
                logger.error(f"Error detecting new videos for {cid}: {e}")

        if new_entries:
            # Append new entries to the inventory file
            with open(self.inventory_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=config.VIDEO_INVENTORY_FIELDS)
                for entry in new_entries:
                    row = {field: entry.get(field) for field in config.VIDEO_INVENTORY_FIELDS}
                    writer.writerow(row)
            logger.info(
                f"Detected {len(new_entries)} new videos from "
                f"{channels_with_new} channels, appended to inventory"
            )
        else:
            logger.info("No new videos detected")

        return new_entries

    def save_daily_stats(
        self,
        video_stats: List[Dict],
        channel_stats: List[Dict],
    ) -> Tuple[Path, Path]:
        """
        Write daily panel CSVs for video stats and channel stats.

        Args:
            video_stats: List of video stats dicts
            channel_stats: List of channel stats dicts

        Returns:
            Tuple of (video_stats_path, channel_stats_path)
        """
        video_path = config.get_daily_panel_path('video_stats', self.today)
        channel_path = config.get_daily_panel_path('channel_stats', self.today)

        # Write video stats
        with open(video_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.VIDEO_STATS_FIELDS)
            writer.writeheader()
            for s in video_stats:
                row = {field: s.get(field) for field in config.VIDEO_STATS_FIELDS}
                writer.writerow(row)
        logger.info(f"Saved {len(video_stats)} video stats to {video_path.name}")

        # Write channel stats
        with open(channel_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_STATS_FIELDS)
            writer.writeheader()
            for s in channel_stats:
                row = {field: s.get(field) for field in config.CHANNEL_STATS_FIELDS}
                writer.writerow(row)
        logger.info(f"Saved {len(channel_stats)} channel stats to {channel_path.name}")

        return video_path, channel_path

    def run(self, test_mode: bool = False, limit: Optional[int] = None) -> Dict:
        """
        Execute full daily collection pipeline.

        Steps:
            1. Load inventory
            2. Load/validate checkpoint
            3. Collect video stats (with checkpoint)
            4. Collect channel stats (if not done per checkpoint)
            5. Save daily panel files
            6. Detect new videos and update inventory (if not done per checkpoint)
            7. Clear checkpoint on success

        Args:
            test_mode: If True, default limit to 250 video IDs
            limit: Max video IDs to process

        Returns:
            Summary dict with counts and paths
        """
        if test_mode and limit is None:
            limit = 250

        # Step 1: Load inventory
        video_ids, channel_ids = self.load_inventory()

        if not video_ids:
            logger.warning("No video IDs in inventory, nothing to collect")
            return {'success': False, 'error': 'Empty inventory'}

        # Step 2: Load checkpoint
        checkpoint = self.load_checkpoint()

        # Step 3: Collect video stats
        video_stats = self.collect_video_stats(video_ids, checkpoint, limit=limit)

        # Step 4: Collect channel stats
        if not checkpoint.get('channel_stats_done', False):
            channel_stats = self.collect_channel_stats(channel_ids)
            checkpoint['channel_stats_done'] = True
            self.save_checkpoint(checkpoint)
        else:
            # Reload from today's saved file if checkpoint says done
            channel_stats_path = config.get_daily_panel_path('channel_stats', self.today)
            channel_stats = []
            if channel_stats_path.exists():
                with open(channel_stats_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        channel_stats.append(row)
                logger.info(f"Reloaded {len(channel_stats)} channel stats from {channel_stats_path.name}")

        # Step 5: Save daily panel files
        video_path, channel_path = self.save_daily_stats(video_stats, channel_stats)

        # Step 6: Detect new videos
        new_videos = []
        if not checkpoint.get('new_video_detection_done', False):
            yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            prev_channel_path = config.get_daily_panel_path('channel_stats', yesterday_str)

            new_videos = self.detect_and_add_new_videos(channel_stats, prev_channel_path)

            checkpoint['new_video_detection_done'] = True
            self.save_checkpoint(checkpoint)
        else:
            logger.info("New video detection already done per checkpoint")

        # Step 7: Clear checkpoint on success
        self.clear_checkpoint()

        summary = {
            'success': True,
            'date': self.today,
            'video_stats_collected': len(video_stats),
            'channel_stats_collected': len(channel_stats),
            'new_videos_detected': len(new_videos),
            'video_stats_path': str(video_path),
            'channel_stats_path': str(channel_path),
        }
        return summary


def main():
    """CLI entry point for daily stats collection."""
    parser = argparse.ArgumentParser(
        description="Daily panel statistics collection engine"
    )
    parser.add_argument(
        '--video-inventory', type=str, required=True,
        help='Path to video inventory CSV (e.g., data/video_inventory/gender_gap_inventory.csv)'
    )
    parser.add_argument('--test', action='store_true', help='Test mode (limit to 250 video IDs)')
    parser.add_argument('--limit', type=int, default=None, help='Max video IDs to process')
    args = parser.parse_args()

    # Ensure directories exist
    config.ensure_directories()

    # Resolve inventory path
    inventory_path = Path(args.video_inventory)
    if not inventory_path.is_absolute():
        inventory_path = config.PROJECT_ROOT / inventory_path

    logger.info("=" * 60)
    logger.info("DAILY PANEL STATISTICS COLLECTION")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"Inventory: {inventory_path}")
    logger.info(f"Test mode: {args.test}")
    if args.limit:
        logger.info(f"Limit: {args.limit}")
    logger.info("=" * 60)

    if not inventory_path.exists():
        logger.error(f"Inventory file not found: {inventory_path}")
        sys.exit(1)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        collector = DailyStatsCollector(youtube, inventory_path)
        summary = collector.run(test_mode=args.test, limit=args.limit)

        logger.info("=" * 60)
        logger.info("DAILY COLLECTION COMPLETE")
        logger.info(f"Date: {summary.get('date')}")
        logger.info(f"Video stats: {summary.get('video_stats_collected')}")
        logger.info(f"Channel stats: {summary.get('channel_stats_collected')}")
        logger.info(f"New videos detected: {summary.get('new_videos_detected')}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Daily collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
