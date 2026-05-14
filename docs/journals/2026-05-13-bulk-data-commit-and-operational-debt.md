# Bulk Data Commit: 46 Export Files and the Growing Operational Debt

**Date**: 2026-05-13 10:00
**Severity**: Low
**Component**: git repository, data/ directory
**Status**: Resolved (committed)

## What Happened

On May 13, committed and pushed a large batch: 46 order export JSON files (covering April 2 - May 12, 2026) plus 767 config/hook/agent files from the Claude Code stack. The data commit (`c883b48`) added daily order exports in the naming pattern `odoo-orders-{date}-{methods}.json`. The config commit (`6d5a272`) updated the entire `.claude/` directory tree.

The data files contain complete POS order payloads from Odoo: order numbers, amounts, payment methods, product details, customer names. All stored in plaintext JSON in the git repository.

## The Brutal Truth

Let us be honest about what just happened: we committed 46 files of production financial data to a git repository. Every order number, every amount, every payment method for 30+ days of business operations is now in git history. Even if we delete the files tomorrow, the history remains. The order data itself is not deeply sensitive (no credit card numbers, no PII beyond customer names from Odoo), but it is still production financial data sitting in a dev repo.

The 767-file config commit is a different kind of mess. That is the entire Claude Code hook/skill/agent system being versioned alongside the actual project code. It works, but the signal-to-noise ratio in `git log` is now terrible.

## Technical Details

**Commit `c883b48`:** `chore(data): add daily order exports Apr-May 2026`
- 46 JSON files, each containing 4-55 orders
- Naming: `odoo-orders-2026-04-08-card-vnpay-vnpayqr.json`
- Each file: `{"query_date": "...", "total_orders": N, "orders": [...]}`

**Commit `6d5a272`:** `chore: update claude/opencode configs, hooks, skills and agents`
- 767 files across `.claude/` directory
- Hooks, agents, skills, tests, configs

**Git log now shows:**
```
6d5a272 chore: update claude/opencode configs, hooks, skills and agents
c883b48 chore(data): add daily order exports Apr-May 2026
ba7e653 chore(data): add order exports and weekly sales report
6361336 feat(b4b): add invoice generation and sale order updates
```

## What We Tried

We committed what we had. The data files are useful for debugging and auditing -- having historical order exports in git means we can re-import or verify past syncs without re-querying Odoo. The config files were due for a commit after weeks of incremental changes.

## Root Cause Analysis

No `.gitignore` rules for the export files. The `odoo-orders-*.json` files were generated in the project root alongside the code. Over 30 days they accumulated, and eventually they all got committed together. The proper approach would have been either: (a) `.gitignore` the export files and store them in a separate data store, or (b) commit them daily as part of the sync process.

## Lessons Learned

1. Decide upfront whether generated data files belong in git or not. If yes, commit them daily. If no, add them to `.gitignore` immediately.
2. Production financial data in git is a compliance question, not just a developer convenience question. Consider what auditors or regulators would think.
3. Config/tooling files (`.claude/`) should probably be in a separate repo or at least a consistent commit schedule. A 767-file mega-commit is a code review nightmare.
4. The export files ARE useful for audit trail purposes. A dedicated `data/` directory with a retention policy would be cleaner than dumping in the project root.

## Next Steps

- Move future exports to `data/exports/` directory with `.gitkeep`
- Add `odoo-orders-*.json` to `.gitignore` (keep existing committed files for audit trail)
- Consider encrypting or sanitizing order data before committing if compliance requires it
- Set up daily auto-commit of export files if they are deemed necessary in git
- Separate `.claude/` config updates into their own branch or repo
