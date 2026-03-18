"""
discover_tech_census.py
-----------------------
Tech Census Discovery -- pre-2023 technology channels for AI adoption study.

Two discovery methods (selectable via --method):
  - topicid:  Search with YouTube's Technology topicId (/m/07c1v)
  - keyword:  Search with tech content keywords (no topicId filter)

Both methods use 24-hour time windows across 2015-2022 to find videos,
extract unique channel IDs, and collect full channel details. Post-hoc
verification filters to channels with Technology-related topics created
before January 2023.

Supports checkpoint/resume, --max-runtime, --reserve-quota, --test, --limit.

Target: 50,000 channels
Method: Two-pass (topicId + keyword)
Filter: Channel created < 2023-01-01, topic includes Technology-related term

Usage:
    python -m src.collection.discover_tech_census --method topicid [--test] [--limit N]
    python -m src.collection.discover_tech_census --method keyword [--test] [--limit N]
    python -m src.collection.discover_tech_census --method topicid \
        --max-runtime 28800 --reserve-quota 2000

Author: Katie Apker
Last Updated: March 2026
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
from typing import Dict, List, Optional, Set

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

TECH_CENSUS_DIR = config.STREAM_DIRS["tech_census"]
LOCKFILE_PATH = TECH_CENSUS_DIR / ".tech_census.lock"


def setup_logging():
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / ("discover_tech_census_%s.log" % config.get_date_stamp())

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file),
        ],
    )


# =============================================================================
# TIME WINDOW GENERATION
# =============================================================================

def generate_windows(start_date_str, end_date_str):
    """Generate 24-hour (date, date+1) windows across the given range.

    Returns list of (published_after_iso, published_before_iso) tuples.
    """
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    end = datetime.strptime(end_date_str, "%Y-%m-%d")
    windows = []
    current = start
    while current < end:
        after = current.strftime("%Y-%m-%dT00:00:00Z")
        before = (current + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        windows.append((after, before))
        current += timedelta(days=1)
    return windows


# =============================================================================
# CHECKPOINT
# =============================================================================

def checkpoint_path(method):
    return TECH_CENSUS_DIR / (".discovery_%s_checkpoint.json" % method)


def load_checkpoint(method, output_path):
    """Load checkpoint for a given method. Returns (completed_keys, channels_by_id)."""
    cp_path = checkpoint_path(method)
    completed = set()
    channels_by_id = {}

    if not cp_path.exists():
        return completed, channels_by_id

    with open(cp_path, "r", encoding="utf-8") as f:
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


def save_checkpoint_data(method, completed_keys, output_path, channel_count):
    cp_path = checkpoint_path(method)
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump({
            "completed_keys": list(completed_keys),
            "output_path": str(output_path),
            "channel_count": channel_count,
            "timestamp": datetime.utcnow().isoformat(),
        }, f)


def clear_checkpoint(method):
    cp_path = checkpoint_path(method)
    if cp_path.exists():
        cp_path.unlink()
        logger.info("Checkpoint cleared for method=%s", method)


# =============================================================================
# FLUSH BATCH TO CSV
# =============================================================================

def flush_channels_to_csv(channels_by_id, output_path):
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
    method,
    output_path,
    test_mode=False,
    limit=None,
    max_runtime=None,
    reserve_quota=0,
    daily_quota_limit=0,
):
    """
    Main discovery loop for either topicid or keyword method.

    Each "key" is a unique combination of (window_date, sort_order, keyword_or_topic).
    Channels are deduped across all keys and flushed periodically.
    """
    start_time = time.time()
    quota_ceiling = daily_quota_limit - reserve_quota if reserve_quota > 0 and daily_quota_limit > 0 else 0

    # Generate time windows
    windows = generate_windows(config.TECH_CENSUS_WINDOW_START, config.TECH_CENSUS_WINDOW_END)
    if test_mode:
        windows = windows[:5]
        logger.info("TEST MODE: limited to %d windows", len(windows))

    # Build the work queue: list of (key_string, search_params) tuples
    sort_orders = ["date", "relevance", "viewCount"]
    regions = config.TECH_CENSUS_REGIONS
    work_queue = []

    # Broad query terms paired with topicId to boost yield (topicId alone is ~1 result/day)
    topicid_queries = [
        "technology", "tech", "software", "computer", "programming",
        "tutorial", "review", "how to", "code", "developer",
    ]

    if method == "topicid":
        for i, (after, before) in enumerate(windows):
            region = regions[i % len(regions)]
            for tq in topicid_queries:
                for sort_order in ["date", "relevance"]:
                    key = "%s|%s|%s|%s" % (after[:10], tq, sort_order, region)
                    params = {
                        "published_after": after,
                        "published_before": before,
                        "order": sort_order,
                        "region_code": region,
                        "max_pages": 5,
                        "query": tq,
                        "topicId": config.TECH_CENSUS_TOPIC_ID,
                    }
                    work_queue.append((key, params))

    elif method == "keyword":
        keywords = config.TECH_CENSUS_KEYWORDS
        for i, (after, before) in enumerate(windows):
            region = regions[i % len(regions)]
            for kw in keywords:
                for sort_order in ["date", "relevance"]:
                    key = "%s|%s|%s|%s" % (after[:10], kw[:30], sort_order, region)
                    params = {
                        "published_after": after,
                        "published_before": before,
                        "order": sort_order,
                        "region_code": region,
                        "max_pages": 5,
                        "query": kw,
                    }
                    work_queue.append((key, params))

    if limit is not None:
        work_queue = work_queue[:limit]

    logger.info("Work queue: %d keys for method=%s", len(work_queue), method)

    # Load checkpoint
    completed_keys, channels_by_id = load_checkpoint(method, output_path)
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

        # Build search kwargs
        search_kwargs = {
            "published_after": params["published_after"],
            "published_before": params["published_before"],
            "order": params["order"],
            "max_pages": params["max_pages"],
        }
        if params.get("region_code"):
            search_kwargs["region_code"] = params["region_code"]
        if params.get("query"):
            search_kwargs["query"] = params["query"]

        # Extra params for topicId (passed through to search.list)
        extra = {}
        if params.get("topicId"):
            extra["topicId"] = params["topicId"]

        try:
            results = search_videos_paginated(youtube, **search_kwargs, **extra)
        except QuotaExhaustedError:
            logger.warning("Quota exhausted. Will resume next run.")
            break
        except Exception as e:
            logger.error("Error on key %s: %s", key, e)
            completed_keys.add(key)
            save_checkpoint_data(method, completed_keys, output_path, len(channels_by_id))
            continue

        # Extract channel IDs
        new_cids = extract_channel_ids_from_search(results)
        unknown_cids = [cid for cid in new_cids if cid not in channels_by_id]

        if unknown_cids:
            try:
                details = get_channel_full_details(
                    youtube,
                    unknown_cids,
                    stream_type="tech_census_%s" % method,
                    discovery_language="global",
                    discovery_keyword=params.get("query", "topicId:%s" % config.TECH_CENSUS_TOPIC_ID),
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
            save_checkpoint_data(method, completed_keys, output_path, len(channels_by_id))
            flush_channels_to_csv(channels_by_id, output_path)
            logger.info(
                "Progress: %d/%d keys, %d total channels (+%d this run), quota=%d",
                len(completed_keys), len(work_queue), len(channels_by_id),
                new_channels_this_run, get_quota_used(),
            )

    # Final flush
    save_checkpoint_data(method, completed_keys, output_path, len(channels_by_id))
    flush_channels_to_csv(channels_by_id, output_path)

    # Clear checkpoint only if all keys are done
    if len(completed_keys) >= len(work_queue):
        clear_checkpoint(method)

    summary = {
        "method": method,
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

def main():
    parser = argparse.ArgumentParser(
        description="Tech Census Discovery -- pre-2023 tech channels"
    )
    parser.add_argument(
        "--method", type=str, required=True, choices=["topicid", "keyword"],
        help="Discovery method: topicid (Technology topic) or keyword (text search)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output CSV path (default: data/channels/tech_census/METHOD_YYYYMMDD.csv)",
    )
    parser.add_argument("--test", action="store_true", help="Test mode (5 windows)")
    parser.add_argument("--limit", type=int, default=None, help="Max work keys to process")
    parser.add_argument(
        "--max-runtime", type=int, default=None,
        help="Stop after N seconds (launchd safety)",
    )
    parser.add_argument(
        "--reserve-quota", type=int, default=2000,
        help="Stop this many units before daily limit (default 2000)",
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
        output_path = TECH_CENSUS_DIR / ("%s_%s.csv" % (args.method, config.get_date_stamp()))

    logger.info("=" * 60)
    logger.info("TECH CENSUS DISCOVERY")
    logger.info("=" * 60)
    logger.info("Method: %s", args.method)
    logger.info("Output: %s", output_path)
    logger.info("Test mode: %s", args.test)
    if args.limit:
        logger.info("Limit: %d", args.limit)
    if args.max_runtime is not None:
        logger.info("Max runtime: %ds", args.max_runtime)
    logger.info("Reserve quota: %d", args.reserve_quota)
    logger.info("=" * 60)

    # PID lockfile to prevent concurrent instances
    TECH_CENSUS_DIR.mkdir(parents=True, exist_ok=True)
    lock_fd = open(LOCKFILE_PATH, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        logger.error("Another tech census instance is running (lockfile held). Exiting.")
        sys.exit(1)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        cfg = load_config()
        daily_quota_limit = cfg.get("daily_quota_limit", 0)

        summary = run_discovery(
            youtube=youtube,
            method=args.method,
            output_path=output_path,
            test_mode=args.test,
            limit=args.limit,
            max_runtime=args.max_runtime,
            reserve_quota=args.reserve_quota,
            daily_quota_limit=daily_quota_limit,
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
