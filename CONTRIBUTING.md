# Contributing

Guide for developers working on the Piedmont app.

---

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Git
- A text editor / IDE

You do not need Python, PostgreSQL, or any other dependency installed locally — Docker handles everything.

---

## First-Time Setup

```bash
git clone <repo-url>
cd piedmont

# Copy env files (ask the project owner for actual values)
cp .env.dev .env.dev.local   # not needed — .env.dev is already present for dev

# Build and start
docker compose up --build

# In a second terminal, run migrations and create a superuser
docker compose run web python manage.py migrate
docker compose run web python manage.py createsuperuser
```

App is now running at `http://localhost:8000`.
Django admin is at `http://localhost:8000/admin/`.

---

## Day-to-Day Development

**Start the stack:**
```bash
docker compose up
```

**Stop the stack:**
```bash
docker compose down
```

**Apply new migrations:**
```bash
docker compose run web python manage.py migrate
```

**Create migrations after a model change:**
```bash
docker compose run web python manage.py makemigrations <appname>
```

**Open a Django shell:**
```bash
docker compose run web python manage.py shell
```

**Run tests:**
```bash
docker compose run web pytest                                           # all
docker compose run web pytest <appname>/tests.py                       # one app
docker compose run web pytest <appname>/tests.py::Class::method        # one test
```

**Lint:**
```bash
flake8 app/
```

---

## Git Workflow

- **Never push directly to `main`.** All changes go through a feature branch and pull request.
- Branch naming: `feature/<short-description>`, `fix/<short-description>`, `chore/<short-description>`
- Keep commits focused. One logical change per commit.
- Write a clear commit message: `fix: correct DEBUG env var parsing` not `update settings`
- Before opening a PR: run tests, run flake8, confirm nothing is broken locally.

```bash
git checkout -b fix/debug-env-var
# make changes
git add app/app/settings.py
git commit -m "fix: correct DEBUG env var parsing"
git push origin fix/debug-env-var
# open pull request
```

---

## Adding a New App

1. Create the app:
   ```bash
   docker compose run web python manage.py startapp <appname>
   ```
2. Register it in `app/app/settings.py` under `INSTALLED_APPS`.
3. Add its URLs in `app/app/urls.py`.
4. Follow the existing app structure — `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, `tests.py`, `templates/<appname>/`.
5. Auth is handled globally by `LoginRequiredMiddleware` — you do not need to add `@login_required` to individual views. Do not add `@login_required` or `@csrf_exempt` to new views.
6. Run `makemigrations` and `migrate`.

---

## Migrations

- **Never edit an existing migration file.**
- Never squash migrations without testing the full migration chain from zero.
- Every model change — including `help_text`, `verbose_name`, and `default` changes — requires a new migration.
- Before deploying, always run `python manage.py migrate --plan` to preview what will run.

---

## Production Deployment

**The production server uses `docker-compose.prod.yml`. Never run `docker compose up` (the dev file) on prod.**

Deployment steps (run on the production server):

```bash
git pull origin main
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml run web python manage.py migrate --noinput
```

`collectstatic` runs automatically on container start (`RUN_COLLECTSTATIC=1` in `entrypoint.prod.sh`).

After deploying, verify:
- The app loads at the production URL
- The Django admin is accessible
- Check container logs for errors: `docker compose -f docker-compose.prod.yml logs web`

---

## Environment Files

| File | Used by | Contains |
|---|---|---|
| `.env.dev` | `docker-compose.yml` | Dev DB credentials, `DEBUG=True` |
| `.env.prod` | `docker-compose.prod.yml` | Prod app config, `DEBUG=False` |
| `.env.prod.db` | `docker-compose.prod.yml` | Prod Postgres credentials |

**Never commit `.env.prod` or `.env.prod.db` to the repository.**

---

## Code Standards

See `CLAUDE.md` for the full list. Key rules:

- Auth is global via `LoginRequiredMiddleware` — no `@login_required` needed on individual views
- Use `get_object_or_404()`, never `Model.objects.get()` in views
- No `print()` — use `logging`
- Max line length 79 (flake8 enforced)
- Bootstrap 5.3 utility classes before custom CSS
- Forms rendered with `django-widget-tweaks`

---

## Project Docs

| File | Purpose |
|---|---|
| `CLAUDE.md` | Instructions for Claude Code AI assistant |
| `TASK.md` | Active task tracker |
| `plan.md` | Remediation plan for known issues |
| `CHANGELOG.md` | History of significant changes |
| `docs/data-model.md` | Full data model reference |
