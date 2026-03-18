"""
parallel_enumerate.py
---------------------
Splits remaining video enumeration work into N parallel shards and
launches them concurrently, then merges results into the master inventory.

Usage:
    # Prepare shards (creates shard files + launch script):
    python3 -m src.collection.parallel_enumerate --prepare \
        --channel-list data/channels/gender_gap/channel_ids.csv \
        --output data/video_inventory/gender_gap_inventory.csv \
        --shards 10

    # Launch all shards:
    python3 -m src.collection.parallel_enumerate --launch \
        --output data/video_inventory/gender_gap_inventory.csv \
        --shards 10

    # Check status:
    python3 -m src.collection.parallel_enumerate --status \
        --output data/video_inventory/gender_gap_inventory.csv \
        --shards 10

    # Merge completed shards into master inventory:
    python3 -m src.collection.parallel_enumerate --merge \
        --output data/video_inventory/gender_gap_inventory.csv \
        --shards 10

Author: Katie Apker
Last Updated: March 2026
"""

import argparse
import csv
import io
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def get_shard_dir(output_path):
    """Directory for shard files, next to the master output."""
    return output_path.parent / (".shards_%s" % output_path.stem)


def get_completed_channels(output_path):
    """Read completed channel IDs from the checkpoint file."""
    stem = output_path.stem
    ckpt_path = output_path.parent / (".enumerate_%s_checkpoint.json" % stem)

    if ckpt_path.exists():
        with open(ckpt_path, "r") as f:
            data = json.load(f)
        return set(data.get("completed_channels", []))

    # No checkpoint -- try reading the inventory CSV directly (NUL-safe)
    completed = set()
    if output_path.exists():
        with open(output_path, "rb") as f:
            raw = f.read().replace(b"\x00", b"")
        text = raw.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            cid = row.get("channel_id", "").strip()
            if cid:
                completed.add(cid)
    return completed


def prepare_shards(channel_list_path, output_path, num_shards):
    """Split remaining channels into N shard files."""
    # Read all channels
    with open(channel_list_path, "r") as f:
        all_ids = [line.strip() for line in f if line.strip() and not line.startswith("channel_id")]

    # Get already completed
    completed = get_completed_channels(output_path)
    remaining = [c for c in all_ids if c not in completed]

    logger.info("Total channels: %d", len(all_ids))
    logger.info("Already completed: %d", len(completed))
    logger.info("Remaining: %d", len(remaining))

    if not remaining:
        logger.info("Nothing to shard -- all channels already enumerated!")
        return

    # Create shard directory
    shard_dir = get_shard_dir(output_path)
    shard_dir.mkdir(parents=True, exist_ok=True)

    # Split into shards
    shard_size = len(remaining) // num_shards
    extra = len(remaining) % num_shards

    idx = 0
    for i in range(num_shards):
        size = shard_size + (1 if i < extra else 0)
        shard_channels = remaining[idx:idx + size]
        idx += size

        shard_list = shard_dir / ("shard_%02d_channels.csv" % i)
        with open(shard_list, "w") as f:
            f.write("channel_id\n")
            for cid in shard_channels:
                f.write(cid + "\n")

        logger.info("Shard %02d: %d channels -> %s", i, len(shard_channels), shard_list)

    logger.info("Prepared %d shards in %s", num_shards, shard_dir)


def launch_shards(output_path, num_shards, max_runtime=None):
    """Launch N parallel enumerate_videos.py instances in screen sessions."""
    shard_dir = get_shard_dir(output_path)

    for i in range(num_shards):
        shard_list = shard_dir / ("shard_%02d_channels.csv" % i)
        shard_output = shard_dir / ("shard_%02d_inventory.csv" % i)
        screen_name = "enum_shard_%02d" % i

        if not shard_list.exists():
            logger.warning("Shard file missing: %s", shard_list)
            continue

        cmd_parts = [
            "python3", "-m", "src.collection.enumerate_videos",
            "--channel-list", str(shard_list),
            "--output", str(shard_output),
        ]
        if max_runtime is not None:
            cmd_parts.extend(["--max-runtime", str(max_runtime)])

        inner_cmd = " ".join(cmd_parts)
        log_file = str(config.LOGS_DIR / ("enum_shard_%02d_%s.log" % (i, config.get_date_stamp())))

        screen_cmd = [
            "screen", "-dmS", screen_name,
            "bash", "-c",
            "%s 2>&1 | tee %s" % (inner_cmd, log_file),
        ]

        subprocess.run(screen_cmd)
        logger.info("Launched shard %02d in screen '%s'", i, screen_name)

    logger.info("All %d shards launched. Monitor with --status.", num_shards)


