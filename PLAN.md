# Implementation Plan

Numbered sections correspond to `TASK.md` plan references. Add a new section here before starting any non-trivial feature or fix. Items are ordered by when they were planned.

---

## 1. Secret Key in Source (Critical)

**File:** `app/app/settings.py:25`

Move `SECRET_KEY` to an environment variable.

```python
SECRET_KEY = os.environ.get("SECRET_KEY")
```

Add `SECRET_KEY` to `.env.dev` and `.env.prod`.

---

## 2. DEBUG Always Evaluates True (High)

**File:** `app/app/settings.py:28`

```python
# Current (broken)
DEBUG = os.environ.get("DEBUG")

# Fix
DEBUG = os.environ.get("DEBUG", "").lower() == "true"
```

---

## 3. Add Login Protection to All Apps (High)

**Affected apps:** `process`, `part`, `standard`, `tanks`, `masking`, `kanban`, `logbook`, `ndt`, `periodic_testing`, `sds`, `tank_controls`, `fixtures`, `pm`, `scheduler`, `customer_links`, `kanban`

Easiest fix: add `LOGIN_URL` and enforce via middleware rather than per-view decorators. In `settings.py`:

```python
LOGIN_URL = '/admin/login/'
```

Then add to `MIDDLEWARE`:

```python
'django.contrib.auth.middleware.LoginRequiredMiddleware',  # Django 5.1+
```

Or decorate each view with `@login_required`. The `drawings` app already does this correctly — use it as the reference.

---

## 4. Remove `@csrf_exempt` from Scheduler Views (High)

**File:** `app/scheduler/views.py` — `AddDelayView`, `UpdateStatusView`

Remove `@csrf_exempt`. Update the frontend JS to include the CSRF token in the request headers:

```javascript
headers: { 'X-CSRFToken': getCookie('csrftoken') }
```

Django's `{% csrf_token %}` template tag must be present in the relevant template.

---

## 5. Fix Contradictory `PartStandard` Constraints (High)

**File:** `app/part/models.py:54–65`

Both constraints have `condition=Q(classification__isnull=True)` — one is unreachable. The intent appears to be:

- When classification is set: unique on `(part, standard, classification)`
- When classification is null: unique on `(part, standard)`

```python
constraints = [
    models.UniqueConstraint(
        fields=['part', 'standard', 'classification'],
        condition=Q(classification__isnull=False),
        name='unique_part_standard_with_classification'
    ),
    models.UniqueConstraint(
        fields=['part', 'standard'],
        condition=Q(classification__isnull=True),
        name='unique_part_standard_unclassified'
    )
]
```

Requires a new migration.

---

## 6. Fix N+1 Queries (Medium)

### 6a. Fixtures view
**File:** `app/fixtures/views.py:18–32`

Add `prefetch_related` to the rack queryset:

```python
racks = Rack.objects.prefetch_related(
    'pm_plan__task',
    Prefetch('rack_pms', queryset=RackPM.objects.order_by('-date_performed'))
).all()
```

Then restructure the loop to avoid per-rack DB hits.

### 6b. Kanban view
**File:** `app/kanban/views.py:13–19`

```python
products = Product.objects.prefetch_related('chemical_lots').all()
```

The `total_quantity` property will then use the prefetched cache instead of firing a new query per product.

---

## 7. Replace `print()` with `logging` (Medium)

**Files:**
- `app/periodic_testing/views.py:122`
- `app/masking/views.py:95`
- `app/logbook/views.py` (multiple)

Add to `settings.py`:

```python
import logging
LOGGING = {
    'version': 1,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'DEBUG'},
}
```

Replace all `print()` calls with `logger = logging.getLogger(__name__)` and `logger.debug(...)` / `logger.warning(...)`.

---

## 8. Replace `.get()` with `get_object_or_404()` (Medium)

**Affected files:** `kanban/views.py`, any other view using `Model.objects.get(id=pk)` directly.

```python
# Before
product = Product.objects.get(id=product_id)

# After
from django.shortcuts import get_object_or_404
product = get_object_or_404(Product, id=product_id)
```

---

## 9. Fix Media File URL in Masking View (Medium)

**File:** `app/masking/views.py:93–95`

