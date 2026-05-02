# Inventory list query profiling

This document describes how to capture PostgreSQL query plans for the **My items**
and **Previously held** pages, which are built by:

- `inventory.models.build_my_items_page_data`
- `inventory.models.build_previous_items_page_data`

## When to use this

- After changing correlated subqueries, `select_related`, or indexes on
  `inventory_operation` / `inventory_pendingtransfer`.
- When investigating slow list pages in production-like data volumes.

## How to run

1. Point Django at PostgreSQL (see `env.example` and `README.md`).
2. Apply migrations (`python src/manage.py migrate`).
3. Run:

```sh
PYTHONPATH=src SECRET_KEY=unsafe-secret-key-for-tooling \
  uv run python src/manage.py profile_inventory_list_queries
```

Optional: scope to a specific responsible profile:

```sh
uv run python src/manage.py profile_inventory_list_queries --responsible-id 42
```

## What to look for in the output

- **Sequential scans** on `inventory_operation` with large row counts often
  benefit from the existing partial “latest per item” index and the composite
  index `inventory_op_resp_item_idx` on
  `(responsible_id, item_id, created_at DESC, id DESC)`, which supports filters
  and subqueries that key operations by responsible then walk the latest rows
  per item.
- Plans vary with **table statistics**; re-run `ANALYZE` on the inventory tables
  after bulk loads before drawing conclusions.

## Captured notes (maintenance)

Re-run the command after schema or queryset changes and attach the relevant plan
snippets to the change request when the diff touches list performance.
