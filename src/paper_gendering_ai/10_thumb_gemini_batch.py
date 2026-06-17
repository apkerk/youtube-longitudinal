#!/usr/bin/env python3
"""10_thumb_gemini_batch.py — KE thumbnail-gender pipeline step 5 (PAID, GATED — do NOT run yet).

The Gemini refinement pass over the SAME on-disk KE thumbnails fetched in step 07. Reuses the
validated dissertation instrument (do-files 74 + 78) almost verbatim — gemini-2.5-flash, temp 0,
structured-output JSON, Batch API (50%-off), sequential ~4k-image chunks — so the KE gender
field is measured with the exact instrument that validated at 92-95% (97% with >=4 face-blocks).

ONE MINIMAL ADAPTATION (per Katie 2026-06-17): the dissertation prompt coded apparent_gender as
PACKAGING (the gender presentation foregrounded by the image). Here we ask instead for the
RECURRING CREATOR's perceived gender — the person who appears across the channel's images — while
keeping the structured-output discipline and the face_present / num_faces fields unchanged.

COST CONTROL: the build step packs ONLY the FACE-BEARING images (where step 08's DeepFace found a
face), read from ke_thumb_deepface_raw.csv. Faceless thumbnails carry no creator-gender signal, so
excluding them cuts the paid image count substantially with no loss to the measure.

GATING: this script REQUIRES GEMINI_API_KEY in env and `google-genai` installed. The parent agent
gates execution on the key + spend approval. Until then, `build` is free (writes JSONL only);
`smoke` / `submit` / `run` are the paid steps and must not be run without Katie's sign-off.

INPUT : data/processed/ke_thumb_deepface_raw.csv            (face-bearing image selector)
        data/processed/ke_thumbnails/ke_thumb_fetch_log.csv (ok images)
        data/processed/ke_thumbnails/images/{channel_id}/{slot}.jpg
OUTPUT: data/processed/ke_thumb_gemini_raw.csv              (1 row per image; gender + face fields)
        data/processed/ke_thumbnails/gemini_batch/*          (jsonl, chunk index, jobs, errors)

Usage (run with the Gemini venv once the key is provided, e.g. ~/.venvs/yt-gemini/bin/python):
  python3 10_thumb_gemini_batch.py build     # FREE: pack face-bearing imgs
  python3 10_thumb_gemini_batch.py smoke      # PAID (~cents): 3-image check
  python3 10_thumb_gemini_batch.py run        # PAID: sequential full run
  python3 10_thumb_gemini_batch.py status     # poll jobs
  python3 10_thumb_gemini_batch.py harvest    # parse finished jobs
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
THUMB_DIR = REPO / "data" / "processed" / "ke_thumbnails"
IMG_DIR = THUMB_DIR / "images"
FETCH_LOG = THUMB_DIR / "ke_thumb_fetch_log.csv"
DEEPFACE_RAW = REPO / "data" / "processed" / "ke_thumb_deepface_raw.csv"
OUT = REPO / "data" / "processed" / "ke_thumb_gemini_raw.csv"

BATCH_DIR = THUMB_DIR / "gemini_batch"
JSONL_DIR = BATCH_DIR / "jsonl"
CHUNK_INDEX = BATCH_DIR / "chunk_index.csv"
JOBS_CSV = BATCH_DIR / "jobs.csv"
HARVEST_ERRLOG = BATCH_DIR / "harvest_errors.csv"

MODEL = "models/gemini-2.5-flash"
CHUNK_SIZE = 4000   # ~2.5M tokens/chunk; submitted SEQUENTIALLY (one in flight) per do-file 78 lesson

# === INSTRUMENT (adapted from validated do-file 74; gender field re-pointed to the recurring
#     creator, structured-output + face fields kept verbatim) ======================================
PROMPT = (
    "You are coding a YouTube channel image (a video thumbnail or the channel avatar) for a study "
    "of who creates knowledge-economy content. Return ONLY the structured fields. "
    "For perceived_gender, report the perceived gender of the RECURRING CREATOR — the person who "
    "appears as the channel's host/creator across its images (the main human face in this image if "
    "it is that person). Report 'female' or 'male' for a clear human face, 'ambiguous' if a face is "
    "present but gender is unclear, and 'none' if there is no clear human face. Judge the depicted "
    "person, not text or logos. Be literal: if no person is shown, perceived_gender is 'none'."
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "face_present": {"type": "boolean"},
        "num_faces": {"type": "integer"},
        "perceived_gender": {"type": "string", "enum": ["female", "male", "ambiguous", "none"]},
        "is_recurring_creator": {"type": "boolean",
                                 "description": "true if the main face appears to be the channel's recurring host/creator (vs a guest, subject, or stock person)"},
    },
    "required": ["face_present", "perceived_gender"],
}

FIELDS = ["channel_id", "slot", "video_id", "face_present", "num_faces",
          "perceived_gender", "is_recurring_creator"]

logging.basicConfig(level=logging.INFO, format="[10] %(message)s")
log = logging.getLogger(__name__)


def nul_safe_dictreader(path: Path) -> csv.DictReader:
    with open(path, "rb") as f:
        raw = f.read().replace(b"\x00", b"")
    return csv.DictReader(io.StringIO(raw.decode("utf-8", errors="replace")))


def rest_schema(schema: dict) -> dict:
    """Uppercase JSON-schema type names for the REST/JSONL passthrough format (per do-file 78)."""
    out: dict = {}
    for k, v in schema.items():
        if k == "type" and isinstance(v, str):
            out[k] = v.upper()
        elif isinstance(v, dict):
            out[k] = rest_schema(v)
        elif isinstance(v, list):
            out[k] = [rest_schema(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


def get_client():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        sys.exit("[10] no GEMINI_API_KEY/GOOGLE_API_KEY in env. Parent agent gates this on the key "
                 "+ spend approval. `build` is free and needs no key; smoke/submit/run/status/harvest do.")
    try:
        from google import genai  # type: ignore
    except ImportError:
        sys.exit("[10] google-genai not installed. `pip install google-genai` in the Gemini venv first.")
    return genai.Client(api_key=key)


def img_path(channel_id: str, slot: str) -> Path:
    return IMG_DIR / channel_id.replace("/", "_") / f"{slot}.jpg"


def face_bearing_targets() -> List[dict]:
    """Face-bearing, ok-fetched images on disk: [{key, channel_id, slot, video_id, path}].

    Face-bearing = DeepFace (step 08) detected a face. These are the ONLY images worth the
    paid Gemini call for a creator-gender measure.
    """
    if not DEEPFACE_RAW.exists():
        sys.exit(f"[10] {DEEPFACE_RAW} missing — run step 08 (DeepFace) first.")
    targets: List[dict] = []
    for r in nul_safe_dictreader(DEEPFACE_RAW):
        if str(r.get("face_present")).lower() != "true":
            continue
        cid = r["channel_id"]
        slot = r.get("slot", "")
        p = img_path(cid, slot)
        if p.exists():
            key = f"{cid.replace('/', '_')}__{slot}"
            targets.append({"key": key, "channel_id": cid, "slot": slot,
                            "video_id": r.get("video_id", ""), "path": str(p)})
    return targets


def coded_keys() -> Set[str]:
    if OUT.exists():
        return {f"{r['channel_id'].replace('/', '_')}__{r.get('slot','')}"
                for r in nul_safe_dictreader(OUT)}
    return set()


def jobs_df_rows() -> List[dict]:
    if JOBS_CSV.exists():
        return list(nul_safe_dictreader(JOBS_CSV))
    return []


def write_jobs(rows: List[dict]) -> None:
    with open(JOBS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["chunk", "job_name", "state", "harvested"])
        w.writeheader()
        for r in rows:
            w.writerow(r)


def append_job(row: dict) -> None:
    write_header = not JOBS_CSV.exists()
    with open(JOBS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["chunk", "job_name", "state", "harvested"])
        if write_header:
            w.writeheader()
        w.writerow(row)


# ---- FREE step: build JSONL chunks of face-bearing images -------------------------------------
def cmd_build() -> None:
    rschema = rest_schema(RESPONSE_SCHEMA)
    JSONL_DIR.mkdir(parents=True, exist_ok=True)

    already = coded_keys()
    indexed: Set[str] = set()
    if CHUNK_INDEX.exists():
        indexed = {r["key"] for r in nul_safe_dictreader(CHUNK_INDEX)}

    targets = face_bearing_targets()
    todo = [t for t in targets if t["key"] not in already and t["key"] not in indexed]
    log.info("face-bearing images on disk: %s | already coded: %s | already chunked: %s | to pack: %s",
             f"{len(targets):,}", f"{len(already):,}", f"{len(indexed):,}", f"{len(todo):,}")
    if not todo:
        log.info("nothing to pack.")
        return

    existing_chunks = len(list(JSONL_DIR.glob("chunk_*.jsonl")))
    index_rows: List[dict] = []
    for start in range(0, len(todo), CHUNK_SIZE):
        part = todo[start:start + CHUNK_SIZE]
        cid = existing_chunks + start // CHUNK_SIZE + 1
        cpath = JSONL_DIR / f"chunk_{cid:04d}.jsonl"
        with cpath.open("w", encoding="utf-8") as f:
            for t in part:
                b64 = base64.b64encode(Path(t["path"]).read_bytes()).decode("ascii")
                req = {"key": t["key"], "request": {
                    "contents": [{"parts": [
                        {"text": PROMPT},
                        {"inlineData": {"mimeType": "image/jpeg", "data": b64}},
                    ]}],
                    "generationConfig": {"responseMimeType": "application/json",
                                         "responseSchema": rschema, "temperature": 0}}}
                f.write(json.dumps(req) + "\n")
        index_rows += [{"key": t["key"], "channel_id": t["channel_id"], "slot": t["slot"],
                        "video_id": t["video_id"], "chunk": cpath.name} for t in part]
        log.info("wrote %s: %s requests (%.0f MB)", cpath.name, f"{len(part):,}",
                 cpath.stat().st_size / 1e6)
    write_header = not CHUNK_INDEX.exists()
    with open(CHUNK_INDEX, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "channel_id", "slot", "video_id", "chunk"])
        if write_header:
            w.writeheader()
        for r in index_rows:
            w.writerow(r)
    log.info("chunk index updated -> %s", CHUNK_INDEX)
    log.info("BUILD complete (FREE). Next PAID step: smoke, then run. Requires GEMINI_API_KEY.")


def upload_jsonl(client, path: Path):
    from google.genai import types  # type: ignore
    last_err = None
    for mt in ("application/jsonl", "jsonl", "text/plain"):
        try:
            return client.files.upload(
                file=str(path), config=types.UploadFileConfig(display_name=path.stem, mime_type=mt))
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise RuntimeError(f"upload failed for {path.name}: {last_err}")


def submit_one(client, chunk: Path, max_429_retries: int = 10) -> str:
    from google.genai import errors as genai_errors  # type: ignore
    up = upload_jsonl(client, chunk)
    for attempt in range(max_429_retries + 1):
        try:
            job = client.batches.create(model=MODEL, src=up.name,
                                        config={"display_name": f"ke-thumb-{chunk.stem}"})
            log.info("%s -> job %s state=%s", chunk.name, job.name, job.state)
            append_job({"chunk": chunk.name, "job_name": job.name,
                        "state": str(job.state), "harvested": "0"})
            return job.name
        except genai_errors.ClientError as exc:
            if getattr(exc, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(exc):
                wait = 600
                log.info("quota 429 on create (%s); waiting %d min (attempt %d/%d)...",
                         chunk.name, wait // 60, attempt + 1, max_429_retries)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"[10] {chunk.name}: still quota-blocked after {max_429_retries} retries.")


def poll_until_done(client, job_name: str, timeout_h: float = 8.0) -> str:
    t0 = time.time()
    while time.time() - t0 < timeout_h * 3600:
        job = client.batches.get(name=job_name)
        state = str(job.state)
        if any(s in state for s in ("SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED")):
            return state
        time.sleep(60)
    return "TIMEOUT"


def parse_response_line(line: str) -> Tuple[str, dict | None, str]:
    obj = json.loads(line)
    key = obj.get("key", "")
    resp = obj.get("response")
    if not resp:
        return key, None, str(obj.get("error", "no_response"))[:200]
    try:
        text = resp["candidates"][0]["content"]["parts"][0]["text"]
        return key, json.loads(text), ""
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        return key, None, f"parse:{exc}"[:200]


def _key_maps() -> Tuple[Dict[str, Tuple[str, str]], Dict[str, str]]:
    """key -> (channel_id, slot) and key -> video_id, from the chunk index."""
    cid_slot: Dict[str, Tuple[str, str]] = {}
    vid: Dict[str, str] = {}
    if CHUNK_INDEX.exists():
        for r in nul_safe_dictreader(CHUNK_INDEX):
            cid_slot[r["key"]] = (r["channel_id"], r["slot"])
            vid[r["key"]] = r.get("video_id", "")
    return cid_slot, vid


def cmd_harvest() -> None:
    client = get_client()
    rows = jobs_df_rows()
    pending = [r for r in rows if r.get("harvested") != "1"]
    if not pending:
        log.info("nothing to harvest.")
        return
    cid_slot, vid_by_key = _key_maps()
    write_header = not OUT.exists()
    for r in pending:
        job = client.batches.get(name=r["job_name"])
        state = str(job.state)
        if "SUCCEEDED" not in state:
            log.info("%s: %s — skip.", r["chunk"], state)
            continue
        data = client.files.download(file=job.dest.file_name).decode("utf-8")
        out_rows, err_rows = [], []
        for line in data.splitlines():
            if not line.strip():
                continue
            key, feat, err = parse_response_line(line)
            cid, slot = cid_slot.get(key, (key.split("__")[0], key.split("__")[-1]))
            if feat is None:
                err_rows.append({"key": key, "error": err})
                continue
            row = {"channel_id": cid, "slot": slot, "video_id": vid_by_key.get(key, "")}
            row.update({k: feat.get(k) for k in FIELDS if k not in row})
            out_rows.append(row)
        if out_rows:
            with open(OUT, "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS)
                if write_header:
                    w.writeheader()
                    write_header = False
                for row in out_rows:
                    w.writerow(row)
        if err_rows:
            eh = not HARVEST_ERRLOG.exists()
            with open(HARVEST_ERRLOG, "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["key", "error"])
                if eh:
                    w.writeheader()
                for row in err_rows:
                    w.writerow(row)
        r["harvested"] = "1"
        r["state"] = state
        log.info("harvested %s: ok=%s err=%s", r["chunk"], f"{len(out_rows):,}", f"{len(err_rows):,}")
    write_jobs(rows)
    log.info("gemini gender -> %s", OUT)


def cmd_run() -> None:
    """Sequential pipeline: one job in flight at a time (quota-tier safe). Resumable."""
    client = get_client()
    chunks = sorted(JSONL_DIR.glob("chunk_*.jsonl"))
    if not chunks:
        sys.exit("[10] no chunks on disk — run `build` first.")
    rows = jobs_df_rows()
    by_chunk = {r["chunk"]: r for r in rows}
    n_done = 0
    for c in chunks:
        r = by_chunk.get(c.name)
        if r and r.get("harvested") == "1":
            continue
        if r and "SUCCEEDED" in str(r.get("state", "")):
            cmd_harvest()
            continue
        job_name = r["job_name"] if r else submit_one(client, c)
        state = poll_until_done(client, job_name)
        rows = jobs_df_rows()
        for rr in rows:
            if rr["job_name"] == job_name:
                rr["state"] = state
        write_jobs(rows)
        if "SUCCEEDED" not in state:
            log.info("%s: terminal state %s — stopping for inspection.", c.name, state)
            return
        cmd_harvest()
        by_chunk = {x["chunk"]: x for x in jobs_df_rows()}
        n_done += 1
        log.info("sequential progress: %d chunk(s) completed this run.", n_done)
    log.info("ALL CHUNKS COMPLETE.")


def cmd_status() -> None:
    client = get_client()
    rows = jobs_df_rows()
    if not rows:
        log.info("no jobs submitted yet.")
        return
    for r in rows:
        job = client.batches.get(name=r["job_name"])
        log.info("%s  %s  %s  harvested=%s", r["chunk"], r["job_name"], job.state, r.get("harvested"))


def cmd_smoke() -> None:
    """3-image end-to-end batch validation (~cents)."""
    rschema = rest_schema(RESPONSE_SCHEMA)
    client = get_client()
    targets = face_bearing_targets()[:3]
    if not targets:
        sys.exit("[10] no face-bearing images available for smoke test (run step 08 first).")
    JSONL_DIR.mkdir(parents=True, exist_ok=True)
    spath = JSONL_DIR / "smoke.jsonl"
    with spath.open("w", encoding="utf-8") as f:
        for t in targets:
            b64 = base64.b64encode(Path(t["path"]).read_bytes()).decode("ascii")
            f.write(json.dumps({"key": t["key"], "request": {
                "contents": [{"parts": [{"text": PROMPT},
                                        {"inlineData": {"mimeType": "image/jpeg", "data": b64}}]}],
                "generationConfig": {"responseMimeType": "application/json",
                                     "responseSchema": rschema, "temperature": 0}}}) + "\n")
    up = upload_jsonl(client, spath)
    job = client.batches.create(model=MODEL, src=up.name, config={"display_name": "ke-thumb-smoke"})
    log.info("smoke job %s submitted; polling...", job.name)
    for _ in range(120):
        time.sleep(15)
        job = client.batches.get(name=job.name)
        if any(s in str(job.state) for s in ("SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED")):
            break
        log.info("   ...%s", job.state)
    log.info("smoke final state: %s", job.state)
    if "SUCCEEDED" in str(job.state):
        data = client.files.download(file=job.dest.file_name).decode("utf-8")
        for line in data.splitlines()[:3]:
            key, feat, err = parse_response_line(line)
            log.info("%s: %s", key, json.dumps(feat) if feat else err)
        log.info("SMOKE PASSED — safe to run the full build+run.")
    else:
        log.info("SMOKE FAILED — inspect job.error before running the full pass.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Gemini BATCH creator-gender over KE face-bearing thumbnails.")
    ap.add_argument("cmd", choices=["build", "smoke", "run", "submit", "status", "harvest"])
    args = ap.parse_args()
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    {"build": cmd_build, "smoke": cmd_smoke, "run": cmd_run,
     "submit": lambda: cmd_run(), "status": cmd_status, "harvest": cmd_harvest}[args.cmd]()


if __name__ == "__main__":
    main()
