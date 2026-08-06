"""
discover_cohort_b_pilot.py
--------------------------
Cohort B Arm 1 discovery PILOT for the "Who Explains AI?" paper.

Runs a small, hard-capped set of search queries with pre-treatment discovery
windows (publishedAfter=2021-07-01, publishedBefore=2022-06-01) so the video
that makes a channel discoverable predates the first AI tool launch in the
calendar (Copilot GA, 2022-06-21). For every discovered channel it records
founding date, subscriber count, video count, and topic hints, then computes:

  - unique channels per query and per query family
  - share meeting Arm 1 eligibility (founded before 2022-06-20, 50+ videos)
  - overlap with the existing 43,546-channel roster (recovery-rate signal)

Design: 4 query families x 3 queries = 12 queries, order=relevance,
max 3 pages per query. Hard quota cap 5,000 units for the whole run
(36 search calls x 100 units = 3,600, plus channels.list batches at 1 unit
per 50 channels). Every unit consumed is logged.

Caveat logged in output: video_count from channels.list is the CURRENT count,
an upper bound on uploads-by-June-2022. The full discovery run will
reconstruct uploads-by-cutoff from upload playlists.

Usage:
    python -m src.collection.discover_cohort_b_pilot --test   # 1 query, 1 page
    python -m src.collection.discover_cohort_b_pilot          # full 12-query pilot

Output:
    papers/gendering-ai-expertise/output/cohort_b_pilot.json (+ _test variant)
    papers/gendering-ai-expertise/output/cohort_b_pilot_log.txt

Author: Katie Apker (agent-drafted pilot)
Created: 2026-08-06
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add src/ to path for imports (same pattern as discover_intent.py)
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

# --- Pilot design parameters (from ROBUST_PLAN_2026-08-06.md, Section 1) ---
REPO_ROOT = Path(__file__).resolve().parents[2]
PAPER_OUTPUT_DIR = REPO_ROOT / "papers" / "gendering-ai-expertise" / "output"
ROSTER_PATH = (
    REPO_ROOT / "papers" / "gendering-ai-expertise" / "processed" / "ke_analysis_base.csv"
)

DISCOVERY_PUBLISHED_AFTER = "2021-07-01T00:00:00Z"
DISCOVERY_PUBLISHED_BEFORE = "2022-06-01T00:00:00Z"
ARM1_FOUNDED_CUTOFF = "2022-06-20"  # day before Copilot GA
ARM1_MIN_VIDEOS = 50
MAX_PAGES_PER_QUERY = 3
SEARCH_CALL_COST = 100
QUOTA_HARD_CAP = 5000  # units for this entire pilot run

QUERY_FAMILIES: Dict[str, List[str]] = {
    "programming_tutorials": [
        "python tutorial",
        "web development course",
        "javascript for beginners",
    ],
    "business_marketing": [
        "marketing strategy",
        "excel tutorial",
        "how to start a business",
    ],
    "knowledge_productivity": [
        "study with me",
        "productivity system",
        "note taking tips",
    ],
    "tech_reviews": [
        "software review",
        "laptop review",
        "best apps",
    ],
}


def setup_logging(log_path: Path) -> None:
    """Configure logging to stream and to the pilot's own log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, mode="w", encoding="utf-8"),
        ],
        force=True,
    )


