"""
health_check.py
---------------
Pipeline health check for the YouTube longitudinal panel collection.

Validates that daily/weekly collection jobs are running, output data
looks correct, and no errors are accumulating in logs.

Usage:
    python -m src.validation.health_check [--json]

Exit codes: 0=HEALTHY, 1=DEGRADED, 2=FAILING

Author: Katie Apker
Created: Feb 16, 2026
"""

import argparse
import csv
import json
import logging
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Thresholds
EXPECTED_CHANNEL_COUNT = 9760
CHANNEL_COUNT_TOLERANCE = 0.01  # 1%
MIN_VIDEO_STATS_ROWS = 100_000
DISK_USAGE_WARN_PCT = 80
QUOTA_WARN_THRESHOLD = 900_000
CHECKPOINT_STALE_HOURS = 24
STDERR_TAIL_LINES = 50
ERROR_PATTERNS = ["ERROR", "CRITICAL", "Exception", "Traceback"]


class CheckResult:
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

    def __init__(self, name: str, status: str, message: str, details: Optional[Dict] = None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


class HealthChecker:
    def __init__(self):
        self.results: List[CheckResult] = []
        self.today_stamp = datetime.utcnow().strftime("%Y%m%d")

    def check_channel_stats_freshness(self) -> CheckResult:
        """Did today's channel stats file get created?"""
        files = sorted(config.CHANNEL_STATS_DIR.glob("*.csv"))
        if not files:
            return CheckResult(
                "channel_stats_freshness", CheckResult.CRITICAL,
                "No channel stats files found",
            )
        latest = files[-1]
        try:
            latest_date = datetime.strptime(latest.stem, "%Y-%m-%d")
            days_ago = (datetime.utcnow() - latest_date).days
        except ValueError:
            days_ago = -1

        if days_ago <= 1:
            return CheckResult(
                "channel_stats_freshness", CheckResult.OK,
                f"Latest: {latest.name} ({days_ago} day(s) ago)",
                {"latest_file": latest.name, "days_since_last": days_ago},
            )
        if days_ago <= 3:
            return CheckResult(
                "channel_stats_freshness", CheckResult.WARNING,
                f"Channel stats {days_ago} days stale (latest: {latest.name})",
                {"latest_file": latest.name, "days_since_last": days_ago},
            )
        return CheckResult(
            "channel_stats_freshness", CheckResult.CRITICAL,
            f"Channel stats {days_ago} days stale (latest: {latest.name})",
            {"latest_file": latest.name, "days_since_last": days_ago},
        )

    def check_channel_stats_completeness(self) -> CheckResult:
        """Does the latest channel stats file have ~9,760 rows?"""
        files = sorted(config.CHANNEL_STATS_DIR.glob("*.csv"))
        if not files:
            return CheckResult(
                "channel_stats_completeness", CheckResult.CRITICAL,
                "No channel stats files to validate",
            )
        latest = files[-1]
        row_count = 0
        header: List[str] = []
        try:
            with open(latest, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                for _ in reader:
                    row_count += 1
        except Exception as e:
            return CheckResult(
                "channel_stats_completeness", CheckResult.CRITICAL,
                f"Failed to read {latest.name}: {e}",
            )

        problems: List[str] = []
        expected_cols = set(config.CHANNEL_STATS_FIELDS)
        actual_cols = set(header)
        missing = expected_cols - actual_cols
        if missing:
            problems.append(f"Missing columns: {sorted(missing)}")

        lower = int(EXPECTED_CHANNEL_COUNT * (1 - CHANNEL_COUNT_TOLERANCE))
        upper = int(EXPECTED_CHANNEL_COUNT * (1 + CHANNEL_COUNT_TOLERANCE))
        if row_count < lower or row_count > upper:
            problems.append(f"Row count {row_count} outside expected [{lower}, {upper}]")

        if problems:
            status = CheckResult.WARNING if row_count > 0 else CheckResult.CRITICAL
            return CheckResult(
                "channel_stats_completeness", status,
                f"{latest.name}: {'; '.join(problems)}",
                {"file": latest.name, "row_count": row_count, "columns": header},
            )
        return CheckResult(
            "channel_stats_completeness", CheckResult.OK,
            f"{latest.name}: {row_count} rows, all columns present",
            {"file": latest.name, "row_count": row_count},
        )

    def check_video_stats_freshness(self) -> CheckResult:
        """Was there a video stats file from the most recent Sunday?"""
        files = sorted(config.VIDEO_STATS_DIR.glob("*.csv"))
        if not files:
            return CheckResult(
                "video_stats_freshness", CheckResult.WARNING,
                "No video stats files found (collection may not have started yet)",
            )
        latest = files[-1]
        try:
            latest_date = datetime.strptime(latest.stem, "%Y-%m-%d")
            days_ago = (datetime.utcnow() - latest_date).days
        except ValueError:
            days_ago = -1

        if days_ago <= 8:
            return CheckResult(
                "video_stats_freshness", CheckResult.OK,
                f"Latest video stats: {latest.name} ({days_ago} day(s) ago)",
            )
        return CheckResult(
            "video_stats_freshness", CheckResult.WARNING,
            f"Video stats {days_ago} days stale (latest: {latest.name})",
        )

    def check_video_stats_completeness(self) -> CheckResult:
        """Does the latest video stats file have a reasonable row count?"""
        files = sorted(config.VIDEO_STATS_DIR.glob("*.csv"))
        if not files:
            return CheckResult(
                "video_stats_completeness", CheckResult.WARNING,
                "No video stats files to validate",
            )
        latest = files[-1]
        row_count = 0
        try:
            with open(latest, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for _ in reader:
                    row_count += 1
        except Exception as e:
            return CheckResult(
                "video_stats_completeness", CheckResult.CRITICAL,
                f"Failed to read {latest.name}: {e}",
            )
        if row_count < MIN_VIDEO_STATS_ROWS:
            return CheckResult(
                "video_stats_completeness", CheckResult.WARNING,
                f"{latest.name}: only {row_count:,} rows (expected >{MIN_VIDEO_STATS_ROWS:,})",
                {"file": latest.name, "row_count": row_count},
            )
        return CheckResult(
            "video_stats_completeness", CheckResult.OK,
            f"{latest.name}: {row_count:,} rows",
        )

    def check_log_errors(self) -> CheckResult:
        """Scan stderr logs for errors."""
        log_files = [
            config.LOGS_DIR / "daily_channel_stats_stderr.log",
            config.LOGS_DIR / "weekly_video_stats_stderr.log",
        ]
        found_errors: Dict[str, List[str]] = {}
        for log_path in log_files:
            if not log_path.exists():
                continue
            try:
                lines = _tail_file(log_path, STDERR_TAIL_LINES)
                matches = [l for l in lines if any(p in l for p in ERROR_PATTERNS)]
                if matches:
                    found_errors[log_path.name] = matches
            except Exception as e:
                found_errors[log_path.name] = [f"Could not read log: {e}"]

        if not found_errors:
            return CheckResult("log_errors", CheckResult.OK, "No errors in recent stderr logs")
        total = sum(len(v) for v in found_errors.values())
        return CheckResult(
            "log_errors", CheckResult.WARNING,
            f"Found {total} error line(s) across {len(found_errors)} log file(s)",
            {"errors_by_file": {k: v[:5] for k, v in found_errors.items()}},
        )

    def check_inventory_integrity(self) -> CheckResult:
        """Does the video inventory exist and have >50K rows?"""
        inventory_path = config.VIDEO_INVENTORY_DIR / "gender_gap_inventory.csv"
        if not inventory_path.exists():
            return CheckResult(
                "inventory_integrity", CheckResult.CRITICAL,
                f"Video inventory not found: {inventory_path.name}",
            )
        row_count = 0
        try:
            with open(inventory_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for _ in reader:
                    row_count += 1
        except Exception as e:
            return CheckResult(
                "inventory_integrity", CheckResult.CRITICAL,
                f"Failed to read inventory: {e}",
            )
        if row_count < 50_000:
            return CheckResult(
                "inventory_integrity", CheckResult.WARNING,
                f"Inventory has only {row_count:,} rows (expected >50,000). Enumeration may be incomplete.",
                {"row_count": row_count},
            )
        return CheckResult(
            "inventory_integrity", CheckResult.OK,
            f"Inventory has {row_count:,} videos",
        )

    def check_disk_space(self) -> CheckResult:
        """Are we under 80% disk usage?"""
        try:
            usage = shutil.disk_usage(config.PROJECT_ROOT)
            used_pct = (usage.used / usage.total) * 100
            free_gb = usage.free / (1024 ** 3)
        except Exception as e:
            return CheckResult("disk_space", CheckResult.WARNING, f"Could not check: {e}")

        if used_pct >= DISK_USAGE_WARN_PCT:
            return CheckResult(
                "disk_space", CheckResult.WARNING,
                f"Disk at {used_pct:.1f}% ({free_gb:.1f} GB free)",
            )
        return CheckResult(
            "disk_space", CheckResult.OK,
            f"Disk at {used_pct:.1f}% ({free_gb:.1f} GB free)",
        )

    def check_quota_usage(self) -> CheckResult:
        """Is the latest quota log showing usage under 900K units?"""
        quota_path = None
        for offset in range(3):
            date_str = (datetime.utcnow() - timedelta(days=offset)).strftime("%Y%m%d")
            candidate = config.LOGS_DIR / f"quota_{date_str}.csv"
            if candidate.exists():
                quota_path = candidate
                break
        if not quota_path:
            return CheckResult("quota_usage", CheckResult.WARNING, "No recent quota log (last 3 days)")

        total_units = 0
        try:
            with open(quota_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    units = row.get("units") or row.get("quota_used") or "0"
                    try:
                        total_units += int(units)
                    except (ValueError, TypeError):
                        pass
        except Exception as e:
            return CheckResult("quota_usage", CheckResult.WARNING, f"Could not parse {quota_path.name}: {e}")

        if total_units >= QUOTA_WARN_THRESHOLD:
            return CheckResult(
                "quota_usage", CheckResult.WARNING,
                f"Quota high: {total_units:,} units ({quota_path.name})",
            )
        return CheckResult(
            "quota_usage", CheckResult.OK,
            f"Quota: {total_units:,} units ({quota_path.name})",
        )

    def check_stale_checkpoint(self) -> CheckResult:
        """Is there a leftover checkpoint older than 24 hours?"""
        cp_path = config.DAILY_PANELS_DIR / ".daily_stats_checkpoint.json"
        if not cp_path.exists():
            return CheckResult("stale_checkpoint", CheckResult.OK, "No checkpoint (clean state)")

        try:
            mtime = datetime.utcfromtimestamp(cp_path.stat().st_mtime)
            age_hours = (datetime.utcnow() - mtime).total_seconds() / 3600
        except Exception as e:
            return CheckResult("stale_checkpoint", CheckResult.WARNING, f"Could not stat checkpoint: {e}")

        if age_hours > CHECKPOINT_STALE_HOURS:
            cp_data = {}
            try:
                with open(cp_path, "r") as f:
                    cp_data = json.load(f)
            except Exception:
                pass
            return CheckResult(
                "stale_checkpoint", CheckResult.CRITICAL,
                f"Stale checkpoint: {age_hours:.1f}h old. Collection run likely failed.",
                {"age_hours": round(age_hours, 1), "checkpoint_date": cp_data.get("date")},
            )
        return CheckResult(
            "stale_checkpoint", CheckResult.OK,
            f"Checkpoint exists, recent ({age_hours:.1f}h old, likely in-progress)",
        )

    def run_all(self) -> List[CheckResult]:
        checks = [
            self.check_channel_stats_freshness,
            self.check_channel_stats_completeness,
            self.check_video_stats_freshness,
            self.check_video_stats_completeness,
            self.check_log_errors,
            self.check_inventory_integrity,
            self.check_disk_space,
            self.check_quota_usage,
            self.check_stale_checkpoint,
        ]
        self.results = []
        for check_fn in checks:
            try:
                result = check_fn()
            except Exception as e:
                result = CheckResult(
                    check_fn.__name__.replace("check_", ""),
                    CheckResult.CRITICAL, f"Check raised exception: {e}",
                )
            self.results.append(result)
        return self.results

    def overall_status(self) -> str:
        statuses = [r.status for r in self.results]
        if CheckResult.CRITICAL in statuses:
            return "FAILING"
        if CheckResult.WARNING in statuses:
            return "DEGRADED"
        return "HEALTHY"

    def format_text_report(self) -> str:
        overall = self.overall_status()
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            "=" * 70,
            f"  PIPELINE HEALTH CHECK  |  {overall}  |  {ts}",
            "=" * 70, "",
        ]
        ok = sum(1 for r in self.results if r.status == CheckResult.OK)
        warn = sum(1 for r in self.results if r.status == CheckResult.WARNING)
        crit = sum(1 for r in self.results if r.status == CheckResult.CRITICAL)
        lines.append(f"  {ok} OK  |  {warn} WARNING  |  {crit} CRITICAL")
        lines.extend(["", "-" * 70])

        badges = {"OK": "[  OK  ]", "WARNING": "[ WARN ]", "CRITICAL": "[CRIT!!]"}
        for r in self.results:
            lines.append(f"  {badges[r.status]}  {r.name}")
            lines.append(f"           {r.message}")
            if r.details and r.status != CheckResult.OK:
                for k, v in r.details.items():
                    if isinstance(v, list):
                        for item in v[:3]:
                            lines.append(f"             - {item}")
                    else:
                        lines.append(f"             {k}: {v}")
            lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    def format_json_report(self) -> str:
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "overall_status": self.overall_status(),
            "checks": [r.to_dict() for r in self.results],
        }, indent=2)

    def save_report(self, text_report: str) -> Path:
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = config.LOGS_DIR / f"health_check_{self.today_stamp}.log"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text_report)
        return output_path


def _tail_file(path: Path, n: int) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return [line.rstrip("\n") for line in all_lines[-n:]]
    except Exception:
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Health check for YouTube longitudinal pipeline")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    args = parser.parse_args()

    checker = HealthChecker()
    checker.run_all()

    if args.json:
        report = checker.format_json_report()
        print(report)
        text_report = checker.format_text_report()
        checker.save_report(text_report)
    else:
        report = checker.format_text_report()
        print(report)
        checker.save_report(report)

    overall = checker.overall_status()
    if overall == "FAILING":
        sys.exit(2)
    elif overall == "DEGRADED":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
