#!/bin/bash
# run_full_phaseAB.sh — KE thumbnail-gender full Phase A (fetch) + Phase B (DeepFace + aggregate).
# Launched via nohup (survives SSH disconnect; screen dies on Mac Mini network drops).
# Each step is resumable; if interrupted, re-running this script picks up where it left off.
set -u
cd /Users/katieapker/.youtube-longitudinal/repo/src/paper_gendering_ai || exit 1

echo "=========================================="
echo "KE THUMBNAIL-GENDER PHASE A+B — full run"
echo "started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=========================================="

echo ""
echo ">>> PHASE A: fetch 391,052 images (free, resumable, 10 workers)"
python3 07_thumb_fetch_images.py --workers 10
rc=$?
echo ">>> fetch exit code: $rc"

echo ""
echo ">>> PHASE B-1: DeepFace gender (free, resumable, 6 workers)"
python3 08_thumb_deepface_gender.py --workers 6
rc=$?
echo ">>> deepface exit code: $rc"

echo ""
echo ">>> PHASE B-2: aggregate per-image -> per-channel (canonical channel file)"
python3 09_thumb_aggregate_channel.py
rc=$?
echo ">>> aggregate exit code: $rc"

echo ""
echo "=========================================="
echo "PHASE A+B COMPLETE"
echo "finished: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "outputs:"
echo "  data/processed/ke_thumb_deepface_raw.csv     (per-image)"
echo "  data/processed/ke_thumb_gender_channel.csv   (per-channel)"
echo "=========================================="