def load_roster_channel_ids(roster_path: Path) -> Set[str]:
    """Read channel_id column from the roster CSV."""
    roster_ids: Set[str] = set()
    with open(roster_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = (row.get("channel_id") or "").strip()
            if cid:
                roster_ids.add(cid)
    logger.info("Roster loaded: %d channel ids from %s", len(roster_ids), roster_path.name)
    return roster_ids


def quota_headroom_ok(next_call_cost: int, quota_at_start: int) -> bool:
    """True if the next call keeps this run under the pilot hard cap."""
    used_this_run = get_quota_used() - quota_at_start
    return used_this_run + next_call_cost <= QUOTA_HARD_CAP


def is_arm1_eligible(published_at: Optional[str], video_count: Optional[int]) -> bool:
    """Arm 1 eligibility: founded before 2022-06-20 and 50+ videos (current count proxy)."""
    if not published_at or video_count is None:
        return False
    return published_at[:10] < ARM1_FOUNDED_CUTOFF and video_count >= ARM1_MIN_VIDEOS


def run_pilot(test_mode: bool) -> Dict:
    """Execute the pilot and return the full results dictionary."""
    quota_at_start = get_quota_used()
    started_at = datetime.utcnow().isoformat()

    roster_ids = load_roster_channel_ids(ROSTER_PATH)
    youtube = get_authenticated_service()
    logger.info("Authenticated with YouTube API")

    if test_mode:
        first_family = next(iter(QUERY_FAMILIES))
        families = {first_family: QUERY_FAMILIES[first_family][:1]}
        max_pages = 1
        logger.info("TEST MODE: 1 query, 1 page")
    else:
        families = QUERY_FAMILIES
        max_pages = MAX_PAGES_PER_QUERY

    channels_by_id: Dict[str, Dict] = {}
    query_records: List[Dict] = []
    quota_events: List[Dict] = []
    aborted_reason: Optional[str] = None

    def log_quota_event(label: str) -> None:
        used = get_quota_used() - quota_at_start
        quota_events.append({"event": label, "cumulative_units_this_run": used})
        logger.info("QUOTA: %s | cumulative this run: %d units", label, used)

    for family, queries in families.items():
        for query in queries:
            if aborted_reason:
                break
            search_budget = max_pages * SEARCH_CALL_COST
            if not quota_headroom_ok(search_budget, quota_at_start):
                aborted_reason = (
                    "quota hard cap %d would be exceeded before query '%s'"
                    % (QUOTA_HARD_CAP, query)
                )
                logger.warning(aborted_reason)
                break

            logger.info("Searching [%s] '%s' (%d pages, order=relevance, window %s to %s)",
                        family, query, max_pages,
                        DISCOVERY_PUBLISHED_AFTER[:10], DISCOVERY_PUBLISHED_BEFORE[:10])
            try:
                results = search_videos_paginated(
                    youtube=youtube,
                    query=query,
                    published_after=DISCOVERY_PUBLISHED_AFTER,
                    published_before=DISCOVERY_PUBLISHED_BEFORE,
                    max_pages=max_pages,
                    order="relevance",
                )
            except QuotaExhaustedError:
                aborted_reason = "daily API quota exhausted during search for '%s'" % query
                logger.error(aborted_reason)
                break
            log_quota_event("search '%s' (%d results)" % (query, len(results)))

            query_channel_ids: List[str] = []
            seen_in_query: Set[str] = set()
            for item in results:
                cid = item.get("snippet", {}).get("channelId")
                if cid and cid not in seen_in_query:
                    seen_in_query.add(cid)
                    query_channel_ids.append(cid)

            new_ids = [cid for cid in query_channel_ids if cid not in channels_by_id]
            if new_ids:
                if not quota_headroom_ok((len(new_ids) // 50) + 1, quota_at_start):
                    aborted_reason = (
                        "quota hard cap %d would be exceeded by channels.list for '%s'"
                        % (QUOTA_HARD_CAP, query)
                    )
                    logger.warning(aborted_reason)
                    break
                try:
                    details = get_channel_full_details(
                        youtube=youtube,
                        channel_ids=new_ids,
                        stream_type="cohort_b_pilot",
                        discovery_language="English",
                        discovery_keyword=query,
                    )
                except QuotaExhaustedError:
                    aborted_reason = (
                        "daily API quota exhausted during channels.list for '%s'" % query
                    )
                    logger.error(aborted_reason)
                    break
                log_quota_event(
                    "channels.list for '%s' (%d ids, %d returned)"
                    % (query, len(new_ids), len(details))
                )
                for ch in details:
                    cid = ch["channel_id"]
                    channels_by_id[cid] = {
                        "channel_id": cid,
                        "title": ch.get("title"),
                        "published_at": ch.get("published_at"),
                        "subscriber_count": ch.get("subscriber_count"),
                        "video_count": ch.get("video_count"),
                        "topic_1": ch.get("topic_1"),
                        "topic_2": ch.get("topic_2"),
                        "topic_3": ch.get("topic_3"),
                        "country": ch.get("country"),
                        "first_query": query,
                        "first_family": family,
                        "queries_found_by": [],
                    }

            for cid in query_channel_ids:
                if cid in channels_by_id:
                    channels_by_id[cid]["queries_found_by"].append(query)

            query_records.append({
                "family": family,
                "query": query,
                "search_results": len(results),
                "pages_requested": max_pages,
                "unique_channels_in_query": len(query_channel_ids),
                "new_channels_added": len(new_ids),
            })
        if aborted_reason:
            break

    # --- Enrich with eligibility and roster overlap ---
    for ch in channels_by_id.values():
        ch["arm1_eligible"] = is_arm1_eligible(ch.get("published_at"), ch.get("video_count"))
        ch["founded_before_cutoff"] = bool(
            ch.get("published_at") and ch["published_at"][:10] < ARM1_FOUNDED_CUTOFF
        )
        ch["has_min_videos"] = bool(
            ch.get("video_count") is not None and ch["video_count"] >= ARM1_MIN_VIDEOS
        )
        ch["on_roster"] = ch["channel_id"] in roster_ids

    channels = list(channels_by_id.values())
    n = len(channels)
    n_eligible = sum(1 for c in channels if c["arm1_eligible"])
    n_founded_ok = sum(1 for c in channels if c["founded_before_cutoff"])
    n_min_videos = sum(1 for c in channels if c["has_min_videos"])
    n_on_roster = sum(1 for c in channels if c["on_roster"])
    n_eligible_on_roster = sum(1 for c in channels if c["arm1_eligible"] and c["on_roster"])

    per_family: Dict[str, Dict] = {}
    for family in families:
        fam_channels = [c for c in channels if c["first_family"] == family]
        fam_seen: Set[str] = set()
        for c in channels:
            if any(q in families[family] for q in c["queries_found_by"]):
                fam_seen.add(c["channel_id"])
        fam_list = [channels_by_id[cid] for cid in fam_seen]
        per_family[family] = {
            "unique_channels": len(fam_seen),
            "first_discovered_here": len(fam_channels),
            "arm1_eligible": sum(1 for c in fam_list if c["arm1_eligible"]),
            "arm1_eligible_share": round(
                sum(1 for c in fam_list if c["arm1_eligible"]) / len(fam_list), 4
            ) if fam_list else None,
            "on_roster": sum(1 for c in fam_list if c["on_roster"]),
            "on_roster_share": round(
                sum(1 for c in fam_list if c["on_roster"]) / len(fam_list), 4
            ) if fam_list else None,
        }

    total_units = get_quota_used() - quota_at_start
    search_calls = sum(1 for e in quota_events if e["event"].startswith("search"))

    results = {
        "pilot": "cohort_b_arm1_discovery_pilot",
        "test_mode": test_mode,
        "started_at_utc": started_at,
        "finished_at_utc": datetime.utcnow().isoformat(),
        "design": {
            "published_after": DISCOVERY_PUBLISHED_AFTER,
            "published_before": DISCOVERY_PUBLISHED_BEFORE,
            "order": "relevance",
            "max_pages_per_query": max_pages,
            "arm1_founded_cutoff": ARM1_FOUNDED_CUTOFF,
            "arm1_min_videos": ARM1_MIN_VIDEOS,
            "quota_hard_cap_units": QUOTA_HARD_CAP,
            "queries": {fam: qs for fam, qs in families.items()},
        },
        "caveats": [
            "video_count is the channel's CURRENT upload count, an upper bound on "
            "uploads by June 2022; the full run will reconstruct counts at cutoff "
            "from upload playlists.",
            "Roster overlap here is a raw recovery signal on 12 English queries; "
            "the full recovery-rate audit stratifies by gender, adoption status, "
            "and subscriber bracket per the plan.",
        ],
        "quota": {
            "total_units_this_run": total_units,
            "search_calls": search_calls,
            "hard_cap_units": QUOTA_HARD_CAP,
            "events": quota_events,
        },
        "aborted_reason": aborted_reason,
        "per_query": query_records,
        "per_family": per_family,
        "totals": {
            "unique_channels": n,
            "arm1_eligible": n_eligible,
            "arm1_eligible_share": round(n_eligible / n, 4) if n else None,
            "founded_before_2022_06_20": n_founded_ok,
            "founded_before_share": round(n_founded_ok / n, 4) if n else None,
            "has_50plus_videos": n_min_videos,
            "has_50plus_videos_share": round(n_min_videos / n, 4) if n else None,
            "on_roster": n_on_roster,
            "on_roster_share": round(n_on_roster / n, 4) if n else None,
            "arm1_eligible_and_on_roster": n_eligible_on_roster,
            "roster_size": len(roster_ids),
        },
        "channels": channels,
    }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Cohort B Arm 1 discovery pilot")
    parser.add_argument("--test", action="store_true", help="Run 1 query, 1 page only")
    args = parser.parse_args()

    suffix = "_test" if args.test else ""
    out_json = PAPER_OUTPUT_DIR / ("cohort_b_pilot%s.json" % suffix)
    log_path = PAPER_OUTPUT_DIR / ("cohort_b_pilot%s_log.txt" % suffix)
    setup_logging(log_path)
    config.ensure_directories()

    logger.info("=" * 60)
    logger.info("COHORT B ARM 1 DISCOVERY PILOT%s", " (TEST)" if args.test else "")
    logger.info("=" * 60)

    results = run_pilot(test_mode=args.test)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info("Results written to %s", out_json)

    t = results["totals"]
    logger.info("SUMMARY: %d unique channels | eligible %s | on roster %s | %d units",
                t["unique_channels"], t["arm1_eligible_share"], t["on_roster_share"],
                results["quota"]["total_units_this_run"])


if __name__ == "__main__":
    main()