```python
# Before
image_url = os.path.join(settings.MEDIA_ROOT, step.image.name)

# After
image_url = step.image.url  # web-accessible URL
image_path = step.image.path  # absolute filesystem path (for existence check)
if not os.path.exists(image_path):
    logger.warning("Image NOT FOUND: %s", image_path)
```

---

## 10. Protect `StandardProcess` from Accidental Cascade (Low)

**File:** `app/process/models.py:17–22`

Change `on_delete=models.CASCADE` to `on_delete=models.PROTECT` on the `standard_process` FK of `Process`. This prevents silent deletion of active processes when a `StandardProcess` is removed.

Requires a new migration.

---

## 11. Remove Unused Signal Imports (Low)

**File:** `app/process/models.py:6–7`

Remove unused imports:
```python
from django.db.models.signals import post_delete  # remove
from django.dispatch import receiver              # remove
```

---

## 12. Replace Emoji in `Standard.__str__` (Low)

**File:** `app/standard/models.py:55`

```python
# Before
review_flag = "🔴 Requires Process Review" if self.requires_process_review else ""

# After
review_flag = "[REVIEW REQUIRED]" if self.requires_process_review else ""
```

---

## 13. Write Tests (Critical — ongoing)

Start with the business-critical paths. Suggested order:

1. **`part` / `process`** — `WorkOrder.get_process_steps()`, `WorkOrder.clean()` (surface area validation), `WorkOrder._calc_amps()` (amps calculation from ASF + surface area)
2. **`standard`** — `Standard.save()` revision change sets `requires_process_review`
3. **`methods`** — `Method.save()` auto-creates `ParameterToBeRecorded` from template
4. **`fixtures`** — PM due-date logic, `RackPMPlan` signals
5. **`kanban`** — Stock level and expiry calculations
6. **Views** — At minimum, verify that all views return 302 redirect to login when unauthenticated (once login protection is added)

Target: 70%+ coverage on `part`, `process`, `standard`, and `methods` apps first.

---

## Checklist (§1–§13 — Remediation Sprint, completed 2026-03-10/11)

- [x] 1. Move `SECRET_KEY` to env var
- [x] 2. Fix `DEBUG` env var parsing
- [x] 3. Add login protection system-wide
- [x] 4. Remove `@csrf_exempt` from scheduler; add CSRF token to JS
- [x] 5. Fix `PartStandard` constraint logic + migrate
- [x] 6a. Fix N+1 in fixtures view
- [x] 6b. Fix N+1 in kanban view
- [x] 7. Replace `print()` with `logging`
- [x] 8. Replace `.get()` with `get_object_or_404()`
- [x] 9. Fix media file URL in masking view
- [x] 10. Change `StandardProcess` FK to `PROTECT` + migrate
- [x] 11. Remove unused signal imports
- [x] 12. Replace emoji in `Standard.__str__`
- [x] 13. Write tests

---

## 14. Apply TAT Technologies Color Scheme to Shared Templates

**Task ref:** U-1
**Date planned:** 2026-03-11
**Status:** Done

### Why

The app is operated by TAT Technologies staff. Matching the corporate color scheme improves brand consistency and professionalism. The original navbar had 13 flat nav items with no grouping — a UX problem on any screen narrower than ~1600px.

### Files changed

- `app/templates/base.html`
- `app/templates/navbar.html`
- `app/templates/footer.html`

### Approach

**Color palette (sourced from tat-technologies.com):**

| Token | Hex | Usage |
|---|---|---|
| `--tat-dark` | `#2E313F` | Navbar and footer background |
| `--tat-blue` | `#0066cc` | Active indicator, accent |
| `--tat-nav-text` | `rgba(255,255,255,0.72)` | Inactive nav link text |
| `--tat-nav-active` | `#ffffff` | Active nav link text |
| `--tat-border` | `rgba(255,255,255,0.10)` | Dividers, dropdown borders |

All tokens defined as CSS custom properties in `base.html` so the palette is changed in one place.

**Navbar restructure — 13 flat links → 6 top-level entries:**

