#!/bin/sh
set -e

# Optional: default values
: "${DATABASE:=postgres}"
: "${SQL_HOST:=db}"
: "${SQL_PORT:=5432}"
: "${RUN_COLLECTSTATIC:=1}"

if [ "$DATABASE" = "postgres" ]; then
  echo "Waiting for Postgres at ${SQL_HOST}:${SQL_PORT} ..."
  # wait up to ~60s
  ATTEMPTS=0
  until nc -z "$SQL_HOST" "$SQL_PORT"; do
    ATTEMPTS=$((ATTEMPTS+1))
    if [ "$ATTEMPTS" -ge 200 ]; then
      echo "Postgres did not become ready in time"; exit 1
    fi
    sleep 0.3
  done
  echo "PostgreSQL started"
fi

# Sanity check Django can import settings
python manage.py check

# Apply migrations (idempotent)
python manage.py migrate --noinput

# Collect static only when desired (e.g., prod)
if [ "$RUN_COLLECTSTATIC" = "1" ]; then
  python manage.py collectstatic --noinput
fi

# Hand off to CMD (gunicorn, etc.)
exec "$@"

