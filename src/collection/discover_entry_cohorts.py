"""
discover_entry_cohorts.py
-------------------------
Entry Cohort Discovery -- channels born around AI tool launch dates.

For each tool in docs/tool_launch_calendar.csv, generates two sets of
time windows:
  - Treatment: 4 weeks before launch through 12 weeks after (16-week span)
  - Control:   same 16-week calendar window, one year prior (seasonality control)

Uses the same KNOWLEDGE_ECONOMY_KEYWORDS domains to search for videos.
Post-hoc filter: channel published_at falls within the treatment or control
window dates (we want channels CREATED in the window, not just channels that
posted videos in it).

Two sort orders per keyword per window (date + relevance), rotating regions.

Supports checkpoint/resume, --max-runtime, --reserve-quota, --test, --limit.

Usage:
    python -m src.collection.discover_entry_cohorts [--test] [--limit N]
    python -m src.collection.discover_entry_cohorts \
        --max-runtime 28800 --reserve-quota 2000

Author: Katie Apker
Last Updated: April 2026
"""

import argparse
import csv
import fcntl
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    search_videos_paginated,
    extract_channel_ids_from_search,
    get_channel_full_details,
    QuotaExhaustedError,
    get_quota_used,
    load_config,
)
import config

logger = logging.getLogger(__name__)

ENTRY_DIR = config.CHANNELS_DIR / "entry_cohorts"
CHECKPOINT_PATH = ENTRY_DIR / ".discovery_checkpoint.json"
LOCKFILE_PATH = ENTRY_DIR / ".entry_cohorts.lock"
TOOL_CALENDAR_PATH = config.PROJECT_ROOT / "docs" / "tool_launch_calendar.csv"

# Region rotation for discovery
ENTRY_REGIONS = getattr(config, "TECH_CENSUS_REGIONS", [
    "US", "GB", "IN", "DE", "BR", "JP", "FR", "KR", "MX", "ID",
    "TR", "PL", "TH", "VN", "EG",
])


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    ENTRY_DIR.mkdir(parents=True, exist_ok=True)
    log_file = config.LOGS_DIR / ("discover_entry_cohorts_%s.log" % config.get_date_stamp())

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file),
        ],
    )


# =============================================================================
# TOOL CALENDAR
# =============================================================================

def read_tool_calendar(calendar_path: Optional[Path] = None) -> List[dict]:
    """Read tool launch calendar CSV.

    Returns:
        List of dicts with at least 'tool_name' and 'launch_date' keys.
    """
    path = calendar_path or TOOL_CALENDAR_PATH
    if not path.exists():
        raise FileNotFoundError("Tool launch calendar not found at %s" % path)

    tools = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("tool_name") and row.get("launch_date"):
                tools.append(row)

    logger.info("Loaded %d tool launches from %s", len(tools), path)
    return tools


# =============================================================================
# TIME WINDOW GENERATION
# =============================================================================

def generate_windows(start_dt: datetime, end_dt: datetime, step_days: int = 7) -> List[Tuple[str, str]]:
    """Generate time windows across the given range.

    Args:
        start_dt: Window range start (datetime object).
        end_dt: Window range end (datetime object).
        step_days: Days between window starts (default 7 = weekly).
            Each window is 24 hours wide; step_days controls spacing.

    Returns:
        List of (published_after_iso, published_before_iso) tuples.
    """
    windows = []
    current = start_dt
    while current < end_dt:
        after = current.strftime("%Y-%m-%dT00:00:00Z")
        before = (current + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        windows.append((after, before))
        current += timedelta(days=step_days)
    return windows


# =============================================================================
# CHECKPOINT
# =============================================================================

def load_checkpoint(output_path: Path) -> Tuple[Set[str], Dict[str, dict]]:
    """Load checkpoint. Returns (completed_keys, channels_by_id)."""
    completed: Set[str] = set()
    channels_by_id: Dict[str, dict] = {}

    if not CHECKPOINT_PATH.exists():
        return completed, channels_by_id

    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        ckpt = json.load(f)

    completed = set(ckpt.get("completed_keys", []))

    saved_path = Path(ckpt.get("output_path", ""))
    if saved_path.exists() and saved_path == output_path:
        with open(saved_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("channel_id", "").strip()
                if cid:
                    channels_by_id[cid] = row

    logger.info(
        "Resumed from checkpoint: %d channels, %d completed keys",
        len(channels_by_id), len(completed),
    )
    return completed, channels_by_id


def save_checkpoint(completed_keys: Set[str], output_path: Path, channel_count: int) -> None:
    """Save checkpoint to disk."""
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "completed_keys": list(completed_keys),
            "output_path": str(output_path),
            "channel_count": channel_count,
            "timestamp": datetime.utcnow().isoformat(),
        }, f)


