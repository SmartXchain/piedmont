# Changelog

All significant changes to this project are recorded here.
Format: `[YYYY-MM-DD] Category: Description`

Categories: `Added`, `Changed`, `Fixed`, `Removed`, `Security`, `Migration`

---

## Unreleased

No changes pending. See `TASK.md` for the full task history.

---

## 2026-03-11

- Added: Tests for kanban stock level and expiry logic — `ChemicalLot.status` (all 4 states), `Product.total_quantity`, `Product.needs_reorder`, dashboard bucket placement at/above/below trigger level (T-5, 19 tests in `kanban/tests.py`)
- Added: Auth redirect tests for every named URL in the project — 44 no-arg views and 37 detail views each verified to return HTTP 302 → `/login/` for unauthenticated requests (T-6, `app/test_login.py`)

---

## 2026-03-10

- Security: Moved `SECRET_KEY` out of source into environment variable; added test to verify env var loading (S-1)
- Security: Fixed `DEBUG` env var always evaluating truthy — `os.environ.get("DEBUG")` returns a string; replaced with explicit `== "True"` comparison (S-2)
- Security: Added `LoginRequiredMiddleware` (Django 5.1+) to protect all views globally; added custom login page with AC 120-78B compliance notice; added logout route and username display in navbar (S-3)
- Security: Removed `@csrf_exempt` from `AddDelayView` and `UpdateStatusView` in scheduler; added `X-CSRFToken` header to both `fetch()` calls in `main.html` (S-4)
- Fixed: Corrected `PartStandard` unique constraint condition — `isnull=True` → `isnull=False` on the classification-scoped uniqueness check; new migration generated (B-1)
- Fixed: Eliminated N+1 queries in `rack_list` and `pm_calendar` — replaced per-loop `RackPM` queries with `Prefetch('rackpm_set', to_attr='prefetched_pms')` (B-2)
- Fixed: Eliminated N+1 queries in `kanban_dashboard` and `product_list` — added `prefetch_related('chemical_lots')`; fixed `get_current_stock()` → `total_quantity`; added `is_expiring_soon()` to `ChemicalLot` (B-3)
- Changed: Replaced all `print()` statements with `logging` module (Q-1)
- Changed: Replaced all `Model.objects.get()` calls in views with `get_object_or_404()` (Q-2)
- Fixed: Media file URL construction in masking view — used `.url` property instead of raw `MEDIA_ROOT` path (Q-3)
- Changed: `StandardProcess` FK `on_delete` changed from `CASCADE` to `PROTECT` to prevent silent cascade-deletion of active processes; migration generated (Q-4)
- Removed: Unused signal imports in `process/models.py` (Q-5)
- Changed: Replaced emoji characters in `Standard.__str__` to avoid encoding issues in logs and exports (Q-6)
- Fixed: Renamed `CheckConstraint.check=` to `CheckConstraint.condition=` in `process/models.py` to resolve Django deprecation warning before 6.0 removal (Q-7)
- Added: Tests for `part`/`process` — `WorkOrder.get_process_steps()`, `clean()`, `_calc_amps()` (T-1)
- Added: Tests for `standard` — revision change sets `requires_process_review` (T-2)
- Added: Tests for `methods` — auto-creation of `ParameterToBeRecorded` from template (T-3)
- Added: Tests for `fixtures` PM due-date logic — overdue/upcoming/neither classification, frequency override, multi-task racks, stats counts; N+1 regression tests for `rack_list` and `pm_calendar` (T-4, 14 tests in `fixtures/tests.py`)
- Added: `.env.dev`, `.env.prod`, `.env.prod.db` excluded from git tracking

---

## 2025-03-10

- Added: `ndt` app — non-destructive testing records
- Added: `drawings` app — drawing management with login protection
- Added: `scheduler` app — production scheduling
- Fixed: Process search and display logic
- Fixed: Method display issues
- Fixed: Links in navigation

---

## Prior History

Full git history available via `git log`. Significant milestones:

- Initial production deployment with core apps: `standard`, `methods`, `process`, `part`, `masking`, `kanban`, `fixtures`, `tanks`, `logbook`, `pm`, `sds`, `periodic_testing`, `tank_controls`, `customer_links`, `landing_page`
