# Task Tracker

Active work items for the Piedmont project.
See `plan.md` for detailed implementation steps for each item.

Status: `[ ]` Todo · `[~]` In Progress · `[x]` Done

---

## Security (do first — production risk)

| # | Status | Task | Plan ref | Notes |
|---|---|---|---|---|
| S-1 | `[x]` | Move `SECRET_KEY` to environment variable | PLAN.md §1 | |
| S-2 | `[x]` | Fix `DEBUG` env var — always evaluates truthy | PLAN.md §2 | `os.environ.get("DEBUG")` returns string, not bool |
| S-3 | `[x]` | Add `@login_required` to all unprotected views | PLAN.md §3 | Implemented via `LoginRequiredMiddleware` (Django 5.1+) |
| S-4 | `[x]` | Remove `@csrf_exempt` from scheduler write views | PLAN.md §4 | `AddDelayView`, `UpdateStatusView`; update JS to send CSRF token |

---

## Bugs (data integrity risk)

| # | Status | Task | Plan ref | Notes |
|---|---|---|---|---|
| B-1 | `[x]` | Fix contradictory `PartStandard` unique constraints | plan.md §5 | Requires new migration — test carefully in dev first |
| B-2 | `[x]` | Fix N+1 queries in fixtures view | plan.md §6a | `prefetch_related` on rack queryset |
| B-3 | `[x]` | Fix N+1 queries in kanban view | plan.md §6b | `prefetch_related('chemical_lots')` |

---

## Code Quality

| # | Status | Task | Plan ref | Notes |
|---|---|---|---|---|
| Q-1 | `[x]` | Replace all `print()` with `logging` | plan.md §7 | 3+ files affected |
| Q-2 | `[x]` | Replace `.get()` with `get_object_or_404()` | plan.md §8 | Audit all views |
| Q-3 | `[x]` | Fix media file URL in masking view | plan.md §9 | `MEDIA_ROOT` used where `.url` is needed |
| Q-4 | `[x]` | Change `StandardProcess` FK to `PROTECT` | plan.md §10 | Prevents silent cascade-delete of active processes; requires migration |
| Q-5 | `[x]` | Remove unused signal imports in `process/models.py` | plan.md §11 | 2-line change |
| Q-6 | `[x]` | Replace emoji in `Standard.__str__` | PLAN.md §12 | Encoding risk in logs/exports |
| Q-7 | `[x]` | Fix `CheckConstraint.check` deprecation in `process/models.py:92` | — | Rename `.check=` to `.condition=` before Django 6.0 removes it |

---

## Testing

| # | Status | Task | Plan ref | Notes |
|---|---|---|---|---|
| T-1 | `[x]` | Write tests for `part` / `process` | plan.md §13 | `WorkOrder.get_process_steps()`, `clean()`, `_calc_amps()` |
| T-2 | `[x]` | Write tests for `standard` | plan.md §13 | Revision change sets `requires_process_review` |
| T-3 | `[x]` | Write tests for `methods` | plan.md §13 | Auto-creates `ParameterToBeRecorded` from template |
| T-4 | `[x]` | Write tests for `fixtures` | plan.md §13 | PM due-date logic |
| T-5 | `[x]` | Write tests for `kanban` | plan.md §13 | Stock level and expiry |
| T-6 | `[x]` | Write auth redirect tests for all views | plan.md §13 | After S-3 is done; verify 302 for unauthenticated requests |

---

## Landing Page

Code review issues and feature work for the `landing_page` app.

| # | Status | Task | Plan ref | Notes |
|---|---|---|---|---|
| LP-1 | `[x]` | Apply TAT Technologies color scheme to landing page | PLAN.md §20 | Match navbar/footer palette; remove custom hero styles |
| LP-2 | `[x]` | Replace Capability accordion with Process/Standard/Classification table | PLAN.md §21 | Pull from Process app; group by Standard; remove search, expand-all, CSV |
| LP-3 | `[x]` | Fix N+1 in `export_capabilities_csv` | PLAN.md §22 | Add `prefetch_related('addons')` |
| LP-4 | `[x]` | Fix N+1 in `capability_pricing_detail` | PLAN.md §22 | Add `select_related('category')` + `prefetch_related('tags', 'addons')` |
| LP-5 | `[x]` | Remove dead `customer_pricing_view` | PLAN.md §22 | Not registered in urls.py; unreachable |
| LP-6 | `[x]` | Write tests for landing_page | PLAN.md §23 | No tests exist; cover new Process table view |

---

## Flake8 — Production Build Errors

Errors surfaced during production Docker build (`flake8 --ignore=E501,F401,W503,W504`).

| # | Status | Task | Plan ref | Notes |
|---|---|---|---|---|
| F8-1 | `[x]` | Fix F841 unused variable `p` in `kanban/tests.py:348` | PLAN.md §24 | Drop the assignment; record is created, `p` is never read |
| F8-2 | `[x]` | Fix E303 too many blank lines in `landing_page/views.py:48` | PLAN.md §24 | 3 blank lines between functions → 2 |
| F8-3 | `[x]` | Fix E402 imports-not-at-top in `masking/views.py` | PLAN.md §24 | Move `logger = logging.getLogger(__name__)` below all imports |
| F8-4 | `[x]` | Fix E402 imports-not-at-top in `periodic_testing/views.py` | PLAN.md §24 | Move `logger = logging.getLogger(__name__)` below all imports |

---

## UI / UX