| Top-level | Contains |
|---|---|
| Home | — |
| Schedule | — |
| Operations | Parts & Work Orders, Processes, Masking |
| Quality | Standards, SDS, Periodic Tests, NDT, Bath Controls |
| Maintenance | PM Tasks, Fixtures & Racks, Logbook |
| Inventory | — |
| Drawings | — |

Dropdown menus use the same dark background with a 2px `--tat-blue` top border. Active state on dropdown toggles (`section-active` class) driven by `request.resolver_match.url_name` and `request.resolver_match.namespace`.

Navbar is `sticky-top` — always visible, never hides on scroll.

**Template extension blocks added to `base.html`:**
- `{% block extra_css %}` — per-page stylesheets
- `{% block extra_js %}` — per-page scripts
- `{% block title %}` — defaults to "Piedmont Aviation"

**Footer:**
Three-column responsive layout (brand | address | phone). Copyright updated to "TAT Technologies". "Internal use only" notice added.

### No migrations required

Templates only — no model or view changes.

---

## 15. Navbar Brand Rename + Admin De-duplication + Nav Restructure

**Task ref:** U-2
**Date planned:** 2026-03-11
**Status:** Done

### Why

- Company rebranded: "Piedmont Aviation" is the old name; correct name is "Greensboro Site" under TAT Technologies.
- Admin link appeared twice (left nav + right nav) depending on viewport. Consolidated to one, staff-only.
- Schedule, Inventory, and Drawings were top-level items; user requested they move into logical dropdown groups.

### Files changed

- `app/templates/navbar.html`
- `app/templates/base.html` (brand CSS only)

### Changes

**Brand:**
- Replaced gear icon + "Piedmont Aviation" text with TAT Technologies SVG logo (`footerlogo.svg` — designed for dark backgrounds) + pipe separator + "Greensboro Site" text.
- Logo loaded from `https://tat-technologies.com/wp-content/uploads/2025/02/footerlogo.svg`.

**Admin link:**
- Removed from left nav entirely.
- Single Admin link kept in right-side nav, now wrapped in `{% if user.is_staff %}` — non-staff users never see it.

**Nav restructure:**

| Item | Before | After |
|---|---|---|
| Schedule | Top-level standalone | Operations dropdown |
| Inventory | Top-level standalone | Maintenance dropdown (below Logbook) |
| Drawings | Top-level standalone | Quality dropdown (below Bath Controls) |

Dividers (`<hr class="dropdown-divider">`) separate logical sub-groups within Operations and Quality dropdowns.

### No migrations required

---

## 16. Fix Duplicate Bootstrap JS in PM Landing + Remove Hardcoded NDT Admin Link

**Task ref:** U-3
**Date planned:** 2026-03-11
**Status:** Done

### Why

Two bugs found during navbar testing:

1. `pm_landing.html` loaded `bootstrap.bundle.min.js` a second time inside an accordion body. Loading Bootstrap JS twice destroys its event delegation — all dropdowns, collapses, and navbar toggles stop responding after visiting the PM Tasks page.
2. `ndt/index.html` had a footer-area `<a class="text-decoration-none" href="{% url 'admin:index' %}">Admin</a>`. The `text-decoration-none` class made it look like plain text, causing user confusion about a "second admin with no link." With Admin now in the navbar, this inline link is redundant.

### Files changed

- `app/pm/templates/pm/pm_landing.html` — removed duplicate `<script>` tag (line 125)
- `app/ndt/templates/ndt/index.html` — removed inline Admin link from page footer

---

## 17. Move Admin into Maintenance Dropdown

**Task ref:** U-4
**Date planned:** 2026-03-11
**Status:** Done

### Why

Admin in the right-side rail sat next to the username display, causing confusion (users read username as a second admin entry). Moving Admin into Maintenance groups it with operational tools and keeps the right rail to username + logout only.

### Files changed

- `app/templates/navbar.html` — removed Admin from right-side `navbar-nav`; added as last item in Maintenance dropdown inside `{% if user.is_staff %}`.

---

## 18. Remove Dropdown Dividers

**Task ref:** U-5
**Date planned:** 2026-03-11
**Status:** Done

### Why

User preference — dividers added visual noise without sufficient benefit.

### Files changed

- `app/templates/navbar.html` — removed all four `<li><hr class="dropdown-divider"></li>` elements.

