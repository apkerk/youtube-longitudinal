"""
discover_cohort_b.py
--------------------
Cohort B Arm 1 PRODUCTION discovery for the "Who Explains AI?" paper.
Katie approved this run 2026-08-06 (sampling expansion per
papers/gendering-ai-expertise/qbq/ROBUST_PLAN_2026-08-06.md, Section 1).

Extends the validated pilot (discover_cohort_b_pilot.py: 31 channels per
100-unit search call, 76.8 percent Arm 1 eligible) to a full query grid:
4 families x 18 queries, 5 pages per query, order=relevance, discovery
window publishedAfter=2021-07-01 to publishedBefore=2022-06-01 so the video
that makes a channel discoverable predates the first calendar launch
(Copilot GA 2022-06-21). No AI words in any query.

Stop conditions (whichever first): 6,500 Arm 1 eligible channels,
all queries exhausted, or the 120,000-unit hard cap.

Checkpoint/resume: completed queries and accumulated channels persist in a
checkpoint JSON; rerunning skips completed queries without repeating quota.

Usage:
    python -m src.collection.discover_cohort_b --test        # 1 query, 1 page
    python -m src.collection.discover_cohort_b               # production
    python -m src.collection.discover_cohort_b --limit 10    # first 10 queries

Output:
    data/channels/cohort_b/arm1_discovery_20260806.csv
    papers/gendering-ai-expertise/output/cohort_b_discovery_summary.json
    data/channels/cohort_b/.discover_cohort_b_checkpoint.json
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    search_videos_paginated,
    get_channel_full_details,
    QuotaExhaustedError,
    get_quota_used,
)
import config

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "channels" / "cohort_b"
PAPER_OUTPUT_DIR = REPO_ROOT / "papers" / "gendering-ai-expertise" / "output"
ROSTER_PATH = (
    REPO_ROOT / "papers" / "gendering-ai-expertise" / "processed" / "ke_analysis_base.csv"
)
CSV_PATH = OUT_DIR / "arm1_discovery_20260806.csv"
SUMMARY_PATH = PAPER_OUTPUT_DIR / "cohort_b_discovery_summary.json"
CHECKPOINT_PATH = OUT_DIR / ".discover_cohort_b_checkpoint.json"

DISCOVERY_PUBLISHED_AFTER = "2021-07-01T00:00:00Z"
DISCOVERY_PUBLISHED_BEFORE = "2022-06-01T00:00:00Z"
ARM1_FOUNDED_CUTOFF = "2022-06-20"
ARM1_MIN_VIDEOS = 50
MAX_PAGES_PER_QUERY = 5
SEARCH_CALL_COST = 100
QUOTA_HARD_CAP = 120_000
ELIGIBLE_TARGET = 6_500

QUERY_FAMILIES: Dict[str, List[str]] = {
    "programming_tutorials": [
        "python tutorial", "web development course", "javascript for beginners",
        "sql tutorial", "java programming course", "learn to code",
        "data structures and algorithms", "react tutorial", "html css tutorial",
        "c++ programming", "data science tutorial", "machine learning course",
        "git tutorial", "linux tutorial", "coding interview prep",
        "app development tutorial", "wordpress tutorial", "programming for beginners",
    ],
    "business_marketing": [
        "marketing strategy", "excel tutorial", "how to start a business",
        "digital marketing course", "seo tutorial", "copywriting tips",
        "social media marketing", "ecommerce business", "sales training",
        "accounting basics", "personal finance tips", "real estate investing",
        "freelancing tips", "email marketing", "business plan how to",
        "stock market for beginners", "bookkeeping tutorial", "entrepreneur advice",
    ],
    "knowledge_productivity": [
        "study with me", "productivity system", "note taking tips",
        "notion tutorial", "time management tips", "how to study effectively",
        "project management basics", "language learning tips", "speed reading",
        "habit building", "goal setting", "morning routine productivity",
        "exam preparation tips", "research paper how to", "memory techniques",
        "focus and concentration", "student productivity", "organization tips",
    ],
    "tech_reviews": [
        "software review", "laptop review", "best apps",
        "photoshop tutorial", "video editing tutorial", "graphic design tutorial",
        "camera review", "pc build guide", "smartphone review",
        "figma tutorial", "premiere pro tutorial", "blender tutorial",
        "tech tips and tricks", "home office setup", "keyboard review",
        "monitor review", "design portfolio tips", "illustrator tutorial",
    ],
}


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, mode="a", encoding="utf-8"),
        ],
        force=True,
    )


def load_roster_channel_ids(roster_path: Path) -> Set[str]:
    roster_ids: Set[str] = set()
    with open(roster_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = (row.get("channel_id") or "").strip()
            if cid:
                roster_ids.add(cid)
    logger.info("Roster loaded: %d channel ids", len(roster_ids))
    return roster_ids


def load_checkpoint() -> Dict:
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            ck = json.load(f)
        logger.info("Checkpoint: %d queries done, %d channels accumulated, %d units used",
                    len(ck.get("completed_queries", [])), len(ck.get("channels", {})),
                    ck.get("units_used", 0))
        return ck
    return {"completed_queries": [], "channels": {}, "units_used": 0, "query_records": []}


def save_checkpoint(ck: Dict) -> None:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ck, f)
    tmp.replace(CHECKPOINT_PATH)


def is_arm1_eligible(published_at: Optional[str], video_count: Optional[int]) -> bool:
    if not published_at or video_count is None:
        return False
    return published_at[:10] < ARM1_FOUNDED_CUTOFF and video_count >= ARM1_MIN_VIDEOS


def eligible_count(channels: Dict[str, Dict]) -> int:
    return sum(1 for c in channels.values()
               if is_arm1_eligible(c.get("published_at"), c.get("video_count")))


def run(test_mode: bool, limit: Optional[int]) -> Dict:
    quota_at_start = get_quota_used()
    started_at = datetime.now(timezone.utc).isoformat()
    roster_ids = load_roster_channel_ids(ROSTER_PATH)
    youtube = get_authenticated_service()
    logger.info("Authenticated with YouTube API")

    ck = load_checkpoint() if not test_mode else {
        "completed_queries": [], "channels": {}, "units_used": 0, "query_records": []}
    channels: Dict[str, Dict] = ck["channels"]
    stop_reason: Optional[str] = None
    session_base = ck["units_used"]  # units from PRIOR sessions, fixed for this run

    def units_this_session() -> int:
        return get_quota_used() - quota_at_start

    def total_units() -> int:
        return session_base + units_this_session()

    all_queries = [(fam, q) for fam, qs in QUERY_FAMILIES.items() for q in qs]
    if test_mode:
        all_queries = all_queries[:1]
        max_pages = 1
        logger.info("TEST MODE: 1 query, 1 page")
    else:
        max_pages = MAX_PAGES_PER_QUERY
        if limit:
            all_queries = all_queries[:limit]

    for family, query in all_queries:
        if query in ck["completed_queries"]:
            continue
        if eligible_count(channels) >= ELIGIBLE_TARGET:
            stop_reason = "eligible target %d reached" % ELIGIBLE_TARGET
            break
        if total_units() + max_pages * SEARCH_CALL_COST + 20 > QUOTA_HARD_CAP:
            stop_reason = "quota hard cap %d would be exceeded" % QUOTA_HARD_CAP
            break

        logger.info("Searching [%s] '%s' (%d pages)", family, query, max_pages)
        try:
            results = search_videos_paginated(
                youtube=youtube, query=query,
                published_after=DISCOVERY_PUBLISHED_AFTER,
                published_before=DISCOVERY_PUBLISHED_BEFORE,
                max_pages=max_pages, order="relevance",
            )
        except QuotaExhaustedError:
            stop_reason = "daily API quota exhausted during search '%s'" % query
            logger.error(stop_reason)
            break

        query_cids: List[str] = []
        seen: Set[str] = set()
        for item in results:
            cid = item.get("snippet", {}).get("channelId")
            if cid and cid not in seen:
                seen.add(cid)
                query_cids.append(cid)
        new_ids = [c for c in query_cids if c not in channels]

        if new_ids:
            try:
                details = get_channel_full_details(
                    youtube=youtube, channel_ids=new_ids,
                    stream_type="cohort_b_arm1",
                    discovery_language="English", discovery_keyword=query,
                )
            except QuotaExhaustedError:
                stop_reason = "daily API quota exhausted during channels.list '%s'" % query
                logger.error(stop_reason)
                break
            for ch in details:
                cid = ch["channel_id"]
                channels[cid] = {
                    "channel_id": cid, "title": ch.get("title"),
                    "published_at": ch.get("published_at"),
                    "subscriber_count": ch.get("subscriber_count"),
                    "video_count": ch.get("video_count"),
                    "topic_1": ch.get("topic_1"), "topic_2": ch.get("topic_2"),
                    "country": ch.get("country"),
                    "first_query": query, "first_family": family,
                }

        ck["completed_queries"].append(query)
        ck["query_records"].append({
            "family": family, "query": query, "search_results": len(results),
            "unique_channels_in_query": len(query_cids),
            "new_channels_added": len(new_ids),
            "cumulative_units": total_units(),
        })
        ck["units_used"] = total_units()
        save_checkpoint(ck)
        logger.info("QUOTA: %d units total | %d channels | %d eligible",
                    total_units(), len(channels), eligible_count(channels))

    if stop_reason is None:
        stop_reason = "all %d queries exhausted" % len(all_queries)
    logger.info("STOP: %s", stop_reason)

    for c in channels.values():
        c["arm1_eligible"] = is_arm1_eligible(c.get("published_at"), c.get("video_count"))
        c["on_roster"] = c["channel_id"] in roster_ids

    if not test_mode:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        cols = ["channel_id", "title", "published_at", "subscriber_count", "video_count",
                "topic_1", "topic_2", "country", "first_query", "first_family",
                "arm1_eligible", "on_roster"]
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for c in channels.values():
                w.writerow(c)
        logger.info("Wrote %d channels to %s", len(channels), CSV_PATH)

    n = len(channels)
    n_eligible = eligible_count(channels)
    per_family: Dict[str, Dict] = {}
    for fam in QUERY_FAMILIES:
        fl = [c for c in channels.values() if c["first_family"] == fam]
        if fl:
            per_family[fam] = {
                "channels": len(fl),
                "eligible": sum(1 for c in fl if c["arm1_eligible"]),
                "on_roster": sum(1 for c in fl if c["on_roster"]),
            }
    summary = {
        "run": "cohort_b_arm1_discovery_production",
        "test_mode": test_mode,
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "stop_reason": stop_reason,
        "quota_units_total": total_units(),
        "quota_hard_cap": QUOTA_HARD_CAP,
        "queries_completed": len(ck["completed_queries"]),
        "queries_planned": len(all_queries),
        "unique_channels": n,
        "arm1_eligible": n_eligible,
        "arm1_eligible_share": round(n_eligible / n, 4) if n else None,
        "on_roster": sum(1 for c in channels.values() if c["on_roster"]),
        "per_family": per_family,
        "per_query": ck["query_records"],
        "csv": str(CSV_PATH),
        "caveat": ("video_count is current count, upper bound on uploads by June 2022; "
                   "uploads-at-cutoff reconstruction happens at enumeration."),
    }
    if not test_mode:
        SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info("Summary written to %s", SUMMARY_PATH)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Cohort B Arm 1 production discovery")
    parser.add_argument("--test", action="store_true", help="1 query, 1 page only")
    parser.add_argument("--limit", type=int, default=None, help="Cap number of queries")
    args = parser.parse_args()

    log_path = PAPER_OUTPUT_DIR / (
        "cohort_b_discovery_test_log.txt" if args.test else "cohort_b_discovery_log.txt")
    setup_logging(log_path)
    config.ensure_directories()
    logger.info("=" * 60)
    logger.info("COHORT B ARM 1 PRODUCTION DISCOVERY%s", " (TEST)" if args.test else "")
    logger.info("=" * 60)
    summary = run(test_mode=args.test, limit=args.limit)
    logger.info("SUMMARY: %d channels | %s eligible | %d units | stop: %s",
                summary["unique_channels"], summary["arm1_eligible_share"],
                summary["quota_units_total"], summary["stop_reason"])


if __name__ == "__main__":
    main()
