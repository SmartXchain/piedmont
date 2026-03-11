# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Workflow

**Every feature addition or significant change must follow this order — no exceptions:**

1. **Plan first — update `PLAN.md`.**
   Add a numbered section (`## N. Title`) describing: what is changing, why, which files are affected, the specific approach, and any migration or test requirements. Be concrete — include code snippets, file paths, and line numbers where relevant.

2. **Track it — update `TASK.md`.**
   Add task rows using the next available ID in the appropriate section. Set status to `[~]` In Progress when work begins. For a new category of work, add a new section with a clear heading.

3. **Write the code.**
   Follow the plan exactly. If the approach changes during implementation, update `PLAN.md` before continuing — the plan is the source of truth, not the chat history.

4. **Close it out.**
   - Set status to `[x]` Done in `TASK.md`.
   - Move the item to the Completed table with today's date and a one-line summary.
   - Add an entry to `CHANGELOG.md`.

> Trivial changes (typo fixes, comment corrections, one-line config tweaks) may skip the plan step, but must still be tracked in `TASK.md` and `CHANGELOG.md`.

---

## What This Is

Piedmont is an internal Django 5.x web application for an aerospace special-processes shop (Piedmont Aviation). It manages process travelers and work orders for NADCAP-certified surface treatment operations (cadmium plating, anodizing, chemical conversion, stripping, etc.), along with chemical inventory, tank bath controls, preventive maintenance, logbooks, drawings, and NDT records.

**This app is in production.** All changes must be tested locally before deploying. Migrations must be reviewed carefully — never auto-squash or edit existing migrations.

---

## Commands

All Django source lives in `app/`. The Django project package is `app/app/` (settings, urls, wsgi/asgi).

**Start dev environment (Docker):**
```bash
docker compose up --build
docker compose down
docker compose run web python manage.py migrate
docker compose run web python manage.py createsuperuser
```
Dev server: `http://localhost:8000`. Config from `.env.dev`.

**Without Docker:**
```bash
cd app
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Run tests:**
```bash
docker compose run web pytest                                           # all tests
docker compose run web pytest fixtures/tests.py                        # single app
docker compose run web pytest fixtures/tests.py::ClassName::test_name  # single test
```
pytest config: `app/pytest.ini` — `DJANGO_SETTINGS_MODULE = app.settings`.

**Lint:**
```bash
flake8 app/
```

**Make a migration after model changes:**
```bash
docker compose run web python manage.py makemigrations <appname>
docker compose run web python manage.py migrate
```

---

## Coding Rules

### Django

- **Always use `get_object_or_404()`**, never `Model.objects.get()` in views.
- **Auth is handled globally by `LoginRequiredMiddleware`** (Django 5.1+, configured in `settings.py`). Do not add `@login_required` to individual views and do not add `@csrf_exempt` to any view.
- **Use `select_related` / `prefetch_related`** on any queryset in a view that touches related objects. Never let N+1 queries into views.
- **Form validation belongs in `clean()` methods**, not in the view. Views call `form.is_valid()` and redirect — nothing more.
- **Never call `QuerySet.update()`** on models that have business logic in `save()` or `clean()` (e.g. `WorkOrder`, `Standard`, `Method`). Use `.save()` so signals and hooks run.
- **Wrap multi-step writes in `transaction.atomic()`**.
- **Never skip migrations.** Every model change needs a migration. Never edit an existing migration file.
- Use `UniqueConstraint` with `condition=` for partial uniqueness, not `unique_together`.
- Every new `ForeignKey` must have an explicit `on_delete` with a comment explaining the choice if it is not `PROTECT`.
- Register every new app in `INSTALLED_APPS` and `app/app/urls.py`.
- Follow the existing app structure: `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, `tests.py`, `templates/<appname>/`.

### Python

- Flake8 enforced. Max line length **79 characters**. Fix all `F`-series errors before finishing.
- No `print()` statements. Use `import logging` and `logger = logging.getLogger(__name__)`.
- No bare `except:` clauses. Catch specific exceptions.
- No unused imports.