---

## 19. Footer Brand Rename

**Task ref:** U-6
**Date planned:** 2026-03-11
**Status:** Done

### Why

Footer still referenced old name "Piedmont Aviation" after the navbar brand was updated in U-2.

### Files changed

- `app/templates/footer.html` — "Piedmont Aviation" → "Greensboro Site".

---

## 20. Landing Page — Apply TAT Color Scheme

**Task ref:** LP-1
**Date planned:** 2026-03-11
**Status:** Todo

### Why

The landing page (`index.html`) uses its own inline styles and Bootstrap defaults that do not match the TAT Technologies palette established in U-1. The hero section, card styles, accordion headers, and button colors all need to align with `--tat-dark` / `--tat-blue`.

### Approach

- Remove the inline `<style>` block in `index.html` and replace with classes that use the CSS custom properties defined in `base.html`.
- Hero / page header: dark background (`var(--tat-dark)`), white text.
- Capability cards: white background, `--tat-blue` accents on hover border and badge.
- Primary buttons: `--tat-blue` background (`btn` styled to match).
- No changes to `views.py`, `models.py`, or `urls.py` — template-only.

### Files to change

- `app/landing_page/templates/landing_page/index.html`

---

## 21. Landing Page — Replace Capability Accordion with Process Table

**Task ref:** LP-2
**Date planned:** 2026-03-11
**Status:** Todo

### Why

The current home page shows data from the `landing_page` app's own `Capability` model — a manually-maintained pricing catalog that stores `standard` as a plain text string and is completely isolated from the operational Process/Standard/Classification system. The user wants the home page to display the shop's actual certified capabilities, driven by live data from the Process app.

### What to display

A table in the center of the page, grouped by **Standard**, showing every configured **Process** with its **Standard Process** (process type/name) and **Classification** (method/class/type variant).

Example layout:

| Standard | Process Type | Classification |
|---|---|---|
| AMS 2700 Rev E | Cadmium Plate | Method A, Class 1 |
| AMS 2700 Rev E | Cadmium Plate | Method C, Class 2 |
| AMS 2759/9 | Hydrogen Embrittlement Relief | — |

Rows grouped under a collapsible (or visible) Standard header. Each Standard group shows all Process rows that belong to it.

### Remove

- Search box and client-side JS filter
- "Expand All / Collapse All" toggle
- "Download CSV" button and `export_capabilities_csv` view (or keep view but remove from landing page)

### Data query

```python
# views.py — landing_page index
from process.models import Process

processes = (
    Process.objects
    .select_related('standard', 'standard_process', 'classification')
    .order_by('standard__name', 'standard_process__title', 'classification__name')
)
```

Group in the view using a dict keyed by `standard`:

```python
from collections import defaultdict
grouped = defaultdict(list)
for p in processes:
    grouped[p.standard].append(p)
```

Pass `grouped.items()` to the template.

### Template structure

```
<section>  ← one per Standard
  <h5>{{ standard.name }} Rev {{ standard.revision }}</h5>
  <table>
    <thead>Standard Process | Classification</thead>
    <tbody>
      {% for process in processes %}
        <tr>
          <td>{{ process.standard_process.title }}</td>
          <td>{{ process.classification.name|default:"—" }}</td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
</section>
```

### Files to change

- `app/landing_page/views.py` — update `landing_page` view; remove or stub out `export_capabilities_csv`
- `app/landing_page/templates/landing_page/index.html` — full rewrite of content section

### No model changes or migrations required

The Capability, CapabilityCategory, AddOn, and related models are untouched (they are still used by `capability_pricing_detail`). Only the home page view changes.

---

## 22. Landing Page — Code Quality Fixes

**Task ref:** LP-3, LP-4, LP-5
**Date planned:** 2026-03-11
**Status:** Todo

### LP-3: N+1 in `export_capabilities_csv`

**File:** `app/landing_page/views.py`

```python
# Before — N+1: one query per capability for addons
for cap in Capability.objects.all():
    addons_str = ", ".join([f"{a.name} (${a.price})" for a in cap.addons.all()])

# After
for cap in Capability.objects.prefetch_related('addons').all():
    addons_str = ", ".join([f"{a.name} (${a.price})" for a in cap.addons.all()])
```

