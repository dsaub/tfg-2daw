#!/bin/sh

set -eu

echo "Sleeping due to mysql..."
sleep 10
echo "Running DB migrations..."
uv run python manage.py migrate
echo "Collecting STATIC..."
uv run python manage.py collectstatic --noinput --clear

echo "Running server!"

uv run gunicorn --bind 0.0.0.0:8000 proyecto.wsgi:application --forwarded-allow-ips="*"
