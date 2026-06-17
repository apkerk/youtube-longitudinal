"""
enumerate_videos_targeted.py
----------------------------
Targeted re-enumeration of a supplied channel list, writing video IDs to a
SEPARATE output CSV. Adapted from enumerate_videos.py for the KE Census
re-enrichment run (2026-06-17): channels that have no videos in the live
knowledge_economy_inventory.csv are re-enumerated into a side file for later
merge, so their thumbnails can be pulled for gender coding.

Differences from enumerate_videos.py:
  - Adds a --reserve-quota guard. The run stops cleanly once this process has
    consumed (daily_quota_limit - reserve_quota) units, leaving headroom for the
    next day's 3-9 AM daily-stats panels. Checkpoint is retained on this exit so
    the next launch resumes.
  - Never writes a completion sentinel for, or otherwise touches, the live
    knowledge_economy_inventory.csv. Output/checkpoint/sentinel are all derived
    from the (separate) output stem.

Carries forward the corrected behavior already present in enumerate_videos.py:
  - A channel is marked complete ONLY after a successful full enumeration
    (inside the try block, after the uploads playlist is fully paged).
  - QuotaExhaustedError is re-raised by the API layer and caught here to stop
    cleanly (checkpoint retained), never swallowed.
  - --max-runtime guard with correct `is not None` check.
  - NUL-safe channel-list read (the live inventory and some CSVs written by
    concurrent collectors can contain embedded NUL bytes).

Usage:
    python -m src.collection.enumerate_videos_targeted \
        --channel-list data/channels/ke_census/reenrich_targets_20260617.csv \
        --output data/video_inventory/knowledge_economy_inventory_reenrich_20260617.csv \
        [--reserve-quota 150000] [--max-runtime 39600] [--test] [--limit N]

Author: Katie Apker (Pat)
Created: Jun 17, 2026
"""

import argparse
import csv
import io
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    get_all_video_ids,
    get_quota_used,
    load_config,
    QuotaExhaustedError,
)
import config

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'enumerate_targeted_{config.get_date_stamp()}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )


def load_channel_ids(filepath: Path) -> List[str]:
    """
    Read channel IDs from a CSV with a channel_id column. NUL-safe: opens in
    binary, strips embedded NUL bytes, then decodes. Returns a deduplicated,
    order-preserving list.
    """
    with open(filepath, 'rb') as f:
        raw = f.read().replace(b'\x00', b'')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8', errors='replace')))

    channel_ids = []
    for row in reader:
        cid = (row.get('channel_id') or '').strip()
        if cid:
            channel_ids.append(cid)

    seen = set()
    unique = []
    for cid in channel_ids:
        if cid not in seen:
            seen.add(cid)
            unique.append(cid)

    logger.info(f"Loaded {len(unique)} unique channel IDs from {filepath.name}")
    return unique


def load_checkpoint(checkpoint_path: Path) -> Dict:
    """Load checkpoint from JSON. Returns dict with 'completed_channels' list."""
    if checkpoint_path.exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(
                f"Loaded checkpoint: {len(data.get('completed_channels', []))} channels already done"
            )
            return data
    return {'completed_channels': []}


