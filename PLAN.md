# Remediation Plan

Based on the code review. Items are ordered by priority.

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

## Checklist

- [ ] 1. Move `SECRET_KEY` to env var
- [ ] 2. Fix `DEBUG` env var parsing
- [ ] 3. Add login protection system-wide
- [ ] 4. Remove `@csrf_exempt` from scheduler; add CSRF token to JS
- [ ] 5. Fix `PartStandard` constraint logic + migrate
- [ ] 6a. Fix N+1 in fixtures view
- [ ] 6b. Fix N+1 in kanban view
- [ ] 7. Replace `print()` with `logging`
- [ ] 8. Replace `.get()` with `get_object_or_404()`
- [ ] 9. Fix media file URL in masking view
- [ ] 10. Change `StandardProcess` FK to `PROTECT` + migrate
- [ ] 11. Remove unused signal imports
- [ ] 12. Replace emoji in `Standard.__str__`
- [ ] 13. Write tests (ongoing)
