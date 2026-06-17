#!/usr/bin/env python3
"""09_thumb_aggregate_channel.py — KE thumbnail-gender pipeline step 4 (channel aggregation).

Rebuilds the canonical per-channel gender file deterministically from the per-image DeepFace
raw output (step 08). Pipeline discipline: the per-channel CSV is an OUTPUT only — never
hand-edited. Step 08 writes a per-channel file incrementally for live monitoring, but THIS
script is the authoritative collapse (idempotent, dedup-safe, reproducible from the raw).

Mirrors do-file 92's aggregation role. Aggregation rule (matches step 08):
  - n_images, n_face_images per channel.
  - deepface_female_share = share of detected faces reading Woman.
  - deepface_label = 'woman' if share > 0.5 else 'man' (only if n_face_images >= 1).
  - confidence_tier keyed to n_face_images (none/tier1/tier2/tier3/tier4plus) — the
    validated 75% -> 97% reliability ladder.
  - Item-nonresponse: n_fetch_fail / fetch_fail_any from the fetch log (dead/placeholder).

INPUT : data/processed/ke_thumb_deepface_raw.csv     (step 08, 1 row per image)
        data/processed/ke_thumbnails/ke_thumb_fetch_log.csv (nonresponse)
OUTPUT: data/processed/ke_thumb_gender_channel.csv   (1 row per channel, OVERWRITTEN)

Usage:
  python3 09_thumb_aggregate_channel.py
"""
from __future__ import annotations

import csv
import io
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

REPO = Path(__file__).resolve().parents[2]
THUMB_DIR = REPO / "data" / "processed" / "ke_thumbnails"
RAW = REPO / "data" / "processed" / "ke_thumb_deepface_raw.csv"
FETCH_LOG = THUMB_DIR / "ke_thumb_fetch_log.csv"
OUT = REPO / "data" / "processed" / "ke_thumb_gender_channel.csv"

OUT_FIELDS = ["channel_id", "n_images", "n_face_images", "deepface_female_share",
              "deepface_label", "confidence_tier", "n_fetch_fail", "fetch_fail_any"]

logging.basicConfig(level=logging.INFO, format="[09] %(message)s")
log = logging.getLogger(__name__)


def confidence_tier(n_face: int) -> str:
    if n_face <= 0:
        return "none"
    return {1: "tier1", 2: "tier2", 3: "tier3"}.get(n_face, "tier4plus")


def nul_safe_dictreader(path: Path) -> csv.DictReader:
    with open(path, "rb") as f:
        raw = f.read().replace(b"\x00", b"")
    return csv.DictReader(io.StringIO(raw.decode("utf-8", errors="replace")))


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"[09] raw per-image file missing: {RAW} (run step 08 first)")

    # Collapse per-image -> per-channel, deduping on (channel_id, slot) keeping the last.
    by_chan_imgs: "defaultdict[str, Dict[str, dict]]" = defaultdict(dict)
    n_rows = 0
    for r in nul_safe_dictreader(RAW):
        cid = r["channel_id"]
        slot = r.get("slot", "")
        by_chan_imgs[cid][slot] = r  # last write wins -> dedup
        n_rows += 1

    # Fetch-failure counts (item nonresponse).
    fail_counts: "defaultdict[str, int]" = defaultdict(int)
    if FETCH_LOG.exists():
        for r in nul_safe_dictreader(FETCH_LOG):
            if (r.get("status") or "") in ("dead", "placeholder", "error"):
                fail_counts[r["channel_id"]] += 1

    rows_out: List[dict] = []
    label_counts = {"woman": 0, "man": 0, "none": 0}
    tier_counts: "defaultdict[str, int]" = defaultdict(int)
    for cid, slots in by_chan_imgs.items():
        imgs = list(slots.values())
        n_images = len(imgs)
        faces = [r for r in imgs if str(r.get("face_present")).lower() == "true"]
        n_face = len(faces)
        if n_face >= 1:
            n_woman = sum(1 for r in faces if (r.get("dominant_gender") or "").lower() == "woman")
            share = n_woman / n_face
            label = "woman" if share > 0.5 else "man"
            label_counts[label] += 1
        else:
            share = None
            label = None
            label_counts["none"] += 1
        tier = confidence_tier(n_face)
        tier_counts[tier] += 1
        rows_out.append({
            "channel_id": cid, "n_images": n_images, "n_face_images": n_face,
            "deepface_female_share": (round(share, 4) if share is not None else ""),
            "deepface_label": label or "", "confidence_tier": tier,
            "n_fetch_fail": fail_counts.get(cid, 0),
            "fetch_fail_any": int(fail_counts.get(cid, 0) > 0),
        })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        w.writeheader()
        for row in rows_out:
            w.writerow(row)

    log.info("per-image rows read: %s", f"{n_rows:,}")
    log.info("channels out: %s", f"{len(rows_out):,}")
    log.info("  label woman/man/none: %s / %s / %s",
             f"{label_counts['woman']:,}", f"{label_counts['man']:,}", f"{label_counts['none']:,}")
    log.info("  confidence tiers: %s",
             {k: tier_counts[k] for k in ("none", "tier1", "tier2", "tier3", "tier4plus")})
    n_labeled = label_counts["woman"] + label_counts["man"]
    if n_labeled:
        log.info("  female share among labeled channels: %.3f", label_counts["woman"] / n_labeled)
    log.info("wrote -> %s", OUT)


if __name__ == "__main__":
    main()
