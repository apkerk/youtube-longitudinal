"""
daily_stats.py
--------------
Panel statistics collection engine (dual-cadence design).

Two collection modes run on separate schedules:
  - Channel stats (daily):  subscriber/view/video counts for all channels
  - Video stats (weekly):   view/like/comment counts for all videos in inventory

The --mode flag controls which stats to collect:
  --mode channel   Channel-level only (daily via launchd)
  --mode video     Video-level only (weekly via launchd)
  --mode both      Both in one run (default, for manual/test runs)

See docs/PANEL_SCHEMA.md for the full dual-cadence design rationale.

Usage:
    # Channel stats only (reads channel IDs directly, no inventory needed):
    python -m src.panels.daily_stats \
        --channel-list data/channels/gender_gap/channel_ids.csv \
        --mode channel [--test] [--limit N]

    # Video or both modes (requires video inventory):
    python -m src.panels.daily_stats \
        --video-inventory data/video_inventory/gender_gap_inventory.csv \
        [--mode channel|video|both] [--test] [--limit N]

Author: Katie Apker
Last Updated: Feb 17, 2026
"""

import argparse
import csv
import json
import logging
import socket
import sys
import time
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

logger = logging.getLogger(__name__)

# Retry backoff schedule: 30s, 120s, 480s (per deployment plan A.0.2)
_RETRY_BACKOFF = (30, 120, 480)


def _call_with_retry(fn, description="API call", max_retries=3):
    """Retry fn() on transient network errors with exponential backoff.

    Catches socket.timeout, ConnectionError, and OSError (network-level failures
    that execute_request in youtube_api.py does not handle).
    HTTP-level errors (403, 503, etc.) are handled by execute_request's own retry.
    """
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except (socket.timeout, ConnectionError, OSError) as e:
            if attempt < max_retries:
                wait = _RETRY_BACKOFF[attempt]
                logger.warning(
                    "%s: %s, retry %d/%d in %ds",
                    description, type(e).__name__, attempt + 1, max_retries, wait,
                )
                time.sleep(wait)
                continue
            raise


def _write_sentinel(date_str, error_msg):
    """Write a failure sentinel file for the health check to detect."""
    sentinel_path = config.LOGS_DIR / "daily_stats_FAILED_{}.flag".format(date_str)
    sentinel_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sentinel_path, 'w', encoding='utf-8') as f:
        f.write("Failed at: {}\n".format(datetime.utcnow().isoformat()))
        f.write("Error: {}\n".format(error_msg))
    logger.error("Wrote failure sentinel: %s", sentinel_path)


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'daily_stats_{config.get_date_stamp()}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )


