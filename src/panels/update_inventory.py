"""
update_inventory.py
-------------------
Daily new video detection for panel inventories.

Reads today's and yesterday's daily channel stats CSVs, finds channels where
video_count increased, fetches new video IDs via the uploads playlist
(UU + channel_id[2:]), and appends them to the panel's inventory CSV.

Designed to run daily via launchd AFTER daily channel stats complete and
BEFORE the video enumeration service fires.

Schedule: 3:30 AM EST (after daily stats at 3:05/3:12, before enumerate at 4:00)

Usage:
    python -m src.panels.update_inventory \
        --panel gender_gap \
        [--date YYYY-MM-DD] [--test] [--limit N] \
        [--max-runtime 1800] [--reserve-quota 2000]

Author: Katie Apker
Last Updated: March 2026
"""

import argparse
import csv
import io
import json
import logging
import socket
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    get_quota_used,
    load_config,
    QuotaExhaustedError,
    execute_request,
)
import config

logger = logging.getLogger(__name__)

# Retry backoff schedule: 30s, 120s, 480s
_RETRY_BACKOFF = (30, 120, 480)


# =============================================================================
# PANEL CONFIGURATION
# =============================================================================

PANEL_CONFIG = {
    "gender_gap": {
        "channel_stats_panel_name": "gender_gap",
        "inventory_path": config.VIDEO_INVENTORY_DIR / "gender_gap_inventory.csv",
    },
    "ai_census": {
        "channel_stats_panel_name": "ai_census",
        "inventory_path": config.VIDEO_INVENTORY_DIR / "ai_census_inventory.csv",
    },
}


def setup_logging(panel: str) -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f"update_inventory_{panel}_{config.get_date_stamp()}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file),
        ],
    )


# =============================================================================
# NUL-SAFE CSV READING
# =============================================================================

def _read_csv_nul_safe(filepath: Path) -> List[Dict]:
    """
    Read a CSV file that may contain NUL bytes (from concurrent writes by
    enumerate_videos.py). Opens in binary mode, strips NUL bytes, decodes,
    then parses as CSV.

    Args:
        filepath: Path to CSV file

    Returns:
        List of row dicts from csv.DictReader
    """
    with open(filepath, "rb") as f:
        raw = f.read()

    cleaned = raw.replace(b"\x00", b"")
    text = cleaned.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def _load_known_video_ids_nul_safe(inventory_path: Path) -> Set[str]:
    """
    Load all video IDs from the inventory CSV using NUL-safe reading.
    Only loads the video_id column to minimize memory usage.

    Args:
        inventory_path: Path to inventory CSV

    Returns:
        Set of known video ID strings
    """
    if not inventory_path.exists():
        return set()

    known = set()

    def _lines():
        # Streaming NUL-safe read: whole-file read of the multi-GB inventory
        # OOM-killed this job on the 8 GB Mac Mini.
        with open(inventory_path, "rb") as f:
            for line in f:
                yield line.replace(b"\x00", b"").decode("utf-8", errors="replace")

    for row in csv.DictReader(_lines()):
        vid = row.get("video_id", "").strip()
        if vid:
            known.add(vid)

    return known


# =============================================================================
# CHANNEL STATS COMPARISON
# =============================================================================