### LP-4: N+1 in `capability_pricing_detail`

**File:** `app/landing_page/views.py`

```python
# Before
capability = get_object_or_404(Capability, pk=pk)

# After
capability = get_object_or_404(
    Capability.objects.select_related('category').prefetch_related('tags', 'addons'),
    pk=pk,
)
```

### LP-5: Remove dead `customer_pricing_view`

**File:** `app/landing_page/views.py`

Delete `customer_pricing_view` entirely — it is not registered in `urls.py` and has never been reachable. Removing it eliminates dead code and a latent unvalidated `request.GET` read.

---

## 23. Landing Page — Tests

**Task ref:** LP-6
**Date planned:** 2026-03-11
**Status:** Todo

### What to test

- Home page returns 200 and passes `grouped` context with at least one Standard when processes exist.
- Home page returns 200 with empty `grouped` context when no processes exist.
- Auth redirect: unauthenticated request → 302 (already covered by T-6; confirm LP-2 view is protected).
- `capability_pricing_detail` returns 200 for valid pk, 404 for invalid pk.

---

## 24. Flake8 — Fix Production Build Errors

**Task ref:** F8-1, F8-2, F8-3, F8-4
**Date planned:** 2026-03-11
**Status:** Todo

Flake8 runs on every production Docker build (`--ignore=E501,F401,W503,W504`). Four
error classes were found during the first post-refactor production deploy. Fix all
before the next push.

### F8-1 — `kanban/tests.py:348` F841 unused variable

**File:** `app/kanban/tests.py:348`

```python
# before (F841 — p is assigned but never used)
p = make_product(name="Empty Chemical", trigger_level=10)

# after
make_product(name="Empty Chemical", trigger_level=10)
```

The variable is only needed to create the DB record; the test reads from the
view response context, not from `p` directly. Drop the assignment.

### F8-2 — `landing_page/views.py:48` E303 too many blank lines

**File:** `app/landing_page/views.py:48`

Two blank lines between top-level functions is the PEP 8 standard; the file
currently has three between `landing_page()` and `capability_pricing_detail()`.
Remove the extra blank line.

### F8-3 — `masking/views.py:7–15` E402 module-level imports not at top

**File:** `app/masking/views.py`

`logger = logging.getLogger(__name__)` was placed between import blocks on line 6,
causing every subsequent import to be flagged E402. Move the logger assignment to
after all imports.

```python
# correct order
import logging
import os
import tempfile

from django.db.models import Q, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from weasyprint import HTML

from .forms import MaskingProcessForm, MaskingStepForm
from .models import MaskingProcess, MaskingStep

logger = logging.getLogger(__name__)
```

### F8-4 — `periodic_testing/views.py:7–15` E402 module-level imports not at top

**File:** `app/periodic_testing/views.py`

Same root cause as F8-3. Move `logger = logging.getLogger(__name__)` to after all
imports.

---

## 25. Standard App — Remove Dead Utility Functions

**Task ref:** ST-1
**Date planned:** 2026-03-11
**Status:** Todo

**File:** `app/standard/models.py` lines 346–362

Three module-level utility functions exist at the bottom of `models.py` that are
never called anywhere in the codebase:

```python
def create_standard(name, description, revision, author, upload_file=None): ...
def list_standards(): ...
def get_standard_by_id(standard_id): ...
```

Delete all three. Any caller should use the ORM directly
(`Standard.objects.create(...)`, `.all()`, `get_object_or_404(Standard, pk=...)`).

No migration required. No test changes required (none of these are tested).

---

## 26. Standard App — Replace `unique_together` with `UniqueConstraint`

**Task ref:** ST-2
**Date planned:** 2026-03-11
**Status:** Todo

**Files:** `app/standard/models.py` lines 113 and 275

Two models use the deprecated `unique_together` syntax. Per CLAUDE.md, all
constraints must use `UniqueConstraint`.

**`StandardProcess` (line 113):**
```python
# before
class Meta:
    unique_together = ('standard', 'title')

# after
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['standard', 'title'],
            name='unique_standard_process_title',
        )
    ]
```