class DailyStatsCollector:
    """
    Daily panel collection engine for the gender gap longitudinal study.

    Collects video-level and channel-level statistics, detects new videos,
    and appends them to the inventory. Supports checkpoint/resume.
    """

    def __init__(
        self,
        youtube,
        inventory_path: Optional[Path] = None,
        channel_list_path: Optional[Path] = None,
        panel_name: Optional[str] = None,
        date_override: Optional[str] = None,
    ):
        """
        Args:
            youtube: Authenticated YouTube API service
            inventory_path: Path to video inventory CSV (required for video/both modes)
            channel_list_path: Path to a CSV with a channel_id column (optional;
                used for channel-only mode to bypass the video inventory)
            panel_name: Optional panel subdirectory name (e.g., 'new_cohort').
                When set, output goes to channel_stats/{panel_name}/YYYY-MM-DD.csv.
                When None, uses the flat default (backwards compatible).
            date_override: Override collection date (YYYY-MM-DD) for backfilling.
                When set, output files use this date instead of today.
        """
        self.youtube = youtube
        self.inventory_path = inventory_path
        self.channel_list_path = channel_list_path
        self.panel_name = panel_name
        self.date_override = date_override
        self.today = date_override if date_override else datetime.utcnow().strftime("%Y-%m-%d")
        checkpoint_suffix = f"_{panel_name}" if panel_name else ""
        self.checkpoint_path = config.DAILY_PANELS_DIR / f".daily_stats_checkpoint{checkpoint_suffix}.json"

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

    def load_channel_list(self) -> List[str]:
        """
        Load channel IDs from a standalone channel list CSV.

        The file must have a 'channel_id' column. Other columns are ignored.

        Returns:
            Sorted list of unique channel IDs
        """
        if self.channel_list_path is None:
            raise ValueError("channel_list_path not set")

        channel_ids_set: set = set()
        with open(self.channel_list_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get('channel_id', '').strip()
                if cid:
                    channel_ids_set.add(cid)

        channel_ids = sorted(channel_ids_set)
        logger.info(f"Loaded channel list: {len(channel_ids)} channels from {self.channel_list_path.name}")
        return channel_ids

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
            partial_path = config.get_daily_panel_path('video_stats', self.today, panel_name=self.panel_name)
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
                batch_stats = _call_with_retry(
                    lambda b=batch: get_video_stats_batch(self.youtube, b),
                    description="video stats batch {}/{}".format(batch_idx + 1, total_batches),
                )
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
        Fetch channel statistics with retry on transient network errors.

        get_channel_stats_only handles batching internally. On network failure,
        the entire call is retried (acceptable: ~196 API calls for 9,760 channels).

        Args:
            channel_ids: List of channel IDs

        Returns:
            List of channel stats dicts
        """
        logger.info(f"Collecting channel stats for {len(channel_ids)} channels")
        stats = _call_with_retry(
            lambda: get_channel_stats_only(self.youtube, channel_ids),
            description="channel stats ({} channels)".format(len(channel_ids)),
        )
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
        if self.inventory_path is None:
            logger.info("No inventory path set, skipping new video detection")
            return []

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

    def run(
        self,
        mode: str = "both",
        test_mode: bool = False,
        limit: Optional[int] = None,
    ) -> Dict:
        """
        Execute panel collection pipeline.

        Modes:
            'channel' — channel stats only (daily schedule)
            'video'   — video stats only (weekly schedule)
            'both'    — all stats in one run (manual/test)

        Steps (filtered by mode):
            1. Load inventory
            2. Load/validate checkpoint
            3. Collect video stats (mode=video or both)
            4. Collect channel stats (mode=channel or both)
            5. Save panel files
            6. Detect new videos via channel stats diff (mode=channel or both)
            7. Clear checkpoint on success

        Args:
            mode: 'channel', 'video', or 'both'
            test_mode: If True, default limit to 250 video IDs
            limit: Max video IDs to process

        Returns:
            Summary dict with counts and paths
        """
        if test_mode and limit is None:
            limit = 250

        collect_videos = mode in ("video", "both")
        collect_channels = mode in ("channel", "both")

        # Step 1: Load channel IDs (from channel list or inventory) and video IDs
        video_ids: List[str] = []
        channel_ids: List[str] = []

        if mode == "channel" and self.channel_list_path is not None:
            # Channel-only mode with a dedicated channel list: skip inventory entirely
            channel_ids = self.load_channel_list()
        else:
            # All other cases: load from the video inventory (provides both video + channel IDs)
            video_ids, channel_ids = self.load_inventory()

        if collect_videos and not video_ids:
            logger.warning("No video IDs in inventory, nothing to collect")
            return {'success': False, 'error': 'Empty inventory'}

        # Step 2: Load checkpoint
        checkpoint = self.load_checkpoint()

        # Step 3: Collect video stats
        video_stats = []
        video_path = None
        if collect_videos:
            video_stats = self.collect_video_stats(video_ids, checkpoint, limit=limit)

        # Step 4: Collect channel stats
        channel_stats = []
        channel_path = None
        if collect_channels:
            if not checkpoint.get('channel_stats_done', False):
                channel_stats = self.collect_channel_stats(channel_ids)
                checkpoint['channel_stats_done'] = True
                self.save_checkpoint(checkpoint)
            else:
                channel_stats_path = config.get_daily_panel_path('channel_stats', self.today, panel_name=self.panel_name)
                if channel_stats_path.exists():
                    with open(channel_stats_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            channel_stats.append(row)
                    logger.info(f"Reloaded {len(channel_stats)} channel stats from {channel_stats_path.name}")

        # Step 5: Save panel files
        if collect_videos and video_stats:
            video_path = config.get_daily_panel_path('video_stats', self.today, panel_name=self.panel_name)
            with open(video_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=config.VIDEO_STATS_FIELDS)
                writer.writeheader()
                for s in video_stats:
                    row = {field: s.get(field) for field in config.VIDEO_STATS_FIELDS}
                    writer.writerow(row)
            logger.info(f"Saved {len(video_stats)} video stats to {video_path.name}")

        if collect_channels and channel_stats:
            channel_path = config.get_daily_panel_path('channel_stats', self.today, panel_name=self.panel_name)
            with open(channel_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=config.CHANNEL_STATS_FIELDS)
                writer.writeheader()
                for s in channel_stats:
                    row = {field: s.get(field) for field in config.CHANNEL_STATS_FIELDS}
                    writer.writerow(row)
            logger.info(f"Saved {len(channel_stats)} channel stats to {channel_path.name}")

        # Step 6: Detect new videos (skip on backfill — stats are current, not historical)
        new_videos = []
        if collect_channels and self.date_override is None and not checkpoint.get('new_video_detection_done', False):
            yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            prev_channel_path = config.get_daily_panel_path('channel_stats', yesterday_str, panel_name=self.panel_name)

            new_videos = self.detect_and_add_new_videos(channel_stats, prev_channel_path)

            checkpoint['new_video_detection_done'] = True
            self.save_checkpoint(checkpoint)
        elif collect_channels:
            logger.info("New video detection already done per checkpoint")

        # Step 7: Clear checkpoint on success
        self.clear_checkpoint()

        summary = {
            'success': True,
            'date': self.today,
            'mode': mode,
            'video_stats_collected': len(video_stats),
            'channel_stats_collected': len(channel_stats),
            'new_videos_detected': len(new_videos),
            'video_stats_path': str(video_path) if video_path else None,
            'channel_stats_path': str(channel_path) if channel_path else None,
        }
        return summary


def main():
    """CLI entry point for daily stats collection."""
    parser = argparse.ArgumentParser(
        description="Daily panel statistics collection engine"
    )
    parser.add_argument(
        '--video-inventory', type=str, default=None,
        help='Path to video inventory CSV (required for video/both modes)'
    )
    parser.add_argument(
        '--channel-list', type=str, default=None,
        help='Path to a CSV with a channel_id column (for channel-only mode without inventory)'
    )
    parser.add_argument(
        '--mode', type=str, default='both', choices=['channel', 'video', 'both'],
        help='Collection mode: channel (daily), video (weekly), or both (default)'
    )
    parser.add_argument('--panel-name', type=str, default=None,
        help='Panel subdirectory name (e.g., new_cohort). Output goes to channel_stats/{name}/.')
    parser.add_argument('--test', action='store_true', help='Test mode (limit to 250 video IDs)')
    parser.add_argument('--limit', type=int, default=None, help='Max video IDs to process')
    parser.add_argument('--date', type=str, default=None,
        help='Override collection date (YYYY-MM-DD) for backfilling missed days')
    args = parser.parse_args()

    # Validate --date format
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("Error: --date must be YYYY-MM-DD format", file=sys.stderr)
            sys.exit(1)

    setup_logging()
    config.ensure_directories()

    # Resolve paths
    inventory_path: Optional[Path] = None
    channel_list_path: Optional[Path] = None

    if args.video_inventory:
        inventory_path = Path(args.video_inventory)
        if not inventory_path.is_absolute():
            inventory_path = config.PROJECT_ROOT / inventory_path

    if args.channel_list:
        channel_list_path = Path(args.channel_list)
        if not channel_list_path.is_absolute():
            channel_list_path = config.PROJECT_ROOT / channel_list_path

    # Validate: video/both modes require the inventory; channel mode needs
    # either --channel-list or --video-inventory
    needs_inventory = args.mode in ("video", "both")
    has_channel_source = (channel_list_path is not None) or (inventory_path is not None)

    if needs_inventory and inventory_path is None:
        logger.error("--video-inventory is required for video or both modes")
        sys.exit(1)

    if args.mode == "channel" and not has_channel_source:
        logger.error("Channel mode requires either --channel-list or --video-inventory")
        sys.exit(1)

    # Check files exist
    if inventory_path is not None and not inventory_path.exists():
        logger.error(f"Inventory file not found: {inventory_path}")
        sys.exit(1)

    if channel_list_path is not None and not channel_list_path.exists():
        logger.error(f"Channel list file not found: {channel_list_path}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("PANEL STATISTICS COLLECTION")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"Mode: {args.mode}")
    if inventory_path:
        logger.info(f"Inventory: {inventory_path}")
    if channel_list_path:
        logger.info(f"Channel list: {channel_list_path}")
    if args.panel_name:
        logger.info(f"Panel name: {args.panel_name}")
    logger.info(f"Test mode: {args.test}")
    if args.limit:
        logger.info(f"Limit: {args.limit}")
    if args.date:
        logger.info(f"Date override: {args.date}")
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        collector = DailyStatsCollector(
            youtube,
            inventory_path=inventory_path,
            channel_list_path=channel_list_path,
            panel_name=args.panel_name,
            date_override=args.date,
        )
        summary = collector.run(mode=args.mode, test_mode=args.test, limit=args.limit)

        logger.info("=" * 60)
        logger.info("COLLECTION COMPLETE")
        logger.info(f"Date: {summary.get('date')}")
        logger.info(f"Mode: {summary.get('mode')}")
        if summary.get('video_stats_collected'):
            logger.info(f"Video stats: {summary.get('video_stats_collected')}")
        if summary.get('channel_stats_collected'):
            logger.info(f"Channel stats: {summary.get('channel_stats_collected')}")
        if summary.get('new_videos_detected'):
            logger.info(f"New videos detected: {summary.get('new_videos_detected')}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Daily collection failed: {e}")
        date_for_sentinel = args.date or datetime.utcnow().strftime("%Y-%m-%d")
        _write_sentinel(date_for_sentinel, str(e))
        raise


if __name__ == "__main__":
    main()
