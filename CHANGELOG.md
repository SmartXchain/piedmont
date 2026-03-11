# Changelog

All significant changes to this project are recorded here.
Format: `[YYYY-MM-DD] Category: Description`

Categories: `Added`, `Changed`, `Fixed`, `Removed`, `Security`, `Migration`

---

## Unreleased

### Landing Page (in progress — see TASK.md LP-1 through LP-6)

- LP-1 `[x]` Apply TAT color scheme to `index.html`
- LP-2 `[x]` Replace Capability accordion with live Process/Standard/Classification table; remove search, expand-all, CSV
- LP-3 `[x]` Fix N+1 in `export_capabilities_csv`
- LP-4 `[x]` Fix N+1 in `capability_pricing_detail`
- LP-5 `[x]` Remove dead `customer_pricing_view`
- LP-6 `[x]` Write tests

---

## 2026-03-11 (continued)

- Fixed: E402 module-level imports not at top in `periodic_testing/views.py` — moved `logger` assignment below all imports and sorted import blocks (F8-4)
- Fixed: E402 module-level imports not at top in `masking/views.py` — moved `logger` assignment below all imports and sorted import blocks (F8-3)
- Fixed: E303 extra blank line between functions in `landing_page/views.py:48` (F8-2)
- Fixed: F841 unused variable `p` in `kanban/tests.py:348` — dropped assignment, record creation is sufficient (F8-1)

---

## 2026-03-11 (continued)

- Added: Tests for `landing_page` — 18 tests in 3 classes covering home page status/context/classification labels, `capability_pricing_detail` 200/404/context, `export_capabilities_csv` content-type/headers/data; all auth redirects verified (LP-6)
- Fixed: Completed truncated `pricing_detail.html` template — file was cut off mid-tag causing `TemplateSyntaxError` on the pricing detail view (LP-6 side fix)

---

## 2026-03-11

- Fixed: Footer brand updated from "Piedmont Aviation" to "Greensboro Site" (U-6)
- Changed: Removed all dropdown dividers from navbar (U-5)
- Changed: Admin link moved from right-side rail into Maintenance dropdown; staff-only; right rail now shows username + logout only (U-4)
- Fixed: Removed duplicate Bootstrap JS `<script>` from `pm_landing.html` — was breaking all navbar dropdowns on the PM Tasks page (U-3)
- Fixed: Removed hardcoded Admin link from `ndt/index.html` page footer — was styled as plain text, causing confusion with the navbar Admin entry (U-3)
- Changed: Navbar brand updated — "Piedmont Aviation" replaced with TAT Technologies SVG logo + "Greensboro Site"; Admin link consolidated to one entry, staff-only; Schedule moved into Operations, Inventory into Maintenance, Drawings into Quality (U-2)
- Changed: Applied TAT Technologies color scheme to shared templates (`base.html`, `navbar.html`, `footer.html`) — dark navy `#2E313F` background, `#0066cc` blue accent, CSS custom properties for single-source color management (U-1)
- Changed: Restructured navbar from 13 flat links into logical dropdown groups (Operations, Quality, Maintenance); navbar is now `sticky-top` and never autohides (U-1)
- Changed: Footer updated to three-column responsive layout; copyright updated to TAT Technologies (U-1)
- Changed: Added `{% block extra_css %}` and `{% block extra_js %}` extension points to `base.html` for per-page assets (U-1)
- Changed: `PLAN.md` renamed from remediation plan to living implementation plan; workflow rule added to `CLAUDE.md` requiring plan and task entries before writing code
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