**`StandardPeriodicRequirement` (line 275):**
```python
# before
class Meta:
    unique_together = ("standard", "test_spec")

# after
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['standard', 'test_spec'],
            name='unique_standard_periodic_requirement',
        )
    ]
```

Two migrations required — one per app model change. Run and test in dev before
applying to production.

---

## 27. Standard App — Remove Unused Imports

**Task ref:** ST-3
**Date planned:** 2026-03-11
**Status:** Todo

Three unused imports across two files:

| File | Import | Line |
|---|---|---|
| `app/standard/models.py` | `Q` from `django.db.models` | 2 |
| `app/standard/views.py` | `Count` from `django.db.models` | 3 |
| `app/standard/admin.py` | `redirect` from `django.shortcuts` | 3 |

Remove each one. No functional change. Verify `flake8` passes after.

---

## 28. Standard App — Create Missing `process_review.html` Template

**Task ref:** ST-4
**Date planned:** 2026-03-11
**Status:** Todo

**File:** `app/standard/views.py` line 182 calls
`render(request, "standard/process_review.html", ...)` but the template does not
exist. Any visit to the process review URL will raise `TemplateDoesNotExist`.

Read `process_review_view()` in `views.py` to understand the context variables
passed (`standards_to_review` queryset), then create:

`app/standard/templates/standard/process_review.html`

The template should:
- Extend `base.html`
- List all standards where `requires_process_review=True` (name, revision, author)
- Show a POST form with an "Acknowledge Review" button for each standard
- Match the TAT color scheme (use `.tat-dark`, `.tat-blue` CSS vars, Bootstrap 5.3)
- Show a success/empty state if there are no pending reviews

---

## 29. Standard App — Fix Broken Test for Non-Existent View

**Task ref:** ST-5
**Date planned:** 2026-03-11
**Status:** Todo

**File:** `app/standard/tests.py` (or a separate `test_views.py` file if present)

The test `test_standard_create_view` attempts to reverse a URL named
`standard_create` which does not exist in `urls.py`. This test always errors
with `NoReverseMatch`.

Options:
1. If a create view is not planned: **delete the test**.
2. If a create view is planned: implement it first, then write the test.

The correct action is option 1 — there is no `standard_create` view in
`views.py` and no plan to add one (standards are managed through Django admin).
Remove the test.

---

## 30. Standard App — Expand Test Coverage

**Task ref:** ST-6
**Date planned:** 2026-03-11
**Status:** Todo

Current `tests.py` only covers `Standard` model behavior (revision flag,
unique constraint, `__str__`). The following are untested:

**Views:**
- `standard_list_view`: returns 200, context contains `standards`, filter by
  process type works, `pending_review` flag in context
- `standard_detail_view`: returns 200 for valid pk, 404 for invalid pk,
  context contains `blocks` with prefetched `classifications` and `inspections`
- `process_review_view`: returns 200 (GET), POST acknowledges a standard and
  clears `requires_process_review`, redirects after POST

**Models:**
- `StandardProcess.__str__()` returns expected string
- `Classification.__str__()` includes method/class/type labels
- `StandardRevisionNotification.__str__()` returns expected string

Add these tests to `app/standard/tests.py`. Use `setUpTestData` for shared
fixtures. Follow the patterns established in `kanban/tests.py` and
`fixtures/tests.py`.

---

## 31. Standard App — Apply TAT Color Scheme to Templates

**Task ref:** ST-7
**Date planned:** 2026-03-11
**Status:** Todo

Both existing templates (`standard_list.html`, `standard_detail.html`) use generic
Bootstrap utility classes. They need to be updated to use the TAT Technologies
palette established in `base.html` (CSS custom properties: `--tat-dark: #2E313F`,
`--tat-blue: #0066cc`).

**`standard_list.html`:**
- Page header: use `var(--tat-dark)` for heading color
- Filter/search bar background: `#f4f6f8` (matches capabilities table header)
- Process type filter badge active state: `var(--tat-blue)` background
- "Pending review" alert: keep Bootstrap `alert-warning` but add TAT icon style
- Standard cards/table rows: use `var(--tat-dark)` for column headers (like
  `.capabilities-table thead th` in `index.html`)
