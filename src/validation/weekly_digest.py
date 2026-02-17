"""
weekly_digest.py
----------------
Generate a weekly summary of the YouTube longitudinal panel data.

Produces a human-readable markdown report covering:
- Date range and file counts
- Collection completeness
- Growth trends across the panel
- Data volume and health check history

Usage:
    python -m src.validation.weekly_digest

Output: data/logs/weekly_digest_YYYYMMDD.md

Author: Katie Apker
Created: Feb 16, 2026
"""

import csv
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def get_files_in_range(directory: Path, start: datetime, end: datetime) -> List[Path]:
    """Get CSV files in a date range (filenames are YYYY-MM-DD.csv)."""
    files = []
    for f in sorted(directory.glob("*.csv")):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d")
            if start <= file_date <= end:
                files.append(f)
        except ValueError:
            continue
    return files


def count_rows(filepath: Path) -> int:
    """Count data rows (excluding header) in a CSV."""
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for _ in reader:
            count += 1
    return count


def compute_channel_trends(files: List[Path]) -> Optional[Dict]:
    """Compute avg subscriber and view changes across first and last file."""
    if len(files) < 2:
        return None

    def load_stats(path: Path) -> Dict[str, Dict]:
        stats = {}
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("channel_id", "").strip()
                if cid:
                    stats[cid] = {
                        "subs": int(row.get("subscriber_count") or 0),
                        "views": int(row.get("view_count") or 0),
                    }
        return stats

    first_stats = load_stats(files[0])
    last_stats = load_stats(files[-1])
    common = set(first_stats.keys()) & set(last_stats.keys())
    if not common:
        return None

    sub_changes = []
    view_changes = []
    for cid in common:
        sub_changes.append(last_stats[cid]["subs"] - first_stats[cid]["subs"])
        view_changes.append(last_stats[cid]["views"] - first_stats[cid]["views"])

    return {
        "channels_tracked": len(common),
        "avg_sub_change": sum(sub_changes) / len(sub_changes),
        "median_sub_change": sorted(sub_changes)[len(sub_changes) // 2],
        "avg_view_change": sum(view_changes) / len(view_changes),
        "total_view_growth": sum(view_changes),
    }


def dir_size_mb(directory: Path) -> float:
    """Total size of all files in a directory tree, in MB."""
    total = 0
    if directory.exists():
        for f in directory.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    return total / (1024 * 1024)


def get_health_check_summary(start: datetime, end: datetime) -> List[str]:
    """Summarize health check results from the week."""
    failures = []
    for f in sorted(config.LOGS_DIR.glob("health_check_*.log")):
        try:
            date_str = f.stem.replace("health_check_", "")
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if start <= file_date <= end:
                with open(f, "r") as fh:
                    first_lines = fh.read(500)
                if "FAILING" in first_lines:
                    failures.append(f"{f.stem}: FAILING")
                elif "DEGRADED" in first_lines:
                    failures.append(f"{f.stem}: DEGRADED")
        except (ValueError, OSError):
            continue
    return failures


def generate_digest() -> str:
    """Generate the weekly digest markdown report."""
    now = datetime.utcnow()
    week_end = now
    week_start = now - timedelta(days=7)

    lines = [
        f"# Weekly Digest: YouTube Longitudinal Panel",
        f"",
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Period:** {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}",
        f"",
        f"---",
        f"",
    ]

    # Channel stats
    ch_files = get_files_in_range(config.CHANNEL_STATS_DIR, week_start, week_end)
    lines.append(f"## Channel Stats")
    lines.append(f"- Files collected this week: **{len(ch_files)}** (expected 7)")
    if ch_files:
        latest_rows = count_rows(ch_files[-1])
        lines.append(f"- Latest file: {ch_files[-1].name} ({latest_rows:,} rows)")
    lines.append("")

    # Video stats
    vid_files = get_files_in_range(config.VIDEO_STATS_DIR, week_start, week_end)
    lines.append(f"## Video Stats")
    lines.append(f"- Files collected this week: **{len(vid_files)}** (expected 1)")
    if vid_files:
        latest_rows = count_rows(vid_files[-1])
        lines.append(f"- Latest file: {vid_files[-1].name} ({latest_rows:,} rows)")
    lines.append("")

    # Inventory
    inv_path = config.VIDEO_INVENTORY_DIR / "gender_gap_inventory.csv"
    lines.append(f"## Video Inventory")
    if inv_path.exists():
        inv_rows = count_rows(inv_path)
        lines.append(f"- Total videos tracked: **{inv_rows:,}**")
    else:
        lines.append(f"- Inventory file not found")
    lines.append("")

    # Growth trends
    if len(ch_files) >= 2:
        trends = compute_channel_trends(ch_files)
        if trends:
            lines.append(f"## Growth Trends (week-over-week)")
            lines.append(f"- Channels tracked: {trends['channels_tracked']:,}")
            lines.append(f"- Avg subscriber change: {trends['avg_sub_change']:+,.1f}")
            lines.append(f"- Median subscriber change: {trends['median_sub_change']:+,}")
            lines.append(f"- Avg view change per channel: {trends['avg_view_change']:+,.0f}")
            lines.append(f"- Total view growth across panel: {trends['total_view_growth']:+,}")
            lines.append("")

    # Data volume
    panel_size = dir_size_mb(config.DAILY_PANELS_DIR)
    inv_size = dir_size_mb(config.VIDEO_INVENTORY_DIR)
    log_size = dir_size_mb(config.LOGS_DIR)
    lines.append(f"## Data Volume")
    lines.append(f"- Daily panels: {panel_size:.1f} MB")
    lines.append(f"- Video inventory: {inv_size:.1f} MB")
    lines.append(f"- Logs: {log_size:.1f} MB")
    lines.append(f"- **Total: {panel_size + inv_size + log_size:.1f} MB**")
    lines.append("")

    # Health check history
    hc_issues = get_health_check_summary(week_start, week_end)
    lines.append(f"## Health Check History")
    if hc_issues:
        lines.append(f"- **{len(hc_issues)} issue(s) this week:**")
        for issue in hc_issues:
            lines.append(f"  - {issue}")
    else:
        lines.append(f"- All checks passed (or no health check logs found)")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    config.ensure_directories()
    report = generate_digest()
    print(report)

    output_path = config.LOGS_DIR / f"weekly_digest_{datetime.utcnow().strftime('%Y%m%d')}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"Digest saved to {output_path}")


if __name__ == "__main__":
    main()
