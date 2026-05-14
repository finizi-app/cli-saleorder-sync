# The `.env` Loading Footgun: Why Every Sync Requires Manual Sourcing

**Date**: 2026-04-13 09:00
**Severity**: Medium
**Component**: sync-odoo-to-b4b.py, sync-daily.sh
**Status**: Unresolved

## What Happened

Every single time the daily sync runs, the operator must manually run `set -a && source .env && set +a` before executing `python3 sync-odoo-to-b4b.py`. Neither the Python script nor the shell wrapper auto-loads the `.env` file. If you forget, the script crashes immediately with "URL required: --url or B4B_API_URL env var" or similar credential errors.

This has been the case since the first day of operations. It is not a bug -- it is a missing feature that was never added because the initial implementation used explicit CLI args or assumed env vars were already set in the shell profile.

## The Brutal Truth

This is embarrassing. The project has `requirements.txt` but does not include `python-dotenv`. The `.env` file exists with all credentials. The `sync-daily.sh` wrapper runs the Python script directly without sourcing `.env`. The README documents environment variables but never mentions you need to manually source them. Every new developer (or the same developer at 7am before coffee) will hit this wall.

The frustrating part is that adding auto-loading is a 3-line change: `from dotenv import load_dotenv; load_dotenv()`. But here we are, 30 days into production usage, still typing `set -a && source .env && set +a` every morning like it is some kind of ritual incantation.

## Technical Details

**What fails without env vars:**
```bash
$ python3 sync-odoo-to-b4b.py --date 2026-04-20
# Error: URL required: --url or B4B_API_URL env var
```

**The required incantation:**
```bash
set -a && source .env && set +a
python3 sync-odoo-to-b4b.py --date 2026-04-20
```

**Files affected:**
- `sync-odoo-to-b4b.py` -- Python script, needs `python-dotenv`
- `sync-daily.sh` -- Shell wrapper, could source `.env` directly
- `src/b4b_import_cli.py` -- Reads env vars via `os.environ.get()`
- `src/cli.py` -- Reads Odoo env vars via `os.environ.get()`

**Current dependency:** `python-dotenv` is NOT in `requirements.txt`.

## What We Tried

Nothing. We just accepted the manual sourcing as "how it works." The `sync-daily.sh` script even has a comment saying "Quick daily sync script" but does not actually make it quick -- you still need the manual env step.

## Root Cause Analysis

The scripts were built with `--url`, `--token`, `--entity-id` CLI arguments as the primary interface. Environment variables were added as a convenience. But the daily operational flow uses env vars exclusively. Nobody went back and added `python-dotenv` because "it works if you source the file." This is the classic gap between "works for the original developer" and "works reliably for daily operations."

## Lessons Learned

1. Any script that reads credentials from environment variables MUST auto-load `.env` if the file exists. No exceptions.
2. Shell wrappers should source their own `.env` -- do not assume the parent shell has done it.
3. If the daily run requires more than one command, it is not "quick" or "daily-ready."
4. The moment you find yourself typing the same 3 commands every day, automate it.

## Next Steps

- Add `python-dotenv` to `requirements.txt`
- Add `load_dotenv()` to `sync-odoo-to-b4b.py` at module level (before any `os.environ.get()` calls)
- Add `source "$(dirname "$0")/.env"` to `sync-daily.sh` before the Python call
- Document the change so future scripts inherit this pattern