- NADCAP badge: replace `bg-dark` with `background-color: var(--tat-blue)` to
  match the `badge-nadcap` style in `landing_page/index.html`

**`standard_detail.html`:**
- Header card: `card-header` background → `var(--tat-dark)`, text white (matches
  `.standard-card .card-header` in `landing_page/index.html`)
- Process block section headings: `var(--tat-dark)` with blue underline accent
  (matches `.lp-section-title::after`)
- Revision badge: replace `bg-info text-dark` with `var(--tat-blue)` background,
  white text
- NADCAP badge: same as list — replace `bg-dark` with `var(--tat-blue)`

**`process_review.html`** (will be created in ST-4):
- Apply TAT scheme from the start — dark header card, blue action buttons.

Use `{% block extra_css %}` for any per-page custom CSS. Do not add a separate
stylesheet file.

---

## 32. Standard App — Fix and Complete Breadcrumbs on All Templates

**Task ref:** ST-8
**Date planned:** 2026-03-11
**Status:** Todo

Three templates need correct breadcrumbs. Two have bugs; one doesn't exist yet.

**`standard_list.html` — bug: first crumb links to `standard_list` but labels
it "Home":**
```html
<!-- current (wrong) -->
<li class="breadcrumb-item">
    <a href="{% url 'standard_list' %}">Home</a>
</li>

<!-- correct -->
<li class="breadcrumb-item">
    <a href="{% url 'home' %}">Home</a>
</li>
<li class="breadcrumb-item active" aria-current="page">Standards</li>
```

**`standard_detail.html` — missing Home crumb; chain should be
Home → Standards → [Standard Name]:**
```html
<!-- current -->
<li class="breadcrumb-item">
    <a href="{% url 'standard_list' %}">Standards</a>
</li>
<li class="breadcrumb-item active">{{ standard.name }} (Rev {{ standard.revision }})</li>

<!-- correct -->
<li class="breadcrumb-item">
    <a href="{% url 'home' %}">Home</a>
</li>
<li class="breadcrumb-item">
    <a href="{% url 'standard_list' %}">Standards</a>
</li>
<li class="breadcrumb-item active" aria-current="page">
    {{ standard.name }} (Rev {{ standard.revision }})
</li>
```

**`process_review.html`** (new in ST-4) — breadcrumb to include from creation:
```
Home → Standards → Process Review
```

Style all breadcrumbs consistently: plain Bootstrap `breadcrumb` component,
no custom CSS needed beyond what `base.html` already provides.

---

## 33. Process App — Replace `Method.objects.get()` with `get_object_or_404()`

**Task ref:** PR-1
**Date planned:** 2026-03-11
**Status:** Todo

**File:** `app/process/views.py:30`

`get_method_info()` uses `Method.objects.get(id=method_id)` wrapped in a bare
`except Method.DoesNotExist`. Per CLAUDE.md, views must always use
`get_object_or_404()`.

```python
# before
try:
    method = Method.objects.get(id=method_id)
    return JsonResponse({...})
except Method.DoesNotExist:
    return JsonResponse({"error": "Method not found"}, status=404)

# after
method = get_object_or_404(Method, id=method_id)
return JsonResponse({...})
```

`get_object_or_404` already imported on line 4. Remove the try/except block.
No migration required.

---

## 34. Process App — Remove Dead Code: `ProcessStep.save()` No-op

**Task ref:** PR-2
**Date planned:** 2026-03-11
**Status:** Todo

**File:** `app/process/models.py:99–100`

```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
```

This `save()` override adds no logic — it only calls `super().save()`, which
Django already does automatically. Remove the entire method.

No migration required.

---

## 35. Process App — Remove Dead Code: `step_count_display()` in Admin

**Task ref:** PR-3
**Date planned:** 2026-03-11
**Status:** Todo

**File:** `app/process/admin.py:46–53`

`step_count_display()` is decorated with `@admin.display` but is never added to
`list_display` — it is unreachable in the admin UI. It also has two bugs:

1. **N+1 query**: calls `obj.steps.count()` per row with no prefetch annotation.
2. **Phantom ordering**: `ordering='_step_count'` references an annotation that
   does not exist; adding this to `list_display` would error on column sort.

Delete the entire method. If a step count column is ever needed, implement it
properly with `get_queryset()` annotating `Count('steps')`.

