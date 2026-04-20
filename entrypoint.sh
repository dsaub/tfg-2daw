#!/bin/sh

set -eu

echo "Sleeping due to mysql..."
sleep 10
echo "Running DB migrations..."
python manage.py migrate
echo "Collecting STATIC..."
python manage.py collectstatic --noinput --clear

echo "Running server!"

gunicorn --bind 0.0.0.0:8000 proyecto.wsgi:application --forwarded-allow-ips="*"