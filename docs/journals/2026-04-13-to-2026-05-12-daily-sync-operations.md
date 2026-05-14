# Daily Sync Operations: 30 Days of Odoo-to-B4B Order Sync

**Date**: 2026-05-12 18:00
**Severity**: Medium
**Component**: sync-odoo-to-b4b.py, sync-daily.sh
**Status**: Ongoing

## What Happened

Ran daily sync operations every day from April 13 through May 12, 2026. Each day involved exporting POS orders from Odoo (payment methods: Card, VNPay, VNPayQR), importing them to B4B, and generating POS invoices (auto-released, auto-signed, auto-tax-sent). Total: ~700 orders across 30 days, roughly 20-55M VND cumulative.

## The Brutal Truth

Running a daily manual sync for 30 consecutive days is a chore that should be automated via cron or Odoo webhook. Every single day requires: (1) load env vars manually because the script does not auto-source `.env`, (2) run the sync command, (3) eyeball the output for duplicate errors, (4) verify invoice generation. This is exactly the kind of repetitive task that breeds complacency and leads to missed days or silent failures.

The volume pattern is predictable: weekdays 30-55 orders (1.5-3M VND), weekends 4-10 orders (200K-800K VND). April 30 (Reunification Day holiday) had only 7 orders. This predictability means we could batch weekend orders into a Monday sync with zero business impact.

## Technical Details

**Daily command pattern:**
```bash
set -a && source .env && set +a
python3 sync-odoo-to-b4b.py --date 2026-04-XX --payment-methods Card VNPay VNPayQR
```

**Volume data (sample):**
- Apr 21 (Mon): 52 orders, 2.82M VND
- Apr 22 (Tue): 55 orders, 3.017M VND
- Apr 26 (Sat): 9 orders, 1.218M VND
- Apr 27 (Sun): 4 orders, 216K VND
- May 7 (Thu): 53 orders, 2.382M VND
- May 10 (Sun): 4 orders, 285K VND

**Invoice flow:** All invoices generated successfully with `auto_release=True`, `auto_sign=True`, `auto_send_tax=True` via `B4BClient.generate_vnpay_invoice()`. Zero invoice failures across 30 days.

**Exit code problem:** Script exits with code 1 when ANY order fails, even if 39 out of 40 succeeded. This makes it impossible to distinguish "total failure" from "mostly fine, 1 duplicate." The `b4b_import_cli.py` line 280: `return 0 if error_count == 0 else 2` is the culprit.

## Root Cause Analysis

The sync is manual because the original implementation focused on getting it working, not making it operational. No cron job, no Odoo webhook callback, no `.env` auto-loading. The script was built as a one-off utility that became a daily ritual.

## Lessons Learned

1. Scripts destined for daily use should auto-load `.env` from day one. Adding `python-dotenv` is 2 lines of code.
2. Exit codes should differentiate between "total failure" and "partial success with known issues." A few duplicate orders should not make the whole sync appear failed.
3. Weekend volumes are 10-20% of weekday volumes. Batch weekend syncs into Monday to reduce operational overhead by 28% (2 out of 7 days).
4. The invoice pipeline (auto-release, auto-sign, auto-tax-sent) is rock-solid. Zero failures in 30 days. This is the one part we do not need to worry about.

## Next Steps

- Add `python-dotenv` auto-loading to `sync-odoo-to-b4b.py` and `sync-daily.sh`
- Implement partial-success exit code (e.g., exit 0 for <5% failures, exit 2 for >5%)
- Set up cron job for weekday automatic sync at 23:00 ICT
- Consider skipping Saturday/Sunday syncs and batching into Monday
