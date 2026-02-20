"""
check_daily_health.py
---------------------
Lightweight daily health check for panel statistics collection.
Runs via launchd at 10:30 UTC after daily stats complete.

Checks:
  (a) Today's gender gap channel stats CSV exists
  (b) Row count within 5% of expected (~9,760)
  (c) Today's AI census channel stats CSV exists
  (d) No FAILED_*.flag sentinel files in data/logs/

Usage:
    python -m src.validation.check_daily_health
"""

import csv
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXPECTED_GENDER_GAP = 9760
TOLERANCE = 0.05


def main():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    issues = []

    # (a) + (b) Gender gap channel stats
    gg_path = config.get_daily_panel_path('channel_stats', today)
    if not gg_path.exists():
        issues.append("MISSING: gender gap channel stats ({})".format(gg_path.name))
    else:
        with open(gg_path, 'r', encoding='utf-8') as f:
            row_count = sum(1 for _ in csv.reader(f)) - 1
        lo = int(EXPECTED_GENDER_GAP * (1 - TOLERANCE))
        hi = int(EXPECTED_GENDER_GAP * (1 + TOLERANCE))
        if lo <= row_count <= hi:
            logger.info("Gender gap OK: %d rows", row_count)
        else:
            issues.append("ROW COUNT: gender gap has {} rows (expected {}-{})".format(
                row_count, lo, hi))

    # (c) AI census channel stats
    ai_path = config.get_daily_panel_path('channel_stats', today, panel_name='ai_census')
    if not ai_path.exists():
        issues.append("MISSING: AI census channel stats ({})".format(ai_path.name))
    else:
        with open(ai_path, 'r', encoding='utf-8') as f:
            row_count = sum(1 for _ in csv.reader(f)) - 1
        logger.info("AI census OK: %d rows", row_count)

    # (d) Failure sentinels
    for flag in sorted(config.LOGS_DIR.glob("daily_stats_FAILED_*.flag")):
        issues.append("SENTINEL: {}".format(flag.name))

    if issues:
        report_path = config.LOGS_DIR / "health_check_{}.txt".format(today)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Daily health check FAILED: {}\n\n".format(today))
            for issue in issues:
                f.write("- {}\n".format(issue))
        logger.error("FAILED (%d issues). Report: %s", len(issues), report_path)
        sys.exit(1)

    logger.info("Daily health check PASSED for %s", today)


if __name__ == "__main__":
    main()