def clear_checkpoint() -> None:
    """Remove checkpoint file (only when all keys are done)."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared.")


# =============================================================================
# FLUSH BATCH TO CSV
# =============================================================================

def flush_channels_to_csv(channels_by_id: Dict[str, dict], output_path: Path) -> None:
    """Write all channels to the output CSV (full rewrite for consistency)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
        writer.writeheader()
        for ch in channels_by_id.values():
            row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
            writer.writerow(row)


# =============================================================================
# CORE DISCOVERY LOOP
# =============================================================================

def run_discovery(
    youtube,
    output_path: Path,
    test_mode: bool = False,
    limit: Optional[int] = None,
    max_runtime: Optional[int] = None,
    reserve_quota: int = 0,
    daily_quota_limit: int = 0,
    step_days: int = 7,
) -> dict:
    """
    Main discovery loop for entry cohort channels.

    For each tool launch, generates treatment (4w before to 12w after) and
    control (same calendar window, one year prior) time windows. Iterates
    (tool x window_type x window x domain x keyword x sort_order), rotating
    regions. Channels are deduped across all keys and flushed periodically.
    """
    start_time = time.time()
    quota_ceiling = daily_quota_limit - reserve_quota if reserve_quota > 0 and daily_quota_limit > 0 else 0

    # Load tool calendar
    calendar = read_tool_calendar()
    if test_mode:
        calendar = calendar[:2]
        logger.info("TEST MODE: limited to %d tool launches", len(calendar))

    # Build the work queue
    regions = ENTRY_REGIONS
    work_queue: List[Tuple[str, dict]] = []
    window_counter = 0  # Global counter for region rotation across all tools

    for tool in calendar:
        tool_name = tool["tool_name"]
        launch = datetime.strptime(tool["launch_date"], "%Y-%m-%d")

        # Treatment windows: 4 weeks before to 12 weeks after launch
        treat_start = launch - timedelta(weeks=4)
        treat_end = launch + timedelta(weeks=12)
        treat_windows = generate_windows(treat_start, treat_end, step_days=step_days)

        # Control windows: same calendar period, one year prior
        ctrl_start = treat_start - timedelta(days=365)
        ctrl_end = treat_end - timedelta(days=365)
        ctrl_windows = generate_windows(ctrl_start, ctrl_end, step_days=step_days)

        if test_mode:
            treat_windows = treat_windows[:5]
            ctrl_windows = ctrl_windows[:5]

        for window_type, windows in [("treatment", treat_windows), ("control", ctrl_windows)]:
            for after, before in windows:
                region = regions[window_counter % len(regions)]
                window_counter += 1
                for domain, keywords in config.KNOWLEDGE_ECONOMY_KEYWORDS.items():
                    for kw in keywords:
                        for sort_order in ["date", "relevance"]:
                            key = "%s|%s|%s|%s|%s|%s" % (
                                tool_name[:20], window_type, after[:10],
                                kw[:30], sort_order, region,
                            )
                            params = {
                                "published_after": after,
                                "published_before": before,
                                "order": sort_order,
                                "region_code": region,
                                "max_pages": 5,
                                "query": kw,
                                "domain": domain,
                                "tool_name": tool_name,
                                "window_type": window_type,
                            }
                            work_queue.append((key, params))

    if limit is not None:
        work_queue = work_queue[:limit]

    logger.info("Work queue: %d keys across %d tool launches", len(work_queue), len(calendar))

    # Load checkpoint
    completed_keys, channels_by_id = load_checkpoint(output_path)
    remaining = [(k, p) for k, p in work_queue if k not in completed_keys]
    logger.info("Remaining: %d keys (skipping %d completed)", len(remaining), len(completed_keys))

    new_channels_this_run = 0
    keys_processed = 0

    for key, params in remaining:
        # Guard: max-runtime
        if max_runtime is not None and time.time() - start_time > max_runtime:
            logger.info("Max runtime %ds reached. Will resume next run.", max_runtime)
            break

        # Guard: reserve-quota
        if quota_ceiling > 0 and get_quota_used() >= quota_ceiling:
            logger.info("Quota ceiling reached. Will resume next run.")
            break

        # Build search kwargs (exclude non-API fields)
        search_kwargs = {
            "published_after": params["published_after"],
            "published_before": params["published_before"],
            "order": params["order"],
            "max_pages": params["max_pages"],
            "region_code": params["region_code"],
            "query": params["query"],
        }

        try:
            results = search_videos_paginated(youtube, **search_kwargs)
        except QuotaExhaustedError:
            logger.warning("Quota exhausted. Will resume next run.")
            break
        except Exception as e:
            logger.error("Error on key %s: %s", key, e)
            completed_keys.add(key)
            save_checkpoint(completed_keys, output_path, len(channels_by_id))
            continue

        # Extract channel IDs
        new_cids = extract_channel_ids_from_search(results)
        unknown_cids = [cid for cid in new_cids if cid not in channels_by_id]

        if unknown_cids:
            tool_name = params["tool_name"]
            window_type = params["window_type"]
            kw = params["query"]
            discovery_kw = "entry:%s:%s:%s" % (tool_name, window_type, kw)

            try:
                details = get_channel_full_details(
                    youtube,
                    unknown_cids,
                    stream_type="entry_cohort",
                    discovery_language="global",
                    discovery_keyword=discovery_kw,
                )
                for ch in details:
                    cid = ch.get("channel_id")
                    if cid and cid not in channels_by_id:
                        channels_by_id[cid] = ch
                        new_channels_this_run += 1
            except QuotaExhaustedError:
                logger.warning("Quota exhausted during channel details. Will resume next run.")
                break
            except Exception as e:
                logger.error("Error fetching channel details: %s", e)

        completed_keys.add(key)
        keys_processed += 1

        # Checkpoint and flush every 50 keys
        if keys_processed % 50 == 0:
            save_checkpoint(completed_keys, output_path, len(channels_by_id))
            flush_channels_to_csv(channels_by_id, output_path)
            logger.info(
                "Progress: %d/%d keys, %d total channels (+%d this run), quota=%d",
                len(completed_keys), len(work_queue), len(channels_by_id),
                new_channels_this_run, get_quota_used(),
            )

    # Final flush
    save_checkpoint(completed_keys, output_path, len(channels_by_id))
    flush_channels_to_csv(channels_by_id, output_path)

    # Clear checkpoint only if all keys are done
    if len(completed_keys) >= len(work_queue):
        clear_checkpoint()

    summary = {
        "tool_launches": len(calendar),
        "keys_total": len(work_queue),
        "keys_completed": len(completed_keys),
        "channels_total": len(channels_by_id),
        "channels_new_this_run": new_channels_this_run,
        "quota_used": get_quota_used(),
        "runtime_seconds": int(time.time() - start_time),
    }
    return summary