def save_checkpoint(checkpoint_path: Path, data: Dict) -> None:
    """Save checkpoint to JSON file."""
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def enumerate_all_channels(
    youtube,
    channel_ids: List[str],
    output_path: Path,
    checkpoint_path: Path,
    test_mode: bool = False,
    limit: int = None,
    max_runtime: int = None,
    reserve_quota: int = None,
) -> int:
    """
    Enumerate all video IDs for a list of channels. Writes results to CSV
    incrementally and checkpoints after each SUCCESSFUL channel.

    Stop conditions (all retain the checkpoint so the next run resumes):
      - QuotaExhaustedError raised by the API layer (hard 403 quotaExceeded).
      - --reserve-quota: this process's cumulative quota reaches the budget
        (daily_quota_limit - reserve_quota).
      - --max-runtime: wall-clock budget exceeded.

    Returns (total_videos, channels_done).
    """
    start_time = time.time()
    if test_mode and limit is None:
        limit = 5

    if limit is not None:
        channel_ids = channel_ids[:limit]

    # Resolve the per-process quota budget for this run, if a reserve was set.
    quota_budget = None
    if reserve_quota is not None:
        daily_limit = 1_000_000  # safe fallback
        try:
            cfg = load_config()
            daily_limit = int(cfg.get('daily_quota_limit', daily_limit))
        except Exception as e:
            logger.warning(
                f"Could not read daily_quota_limit from config.yaml ({e}); "
                f"using fallback {daily_limit}"
            )
        quota_budget = max(0, daily_limit - reserve_quota)
        logger.info(
            f"Quota guard active: this process will stop after consuming "
            f"{quota_budget} units (daily_limit={daily_limit}, reserve={reserve_quota})"
        )

    checkpoint = load_checkpoint(checkpoint_path)
    completed_set = set(checkpoint['completed_channels'])

    remaining = [cid for cid in channel_ids if cid not in completed_set]
    resuming = len(completed_set) > 0
    if resuming:
        logger.info(f"Resuming: {len(completed_set)} done, {len(remaining)} remaining")

    if resuming and output_path.exists():
        file_mode = 'a'
        write_header = False
    else:
        file_mode = 'w'
        write_header = True

    total_videos = 0
    dead_or_empty = 0

    with open(output_path, file_mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=config.VIDEO_INVENTORY_FIELDS)
        if write_header:
            writer.writeheader()

        for idx, channel_id in enumerate(remaining):
            if channel_id.startswith('UC'):
                uploads_playlist_id = 'UU' + channel_id[2:]
            else:
                logger.warning(f"Unexpected channel ID format: {channel_id}, skipping")
                completed_set.add(channel_id)
                checkpoint['completed_channels'] = list(completed_set)
                save_checkpoint(checkpoint_path, checkpoint)
                continue

            try:
                videos, page_token = get_all_video_ids(
                    youtube, uploads_playlist_id, channel_id
                )

                # Only treat as a full, successful enumeration when pagination
                # completed (page_token is None). A non-None token means the run
                # was interrupted mid-channel; do NOT mark complete.
                if page_token is not None:
                    logger.warning(
                        f"Partial enumeration for {channel_id} (pagination interrupted) "
                        "— not marking complete"
                    )
                    # Stop cleanly; checkpoint retained for resume.
                    break

                scraped_at = datetime.utcnow().isoformat()
                for video in videos:
                    writer.writerow({
                        'video_id': video.get('video_id'),
                        'channel_id': video.get('channel_id'),
                        'published_at': video.get('published_at'),
                        'title': video.get('title'),
                        'scraped_at': scraped_at,
                    })
                f.flush()

                total_videos += len(videos)
                if len(videos) == 0:
                    dead_or_empty += 1

                # Mark complete ONLY on a verified-full enumeration.
                completed_set.add(channel_id)
                checkpoint['completed_channels'] = list(completed_set)
                save_checkpoint(checkpoint_path, checkpoint)

            except QuotaExhaustedError:
                logger.warning(
                    "Quota exhausted (403 quotaExceeded) — stopping, will resume next run"
                )
                break
            except Exception as e:
                # Failed channel is NOT marked complete; it will be retried next run.
                logger.error(f"Error enumerating {channel_id}: {e}")

            channels_done = len(completed_set)
            total_to_do = len(channel_ids)
            if (idx + 1) % 100 == 0 or (idx + 1) == len(remaining):
                logger.info(
                    f"Progress: {channels_done}/{total_to_do} channels "
                    f"({total_videos} videos, {dead_or_empty} empty/dead) "
                    f"quota_used={get_quota_used()}"
                )

            # Reserve-quota guard (checkpoint retained on exit).
            if quota_budget is not None and get_quota_used() >= quota_budget:
                logger.info(
                    f"Reserve-quota budget reached (used={get_quota_used()} >= "
                    f"{quota_budget}) — stopping. Will resume next run."
                )
                break

            # Max-runtime guard (checkpoint retained on exit).
            if max_runtime is not None and time.time() - start_time > max_runtime:
                logger.info(
                    f"Max runtime {max_runtime}s reached — stopping. Will resume next run."
                )
                break

    # Clear checkpoint + write a sentinel ONLY when every target was processed.
    # The sentinel name is derived from THIS output stem, so the live inventory's
    # sentinel is never created or touched.
    if len(completed_set) >= len(channel_ids):
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.info("Cleared checkpoint (all channels complete)")
        sentinel_path = checkpoint_path.parent / f".enumerate_{output_path.stem}_complete"
        sentinel_path.write_text(
            f"Completed: {datetime.utcnow().isoformat()}\n"
            f"Channels: {len(completed_set)}\n"
            f"Videos: {total_videos}\n"
        )
        logger.info(f"Completion sentinel written: {sentinel_path.name}")
    else:
        logger.info(
            f"Checkpoint retained — {len(completed_set)}/{len(channel_ids)} channels done, "
            "will resume next run"
        )

    return total_videos, len(completed_set)


