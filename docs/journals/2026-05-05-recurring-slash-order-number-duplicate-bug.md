# Recurring Duplicate Error on '/' Order Numbers from Odoo

**Date**: 2026-05-05 19:00
**Severity**: High
**Component**: order_mapper.py, b4b_import_cli.py
**Status**: Unresolved

## What Happened

On multiple days, the B4B import fails on 1-2 orders per day with duplicate order_number errors. The pattern: Odoo returns POS orders where `order["name"]` is just `/` (a single forward slash). When mapped to B4B format via `order_mapper.py` line 105 (`"order_number": odoo_order.get("name", "")`), these collide because multiple unrelated orders all get `order_number = "/"`.

Observed on: Apr 20 (2 duplicates), May 5 (1 duplicate), May 8 (1 duplicate). Each time, these `/` orders cause `httpx.HTTPStatusError` from B4B API with a duplicate key violation.

## The Brutal Truth

This is infuriating because it is 100% a data quality issue in Odoo that we have zero control over. Someone at the POS is creating orders without proper numbering, and Odoo assigns `/` as the default. We cannot fix the source data. We cannot change B4B's unique constraint. We are stuck in the middle, and the current code just lets it blow up and reports the whole sync as "failed" even though 97% of orders imported fine.

What makes it worse: the `pos_reference` field on these orders usually has a proper unique value (e.g., `Order 00042-001-0001`), but we use `name` as `order_number` and ignore `pos_reference` for the primary key. The reference number is right there, unused.

## Technical Details

**The mapping in `order_mapper.py:105`:**
```python
"order_number": odoo_order.get("name", ""),
```

**The B4B API error:** HTTP 409 or 422 with body containing "duplicate" or "already exists" when posting a second order with `order_number = "/"`.

**Impact on exit code:** `b4b_import_cli.py:280`:
```python
return 0 if error_count == 0 else 2
```
Even 1 duplicate out of 40 orders causes exit code 2, which bubbles up to `sync-odoo-to-b4b.py` as "Sync failed."

**Actual failure rates:**
- Apr 20: 2/41 orders = 4.9% failure
- May 5: 1/37 orders = 2.7% failure
- May 8: 1/39 orders = 2.6% failure

## What We Tried

Nothing yet. We have just been accepting the failures and manually verifying that the other orders went through. This is a ticking time bomb -- eventually someone will miss a day because they see "failed" and assume nothing imported.

## Root Cause Analysis

Two problems compound each other:

1. **Data quality in Odoo:** POS orders created without proper session/context get `name = "/"` as a placeholder. This is an Odoo behavior when orders are manually created or imported without a sequence.

2. **Order key choice:** Using `odoo_order["name"]` as the B4B `order_number` is fragile. The `pos_reference` field is more reliable and usually unique per order.

## Lessons Learned

1. Never trust external system identifiers to be unique. Always have a fallback or composite key strategy.
2. When integrating two systems, the first thing to validate is what constitutes a unique identifier in each system.
3. Partial failures should be reported as partial, not as total. The all-or-nothing exit code is misleading.
4. The `pos_reference` field is the actual unique POS order reference in Odoo. The `name` field is the internal Odoo sequence that can be `/` for manually created records.

## Next Steps

- **Fallback strategy in `order_mapper.py`:** When `name` is `/` or empty, use `pos_reference` as `order_number`. If both are empty, generate a composite key like `odoo-{order_id}-{date}`.
- **Deduplication before import:** Pre-filter orders in `sync-odoo-to-b4b.py` to catch `/` order numbers and either skip or re-key them before sending to B4B.
- **Fix exit code semantics:** Return exit 0 when success_rate > 95%, exit 1 only for total failures.
- **Owner:** Whoever implements the next sync cycle (next sprint).