### PostgreSQL

- Add `db_index=True` on any field used in `filter()` or `order_by()` on large tables.
- Use `UniqueConstraint` (not `unique_together`) for all new constraints.
- Write explicit `on_delete` on every FK — never rely on the default.

### Bootstrap

- Bootstrap **5.3** from CDN only. Do not add a local copy or npm package.
- Use Bootstrap utility classes before writing any custom CSS.
- All forms are rendered with `django-widget-tweaks`. Do not hand-write form field HTML.
- Icons use Bootstrap Icons (CDN). Do not add a separate icon library.

### PDF Generation

- WeasyPrint renders HTML → PDF. It requires native libs (cairo, pango) in the Docker image.
- Do not test PDF views outside Docker — they will fail without the native libs installed.

---

## Architecture

### Core Data Model

See `docs/data-model.md` for the full reference. The short version:

```
Standard ──► StandardProcess
    │               │
    └──► Classification
              │
              ▼
         Process  (unique per Standard + Classification)
              │
              ▼
         ProcessStep  (ordered, step_number ≥ 1)
              │
              ▼
           Method  (tank params, rectifier flags, recorded parameters)
```

`WorkOrder` (in `part`) ties a `Part` + `Standard` + `Classification` run together. It resolves its process steps at runtime via `get_process_steps()` and calculates rectifier amps from surface area × ASF.

### Supporting Apps

| App | Purpose |
|---|---|
| `tanks` | Physical production tanks + `ProductionLine` grouping |
| `tank_controls` | Bath controls: `ControlSet` → `TemperatureSpec`, `ChemicalSpec`, `CheckSpec`, `PeriodicTestSpec` |
| `kanban` | Chemical inventory — `Product` + `ChemicalLot` (stock levels, expiry tracking) |
| `masking` | Masking process steps with images; PDF output via WeasyPrint |
| `fixtures` | Shop racks with `RackPMPlan` and `RackPM` completion records |
| `pm` | General PM tasks not tied to racks |
| `logbook` | `LogEntry` (process runs), `DailyInspectionLogEntry`, `ScrubberLog` |
| `periodic_testing` | Periodic test scheduling and execution logging |
| `sds` | Safety Data Sheet management |
| `scheduler` | Production scheduling (namespaced `scheduler`) |
| `drawings` | Drawing management (namespaced `drawings`) — reference app for auth pattern |
| `ndt` | Non-destructive testing records (namespaced `ndt`) |
| `customer_links` | Curated external links for customers |
| `landing_page` | Home/dashboard |

### Templates

Shared templates (`base.html`, `navbar.html`, `footer.html`) are in `app/templates/`. App templates are in `app/<appname>/templates/<appname>/`. Base uses Bootstrap 5.3 + Bootstrap Icons + Chart.js 4.4, all from CDN.

### Static / Media

- Static: `app/staticfiles/` — collected via `collectstatic`
- Media uploads: `app/mediafiles/`
- Dev: Django serves media (DEBUG guard in `urls.py`). Prod: Nginx serves both.

### Production Deployment

`docker-compose.prod.yml` + `nginx/`. The prod entrypoint runs `collectstatic` automatically. Never use `docker-compose.yml` on the production server.

---

## Project Docs

| File | Purpose |
|---|---|
| `PLAN.md` | Detailed implementation plans — updated before every feature/fix |
| `TASK.md` | Active task tracker — check here before starting work |
| `CHANGELOG.md` | Record of significant changes |
| `CONTRIBUTING.md` | Onboarding and workflow for human developers |
| `NOTES.md` | Compliance context, open decisions, and planning notes |
| `docs/data-model.md` | Full data model reference |

---

## Known Issues / Next Work

Active issues and upcoming work are tracked in `TASK.md`. Check there before starting anything new. Historical resolved issues are in `CHANGELOG.md`.