def main():
    """CLI entry point for targeted video enumeration."""
    parser = argparse.ArgumentParser(
        description="Targeted re-enumeration of a channel list into a separate CSV"
    )
    parser.add_argument('--channel-list', type=str, required=True,
                        help='Path to CSV with channel_id column')
    parser.add_argument('--output', type=str, required=True,
                        help='Output CSV path (must be a SEPARATE file, not the live inventory)')
    parser.add_argument('--test', action='store_true', help='Test mode (5 channels)')
    parser.add_argument('--limit', type=int, default=None, help='Max channels to process')
    parser.add_argument('--max-runtime', type=int, default=None,
                        help='Stop after N seconds (launchd / overnight safety)')
    parser.add_argument('--reserve-quota', type=int, default=None,
                        help='Stop once this process has consumed (daily_limit - reserve) units')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    channel_list_path = Path(args.channel_list)
    if not channel_list_path.is_absolute():
        channel_list_path = config.PROJECT_ROOT / channel_list_path

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = config.PROJECT_ROOT / output_path

    # Guard against accidentally pointing at the live inventory.
    if output_path.name == 'knowledge_economy_inventory.csv':
        logger.error(
            "Refusing to write to the live knowledge_economy_inventory.csv. "
            "Use a separate output filename."
        )
        sys.exit(2)

    checkpoint_name = f".enumerate_{output_path.stem}_checkpoint.json"
    checkpoint_path = config.VIDEO_INVENTORY_DIR / checkpoint_name

    logger.info("=" * 60)
    logger.info("TARGETED VIDEO INVENTORY RE-ENUMERATION")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"Channel list: {channel_list_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Checkpoint: {checkpoint_path}")
    logger.info(f"Test mode: {args.test}")
    if args.limit:
        logger.info(f"Limit: {args.limit}")
    if args.reserve_quota:
        logger.info(f"Reserve quota: {args.reserve_quota}")
    if args.max_runtime:
        logger.info(f"Max runtime: {args.max_runtime}s")
    logger.info("=" * 60)

    if not channel_list_path.exists():
        logger.error(f"Channel list not found: {channel_list_path}")
        sys.exit(1)

    # Honor an existing completion sentinel for THIS output stem only.
    sentinel_path_check = config.VIDEO_INVENTORY_DIR / f".enumerate_{output_path.stem}_complete"
    if sentinel_path_check.exists() and not args.test:
        logger.info("Re-enumeration already complete (sentinel found). Nothing to do.")
        logger.info(f"Delete {sentinel_path_check.name} to force a re-run.")
        return

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        channel_ids = load_channel_ids(channel_list_path)
        if not channel_ids:
            logger.warning("No channel IDs found in input file")
            return

        total_videos, channels_done = enumerate_all_channels(
            youtube=youtube,
            channel_ids=channel_ids,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
            test_mode=args.test,
            limit=args.limit,
            max_runtime=args.max_runtime,
            reserve_quota=args.reserve_quota,
        )

        logger.info("=" * 60)
        if channels_done >= len(channel_ids):
            logger.info("RE-ENUMERATION COMPLETE")
        else:
            logger.info("RE-ENUMERATION PAUSED — will resume next run")
        logger.info(f"Channels done: {channels_done}/{len(channel_ids)}")
        logger.info(f"Videos found this run: {total_videos}")
        logger.info(f"Output: {output_path}")
        logger.info(f"Quota used (this process): {get_quota_used()}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Re-enumeration failed: {e}")
        raise


if __name__ == "__main__":
    main()