def load_channel_stats(stats_path: Path) -> Dict[str, int]:
    """
    Load channel stats CSV and return {channel_id: video_count} mapping.

    Args:
        stats_path: Path to a daily channel stats CSV

    Returns:
        Dict mapping channel_id to video_count
    """
    counts = {}
    if not stats_path.exists():
        return counts

    with open(stats_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("channel_id", "").strip()
            vc = row.get("video_count")
            if cid and vc is not None:
                try:
                    counts[cid] = int(vc)
                except (ValueError, TypeError):
                    pass

    return counts


def find_channels_with_new_videos(
    today_stats: Dict[str, int],
    yesterday_stats: Dict[str, int],
) -> List[Tuple[str, int, int]]:
    """
    Compare today's and yesterday's video counts to find channels with increases.

    Args:
        today_stats: {channel_id: video_count} for today
        yesterday_stats: {channel_id: video_count} for yesterday

    Returns:
        List of (channel_id, yesterday_count, today_count) tuples,
        sorted by count increase (largest first)
    """
    changed = []
    for cid, today_count in today_stats.items():
        yesterday_count = yesterday_stats.get(cid)
        if yesterday_count is not None and today_count > yesterday_count:
            changed.append((cid, yesterday_count, today_count))

    # Sort by count increase (largest first) for best use of limited runtime
    changed.sort(key=lambda x: x[2] - x[1], reverse=True)
    return changed


# =============================================================================
# NEW VIDEO FETCHING
# =============================================================================

def _call_with_retry(fn, description="API call", max_retries=3):
    """Retry fn() on transient network errors with exponential backoff."""
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


def fetch_new_videos_for_channel(
    youtube,
    channel_id: str,
    count_increase: int,
    known_video_ids: Set[str],
) -> List[Dict]:
    """
    Fetch new video entries for a channel by reading the top of its uploads playlist.

    Uses playlistItems.list (1 unit/call) to get video_id, published_at, title
    for recent uploads. Filters against known_video_ids.

    Args:
        youtube: Authenticated YouTube API service
        channel_id: Channel ID
        count_increase: How many new videos to expect
        known_video_ids: Set of already-known video IDs

    Returns:
        List of inventory-row dicts: {video_id, channel_id, published_at, title, scraped_at}
    """
    if not channel_id.startswith("UC"):
        logger.warning("Unexpected channel ID format: %s, skipping", channel_id)
        return []

    uploads_playlist_id = "UU" + channel_id[2:]
    # Fetch enough to cover new uploads plus a buffer for deletions
    fetch_count = min(count_increase + 10, 50)

    def _fetch():
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=fetch_count,
        )
        return execute_request(request, endpoint_name="playlistItems.list")

    try:
        response = _call_with_retry(_fetch, description=f"playlist {channel_id}")
    except QuotaExhaustedError:
        raise
    except Exception as e:
        logger.error("Error fetching playlist for %s: %s", channel_id, e)
        return []

    scraped_at = datetime.utcnow().isoformat()
    new_entries = []

    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        video_id = snippet.get("resourceId", {}).get("videoId")
        if not video_id or video_id in known_video_ids:
            continue

        new_entries.append({
            "video_id": video_id,
            "channel_id": channel_id,
            "published_at": snippet.get("publishedAt"),
            "title": snippet.get("title"),
            "scraped_at": scraped_at,
        })

    return new_entries


# =============================================================================
# CHECKPOINT
# =============================================================================

def _checkpoint_path(panel: str) -> Path:
    return config.DAILY_PANELS_DIR / f".update_inventory_{panel}_checkpoint.json"