| # | Status | Task | Plan ref | Notes |
|---|---|---|---|---|
| U-1 | `[x]` | Apply TAT Technologies color scheme to `base.html`, `navbar.html`, `footer.html` | PLAN.md §14 | Dark nav `#2E313F`, blue accent `#0066cc`; 13 flat links → grouped dropdowns; sticky navbar |
| U-2 | `[x]` | Navbar: rename brand to "Greensboro Site" + TAT logo; deduplicate Admin (staff-only); move Schedule → Operations, Inventory → Maintenance, Drawings → Quality | PLAN.md §15 | |
| U-3 | `[x]` | Fix duplicate Bootstrap JS in `pm_landing.html`; remove hardcoded Admin link from `ndt/index.html` | PLAN.md §16 | Duplicate script broke all navbar dropdowns on PM Tasks page |
| U-4 | `[x]` | Move Admin link into Maintenance dropdown; remove from right rail | PLAN.md §17 | Staff-only; keeps right rail clean (username + logout only) |
| U-5 | `[x]` | Remove all dropdown dividers from navbar | PLAN.md §18 | |
| U-6 | `[x]` | Footer: replace "Piedmont Aviation" with "Greensboro Site" | PLAN.md §19 | |

---

## Completed

| # | Date | Task |
|---|---|---|
| S-1 | 2026-03-10 | Moved `SECRET_KEY` out of `settings.py` into env vars; added to `.env.dev` and `.env.prod`; added `app/app/tests.py` to verify env var loading |
| S-2 | 2026-03-10 | Fixed `DEBUG` parsing in `settings.py`; set `DEBUG=False` in `.env.prod`; fixed `.gitignore` to exclude all `.env.*` files; untracked `.env.dev`, `.env.prod`, `.env.prod.db` from git |
| S-4 | 2026-03-10 | Removed `@csrf_exempt` from `AddDelayView` and `UpdateStatusView`; added `<meta name="csrf-token">` + `getCsrfToken()` to `main.html`; wired `X-CSRFToken` header into both `fetch()` calls; added 7 tests in `scheduler/tests.py` |
| S-3 | 2026-03-10 | Added `LoginRequiredMiddleware` to `settings.py`; created `/login/` and `/logout/` routes; created custom login page at `registration/login.html` with AC 120-78B compliance notice; added username + logout button to navbar; added 16 tests in `app/test_login.py` |
| B-1 | 2026-03-10 | Fixed `unique_part_standard_with_classification` condition: `isnull=True` → `isnull=False`; generated migration `part/migrations/0031_...`; added 6 tests in `part/tests.py` |
| B-2 | 2026-03-10 | Replaced per-plan `RackPM` DB queries with `Prefetch('rackpm_set', to_attr='prefetched_pms')` in `rack_list` and `pm_calendar`; fixed `rack.photos.first` → `rack.photos.all|first` in template; added 5 tests in `fixtures/tests.py` |
| B-3 | 2026-03-10 | Added `prefetch_related('chemical_lots')` to `kanban_dashboard` and `product_list`; fixed `get_current_stock()` → `total_quantity`; added `is_expiring_soon()` to `ChemicalLot`; added 9 tests in `kanban/tests.py` |
| T-5 | 2026-03-11 | Added 19 tests covering `ChemicalLot.status` (all 4 states), `Product.total_quantity`, `Product.needs_reorder`, and dashboard bucket placement at/above/below trigger level |
| T-6 | 2026-03-11 | Added `TestAllViewsRequireAuth` in `app/test_login.py`; 2 sub-test loops covering all 44 no-arg views and 37 detail views across all 17 apps — every URL verifies HTTP 302 → /login/ for unauthenticated requests |
| U-2 | 2026-03-11 | Navbar: TAT logo + "Greensboro Site" brand; Admin consolidated to staff-only single link; Schedule moved into Operations, Inventory into Maintenance, Drawings into Quality |
| U-3 | 2026-03-11 | Removed duplicate Bootstrap JS `<script>` from `pm_landing.html` (was breaking all navbar dropdowns); removed hardcoded Admin link from `ndt/index.html` footer |
| U-4 | 2026-03-11 | Moved Admin into Maintenance dropdown (staff-only, with divider); removed from right-rail nav |
| U-5 | 2026-03-11 | Removed all `<hr class="dropdown-divider">` elements from all navbar dropdowns |
| U-6 | 2026-03-11 | Footer brand updated from "Piedmont Aviation" to "Greensboro Site" |
| LP-6 | 2026-03-11 | Added 18 tests in `landing_page/tests.py`: home page 200/empty/grouped context, classification label (all/partial/none), auth redirect; pricing detail 200/404/context/auth; CSV content-type, disposition, header row, data row, auth; also fixed truncated `pricing_detail.html` template (unclosed if tag) |
| U-1 | 2026-03-11 | Applied TAT Technologies color scheme (`#2E313F` dark, `#0066cc` blue) to `base.html`, `navbar.html`, `footer.html`; restructured 13 flat nav items into grouped dropdowns (Operations, Quality, Maintenance); sticky navbar; CSS custom properties for maintainability; `extra_css`/`extra_js` template blocks added |

---

## Notes

- **Workflow:** Before writing code, add a plan section to `PLAN.md` and a task row here. See `CLAUDE.md §Development Workflow` for the full process.
- **Do not apply migrations to production** without testing the full migration chain in dev first.
- When an item is completed, set status to `[x]`, move it to the Completed table with the date, and add a `CHANGELOG.md` entry.
- When all items in a section are done, note it in `CHANGELOG.md`.
- **Backdating `auto_now_add` fields in tests**: Django prevents direct assignment to `auto_now_add` fields. Use `.update()` after creation to bypass this restriction, then `refresh_from_db()`:
  ```python
  obj = MyModel.objects.create(...)
  MyModel.objects.filter(pk=obj.pk).update(date_field=target_date)
  obj.refresh_from_db()
  ```
  Used in T-4 (`RackPM.date_performed`) and applicable anywhere an `auto_now_add` date needs to be controlled in tests.
