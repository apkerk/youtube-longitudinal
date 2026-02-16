# Data Collection Rules

## Test Before Production

Every collection script supports `--test` and `--limit` flags. Before any production run:

1. Run with `--test --limit 5` to verify the script works
2. Check the output CSV has the expected 35 columns
3. Run `python -m src.validation.validate_sweep` on the output
4. Only then request Katie's approval for a full run

## Quota Awareness

- Daily quota: ~1,010,000 units (Researcher Program)
- Before any large run, calculate expected cost:
  - Search API: 100 units per call
  - Channels.list: 1 unit per call (50 channels per call)
  - Videos.list: 1 unit per call
- Log quota consumed after every run in PROGRESS_LOG.md

## Checkpoint/Resume

All collection scripts use checkpoint files. If a run is interrupted:
- Check the output CSV for the last successfully written row
- Resume from where it left off (scripts handle this via existing channel dedup)
- Never start from scratch if partial data exists

## Data Validation

After every collection run, verify:
1. No duplicate channel_ids within the output
2. All required columns present (check against schema in `src/config.py`)
3. Dates make sense (channel `published_at` >= cohort cutoff `2026-01-01`)
4. No anomalous values (negative counts, null channel_ids)

## File Naming

Collection outputs follow: `{stream_dir}/{descriptor}_{YYYYMMDD}.csv`
Example: `data/channels/stream_a/initial_20260202.csv`