No migration required.

---

## 36. Process App — Explicit Fields in `ProcessForm`

**Task ref:** PR-4
**Date planned:** 2026-03-11
**Status:** Todo

**File:** `app/process/forms.py:14`

`fields = '__all__'` exposes every model field, including auto-managed fields
(`created_at`, `updated_at`, `is_template`). Replace with an explicit list:

```python
fields = [
    'standard',
    'standard_process',
    'classification',
    'description',
    'is_template',
]
```

Verify the admin still functions correctly after this change — the inline
formset and classification filtering logic should be unaffected since they
operate on field instances that will still be present.

No migration required.

---

## 37. Process App — Flake8 Compliance

**Task ref:** PR-5
**Date planned:** 2026-03-11
**Status:** Todo

Run `flake8 --ignore=E501,F401,W503,W504 process/` inside the Docker container
and fix every error returned. Based on manual review the code is mostly clean,
but verify:

- No E402 (imports not at top of file)
- No E303 (too many blank lines)
- No F841 (unused variables)
- No other F-series errors

Fix all findings before marking done. If no issues are found, record that
result in the CHANGELOG.

---

## 38. Process App — Apply TAT Color Scheme to Templates

**Task ref:** PR-6
**Date planned:** 2026-03-11
**Status:** Todo

Two operator-facing templates need the TAT Technologies palette.

**`process_landing.html`:**
- Page heading: `color: var(--tat-dark)` with blue underline accent (`.page-heading` pattern)
- Table `thead.table-light` → TAT dark header (`.standards-thead` pattern from standard app)
- "View Flowchart" button: `btn-outline-primary` → TAT blue outline or filled
- "Search" button: `btn-primary` → TAT blue
- Empty state: `alert-info` → dashed border style matching landing page

**`process_flowchart.html`:**
- Card header: add `.tat-card-header` (dark background, white text) with standard name and classification label
- "Download SVG" button: `btn-outline-primary` → TAT blue outline
- "Back" button: `btn-secondary` → `btn-outline-secondary`
- Flowchart wrapper: replace `style="overflow: auto; border: 1px solid #eee; padding: 1rem;"` with Bootstrap utilities (`overflow-auto p-3 border rounded`)

Add `{% block extra_css %}` with any required per-page CSS.

---

## 39. Process App — Add Breadcrumbs to All Templates

**Task ref:** PR-7
**Date planned:** 2026-03-11
**Status:** Todo

Neither template has breadcrumb navigation. Add Bootstrap `breadcrumb`
component as the first element inside `{% block content %}` on each page.

**`process_landing.html`** — chain:
```
Home → Processes
```
```html
<nav aria-label="breadcrumb" class="mb-4">
  <ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="{% url 'home' %}">Home</a></li>
    <li class="breadcrumb-item active" aria-current="page">Processes</li>
  </ol>
</nav>
```

**`process_flowchart.html`** — chain:
```
Home → Processes → [Standard Name] Flowchart
```
```html
<nav aria-label="breadcrumb" class="mb-3">
  <ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="{% url 'home' %}">Home</a></li>
    <li class="breadcrumb-item"><a href="{% url 'process_landing' %}">Processes</a></li>
    <li class="breadcrumb-item active" aria-current="page">
      {{ process.standard.name }} Flowchart
    </li>
  </ol>
</nav>
```

---

## 40. Process App — Expand Test Coverage

**Task ref:** PR-8
**Date planned:** 2026-03-11
**Status:** Todo

Current `tests.py` has 3 tests covering only the `PROTECT` FK constraint.
Add coverage for:

**Views:**
- `ProcessLandingView`: returns 200, context has `processes`, search filter
  narrows results, auth redirect for unauthenticated request
- `process_flowchart_view`: returns 200 for valid pk, 404 for invalid pk,
  context has `process` and `svg`, auth redirect
- `get_method_info`: returns 200 with JSON for valid method id, 400 when no
  id provided, 404 for invalid id

**Models:**
- `Process.__str__()` includes standard name
- `ProcessStep.__str__()` includes standard name and method title

Add tests to `app/process/tests.py`. Use `setUpTestData` for shared fixtures.
