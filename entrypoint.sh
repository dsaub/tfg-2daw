#!/bin/sh

set -eu

# Si se pasan argumentos, ejecutarlos directamente (ej: celery worker)
if [ $# -gt 0 ]; then
    exec "$@"
fi

echo "Running DB migrations..."
uv run python manage.py migrate
echo "Collecting STATIC..."
uv run python manage.py collectstatic --noinput --clear

echo "Running server!"

uv run gunicorn --bind 0.0.0.0:8000 proyecto.wsgi:application --forwarded-allow-ips="*"