# =============================================================================
# CLI
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Entry Cohort Discovery -- channels born around AI tool launches"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output CSV path (default: data/channels/entry_cohorts/entry_YYYYMMDD.csv)",
    )
    parser.add_argument("--test", action="store_true", help="Test mode (2 tool launches, 5 windows each)")
    parser.add_argument("--limit", type=int, default=None, help="Max work keys to process")
    parser.add_argument(
        "--max-runtime", type=int, default=None,
        help="Stop after N seconds (launchd safety)",
    )
    parser.add_argument(
        "--reserve-quota", type=int, default=2000,
        help="Stop this many units before daily limit (default 2000)",
    )
    parser.add_argument(
        "--step-days", type=int, default=7,
        help="Days between sampled windows (default 7 = weekly, 1 = daily)",
    )
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    # Resolve output path
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = config.PROJECT_ROOT / output_path
    else:
        output_path = ENTRY_DIR / ("entry_%s.csv" % config.get_date_stamp())

    logger.info("=" * 60)
    logger.info("ENTRY COHORT DISCOVERY")
    logger.info("=" * 60)
    logger.info("Output: %s", output_path)
    logger.info("Test mode: %s", args.test)
    logger.info("Calendar: %s", TOOL_CALENDAR_PATH)
    if args.limit:
        logger.info("Limit: %d", args.limit)
    if args.max_runtime is not None:
        logger.info("Max runtime: %ds", args.max_runtime)
    logger.info("Reserve quota: %d", args.reserve_quota)
    logger.info("Step days: %d", args.step_days)
    logger.info("=" * 60)

    # PID lockfile to prevent concurrent instances
    ENTRY_DIR.mkdir(parents=True, exist_ok=True)
    lock_fd = open(LOCKFILE_PATH, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        logger.error("Another entry cohorts instance is running (lockfile held). Exiting.")
        sys.exit(1)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        cfg = load_config()
        daily_quota_limit = cfg.get("daily_quota_limit", 0)

        summary = run_discovery(
            youtube=youtube,
            output_path=output_path,
            test_mode=args.test,
            limit=args.limit,
            max_runtime=args.max_runtime,
            reserve_quota=args.reserve_quota,
            daily_quota_limit=daily_quota_limit,
            step_days=args.step_days,
        )

        logger.info("=" * 60)
        logger.info("DISCOVERY COMPLETE")
        for k, v in summary.items():
            logger.info("  %s: %s", k, v)
        logger.info("=" * 60)

    except Exception as e:
        logger.error("Discovery failed: %s", e)
        raise
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


if __name__ == "__main__":
    main()