def check_status(output_path, num_shards):
    """Check completion status of all shards."""
    shard_dir = get_shard_dir(output_path)
    total_remaining = 0
    total_done = 0
    all_complete = True

    for i in range(num_shards):
        shard_list = shard_dir / ("shard_%02d_channels.csv" % i)
        shard_output = shard_dir / ("shard_%02d_inventory.csv" % i)
        shard_ckpt = shard_dir / (".enumerate_shard_%02d_inventory_checkpoint.json" % i)

        # Count channels in shard
        shard_total = 0
        if shard_list.exists():
            with open(shard_list) as f:
                shard_total = sum(1 for line in f if line.strip() and not line.startswith("channel_id"))

        # Count completed in shard
        shard_done = 0
        if shard_ckpt.exists():
            with open(shard_ckpt) as f:
                data = json.load(f)
            shard_done = len(data.get("completed_channels", []))
        elif shard_output.exists() and not shard_ckpt.exists():
            # No checkpoint but output exists = probably complete
            shard_done = shard_total

        status = "DONE" if shard_done >= shard_total else "RUNNING"
        if shard_done < shard_total:
            all_complete = False

        total_remaining += shard_total - shard_done
        total_done += shard_done

        logger.info(
            "Shard %02d: %d/%d channels (%s)",
            i, shard_done, shard_total, status,
        )

    logger.info("---")
    logger.info("Total: %d done, %d remaining", total_done, total_remaining)
    if all_complete:
        logger.info("ALL SHARDS COMPLETE. Run --merge to combine.")
    return all_complete


def merge_shards(output_path, num_shards):
    """Merge shard outputs into the master inventory."""
    shard_dir = get_shard_dir(output_path)

    # Read existing master inventory (NUL-safe)
    existing_rows = []
    existing_ids = set()
    if output_path.exists():
        with open(output_path, "rb") as f:
            raw = f.read().replace(b"\x00", b"")
        text = raw.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            cid = row.get("channel_id", "").strip()
            if cid and cid not in existing_ids:
                existing_rows.append(row)
                existing_ids.add(cid)

    logger.info("Existing inventory: %d channels", len(existing_rows))

    # Read each shard
    new_count = 0
    for i in range(num_shards):
        shard_output = shard_dir / ("shard_%02d_inventory.csv" % i)
        if not shard_output.exists():
            logger.warning("Shard %02d output missing, skipping", i)
            continue

        with open(shard_output, "rb") as f:
            raw = f.read().replace(b"\x00", b"")
        text = raw.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            cid = row.get("channel_id", "").strip()
            if cid and cid not in existing_ids:
                existing_rows.append(row)
                existing_ids.add(cid)
                new_count += 1

    logger.info("New from shards: %d channels", new_count)
    logger.info("Total after merge: %d channels", len(existing_rows))

    # Determine fieldnames from existing data
    if existing_rows:
        fieldnames = list(existing_rows[0].keys())
    else:
        logger.error("No data to merge!")
        return

    # Write merged inventory
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    logger.info("Merged inventory written to %s", output_path)

    # Rebuild master checkpoint from merged data
    stem = output_path.stem
    ckpt_path = output_path.parent / (".enumerate_%s_checkpoint.json" % stem)
    with open(ckpt_path, "w") as f:
        json.dump({"completed_channels": list(existing_ids)}, f)
    logger.info("Checkpoint rebuilt with %d completed channels", len(existing_ids))


def main():
    parser = argparse.ArgumentParser(description="Parallel video enumeration")
    parser.add_argument("--channel-list", type=str, help="Master channel list CSV")
    parser.add_argument("--output", type=str, required=True, help="Master inventory CSV path")
    parser.add_argument("--shards", type=int, default=10, help="Number of parallel shards")
    parser.add_argument("--max-runtime", type=int, default=None, help="Max runtime per shard (seconds)")
    parser.add_argument("--prepare", action="store_true", help="Prepare shard files")
    parser.add_argument("--launch", action="store_true", help="Launch shard screen sessions")
    parser.add_argument("--status", action="store_true", help="Check shard completion status")
    parser.add_argument("--merge", action="store_true", help="Merge shards into master inventory")
    args = parser.parse_args()

    setup_logging()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = config.PROJECT_ROOT / output_path

    if args.prepare:
        if not args.channel_list:
            logger.error("--channel-list required for --prepare")
            sys.exit(1)
        channel_list = Path(args.channel_list)
        if not channel_list.is_absolute():
            channel_list = config.PROJECT_ROOT / channel_list
        prepare_shards(channel_list, output_path, args.shards)

    elif args.launch:
        launch_shards(output_path, args.shards, max_runtime=args.max_runtime)

    elif args.status:
        check_status(output_path, args.shards)

    elif args.merge:
        merge_shards(output_path, args.shards)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