def load_checkpoint(panel: str, date_str: str) -> Dict:
    """Load checkpoint; only valid if date matches."""
    cp_path = _checkpoint_path(panel)
    if cp_path.exists():
        with open(cp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("date") == date_str:
            logger.info(
                "Resuming from checkpoint: %d channels done",
                len(data.get("completed_channels", [])),
            )
            return data

    return {"date": date_str, "completed_channels": [], "total_new_videos": 0}


def save_checkpoint(panel: str, data: Dict) -> None:
    cp_path = _checkpoint_path(panel)
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def clear_checkpoint(panel: str) -> None:
    cp_path = _checkpoint_path(panel)
    if cp_path.exists():
        cp_path.unlink()
        logger.info("Checkpoint cleared")


# =============================================================================
# MAIN COLLECTION LOOP
# =============================================================================

def run_update(
    youtube,
    panel: str,
    date_str: str,
    test_mode: bool = False,
    limit: Optional[int] = None,
    max_runtime: Optional[int] = None,
    reserve_quota: int = 0,
    daily_quota_limit: int = 0,
) -> Dict:
    """
    Main update loop: compare channel stats, fetch new videos, append to inventory.

    Args:
        youtube: Authenticated YouTube API service
        panel: Panel name (gender_gap or ai_census)
        date_str: Today's date (YYYY-MM-DD)
        test_mode: If True, limit to 10 channels
        limit: Max channels to process
        max_runtime: Stop after N seconds
        reserve_quota: Units to reserve for other services
        daily_quota_limit: Daily quota ceiling

    Returns:
        Summary dict
    """
    start_time = time.time()
    panel_cfg = PANEL_CONFIG[panel]

    if test_mode and limit is None:
        limit = 10

    # Paths
    panel_name = panel_cfg["channel_stats_panel_name"]
    inventory_path = panel_cfg["inventory_path"]

    today_stats_path = config.get_daily_panel_path("channel_stats", date_str, panel_name=panel_name)
    yesterday_str = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_stats_path = config.get_daily_panel_path("channel_stats", yesterday_str, panel_name=panel_name)

    # Check prerequisites
    if not today_stats_path.exists():
        logger.error("Today's channel stats not found: %s", today_stats_path)
        return {"success": False, "error": "missing_today_stats"}

    if not yesterday_stats_path.exists():
        logger.warning("Yesterday's channel stats not found: %s (skipping)", yesterday_stats_path)
        return {"success": True, "skipped": True, "reason": "no_yesterday_stats"}

    if not inventory_path.exists():
        logger.warning("Inventory file not found: %s (skipping — wait for enumeration to complete)", inventory_path)
        return {"success": True, "skipped": True, "reason": "no_inventory"}

    # Step 1: Load channel stats
    logger.info("Loading today's stats: %s", today_stats_path.name)
    today_stats = load_channel_stats(today_stats_path)
    logger.info("Loading yesterday's stats: %s", yesterday_stats_path.name)
    yesterday_stats = load_channel_stats(yesterday_stats_path)

    # Step 2: Find channels with new videos
    changed = find_channels_with_new_videos(today_stats, yesterday_stats)
    logger.info("Channels with increased video count: %d", len(changed))

    if not changed:
        logger.info("No channels with new videos — nothing to do")
        return {
            "success": True,
            "date": date_str,
            "panel": panel,
            "channels_checked": len(today_stats),
            "channels_with_new_videos": 0,
            "new_videos_added": 0,
        }

    if limit is not None:
        changed = changed[:limit]

    # Step 3: Load known video IDs (NUL-safe)
    logger.info("Loading known video IDs from inventory (NUL-safe)...")
    known_video_ids = _load_known_video_ids_nul_safe(inventory_path)
    logger.info("Known video IDs: %d", len(known_video_ids))

    # Step 4: Load checkpoint
    checkpoint = load_checkpoint(panel, date_str)
    completed_set = set(checkpoint.get("completed_channels", []))
    total_new_videos = checkpoint.get("total_new_videos", 0)

    quota_ceiling = daily_quota_limit - reserve_quota if reserve_quota > 0 and daily_quota_limit > 0 else 0

    channels_processed = 0
    channels_with_new = 0

    for idx, (channel_id, yesterday_count, today_count) in enumerate(changed):
        if channel_id in completed_set:
            continue

        # Guard: max-runtime
        if max_runtime is not None and time.time() - start_time > max_runtime:
            logger.info("Max runtime %ds reached — stopping. Will resume next run.", max_runtime)
            break

        # Guard: reserve-quota
        if quota_ceiling > 0 and get_quota_used() >= quota_ceiling:
            logger.info("Quota ceiling reached — stopping. Will resume next run.")
            break

        count_increase = today_count - yesterday_count

        try:
            new_entries = fetch_new_videos_for_channel(
                youtube=youtube,
                channel_id=channel_id,
                count_increase=count_increase,
                known_video_ids=known_video_ids,
            )
        except QuotaExhaustedError:
            logger.warning("Quota exhausted — stopping. Will resume next run.")
            break

        if new_entries:
            # Append to inventory CSV
            write_header = not inventory_path.exists()
            with open(inventory_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=config.VIDEO_INVENTORY_FIELDS)
                if write_header:
                    writer.writeheader()
                for entry in new_entries:
                    row = {field: entry.get(field) for field in config.VIDEO_INVENTORY_FIELDS}
                    writer.writerow(row)

            # Update in-memory known set
            for entry in new_entries:
                known_video_ids.add(entry["video_id"])

            total_new_videos += len(new_entries)
            channels_with_new += 1
            logger.info(
                "  %s: +%d videos (count %d→%d)",
                channel_id, len(new_entries), yesterday_count, today_count,
            )

        channels_processed += 1

        # Checkpoint after each channel
        completed_set.add(channel_id)
        checkpoint["completed_channels"] = list(completed_set)
        checkpoint["total_new_videos"] = total_new_videos
        save_checkpoint(panel, checkpoint)

        # Progress logging every 50 channels
        if (channels_processed) % 50 == 0:
            logger.info(
                "Progress: %d/%d channels processed, %d new videos so far",
                channels_processed, len(changed), total_new_videos,
            )

    # Clear checkpoint if all channels processed
    remaining = [cid for cid, _, _ in changed if cid not in completed_set]
    if not remaining:
        clear_checkpoint(panel)
    else:
        logger.info("Checkpoint retained — %d channels remaining", len(remaining))

    summary = {
        "success": True,
        "date": date_str,
        "panel": panel,
        "channels_checked": len(today_stats),
        "channels_with_new_videos": channels_with_new,
        "channels_processed": channels_processed,
        "new_videos_added": total_new_videos,
        "channels_remaining": len(remaining),
        "quota_used": get_quota_used(),
        "runtime_seconds": int(time.time() - start_time),
    }
    return summary


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point for daily inventory updates."""
    parser = argparse.ArgumentParser(
        description="Daily new video detection — compare channel stats and update inventory"
    )
    parser.add_argument(
        "--panel", type=str, required=True, choices=list(PANEL_CONFIG.keys()),
        help="Panel to update (gender_gap or ai_census)",
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="Override date (YYYY-MM-DD, default=today UTC)",
    )
    parser.add_argument("--test", action="store_true", help="Test mode (limit to 10 channels)")
    parser.add_argument("--limit", type=int, default=None, help="Max channels to process")
    parser.add_argument(
        "--max-runtime", type=int, default=None,
        help="Stop after N seconds (launchd safety)",
    )
    parser.add_argument(
        "--reserve-quota", type=int, default=2000,
        help="Stop this many units before daily limit (default 2000)",
    )
    args = parser.parse_args()

    # Validate date
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("Error: --date must be YYYY-MM-DD format", file=sys.stderr)
            sys.exit(1)

    setup_logging(args.panel)
    config.ensure_directories()

    date_str = args.date or datetime.utcnow().strftime("%Y-%m-%d")

    logger.info("=" * 60)
    logger.info("INVENTORY UPDATE — NEW VIDEO DETECTION")
    logger.info("=" * 60)
    logger.info("Panel: %s", args.panel)
    logger.info("Date: %s", date_str)
    logger.info("Test mode: %s", args.test)
    if args.limit:
        logger.info("Limit: %d", args.limit)
    if args.max_runtime is not None:
        logger.info("Max runtime: %ds", args.max_runtime)
    logger.info("Reserve quota: %d", args.reserve_quota)
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        cfg = load_config()
        daily_quota_limit = cfg.get("daily_quota_limit", 0)

        summary = run_update(
            youtube=youtube,
            panel=args.panel,
            date_str=date_str,
            test_mode=args.test,
            limit=args.limit,
            max_runtime=args.max_runtime,
            reserve_quota=args.reserve_quota,
            daily_quota_limit=daily_quota_limit,
        )

        logger.info("=" * 60)
        logger.info("UPDATE COMPLETE")
        for k, v in summary.items():
            logger.info("  %s: %s", k, v)
        logger.info("=" * 60)

    except Exception as e:
        logger.error("Inventory update failed: %s", e)
        raise


if __name__ == "__main__":
    main()
