"""Merge completed shard inventories into the master gender_gap_inventory.csv.

Streams rows with NUL-byte handling (shards may contain NUL from concurrent writes).
"""
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
import config

INVENTORY_DIR = config.PROJECT_ROOT / "data" / "video_inventory"

def merge():
    output = INVENTORY_DIR / "gender_gap_inventory.csv"
    header = ["video_id", "channel_id", "published_at", "title", "scraped_at"]

    seen = set()
    total_videos = 0
    total_channels = set()

    with open(output, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=header)
        writer.writeheader()

        for i in range(10):
            shard_file = INVENTORY_DIR / ("shard_%02d_inventory.csv" % i)
            if not shard_file.exists():
                print("WARNING: shard_%02d_inventory.csv missing" % i)
                continue

            shard_count = 0
            raw = open(shard_file, "rb").read().replace(b"\x00", b"").decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(raw))
            for row in reader:
                vid = row.get("video_id", "").strip()
                if vid and vid not in seen:
                    seen.add(vid)
                    writer.writerow({k: row.get(k, "") for k in header})
                    total_videos += 1
                    shard_count += 1
                    total_channels.add(row.get("channel_id", ""))

            print("Shard %02d: %d videos, running total %d" % (i, shard_count, total_videos))

    print("Merged: %d unique videos, %d channels -> %s" % (total_videos, len(total_channels), output))

if __name__ == "__main__":
    merge()
