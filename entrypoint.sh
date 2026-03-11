#!/bin/bash

figlet Proyecto MVC

echo "Running DB migrations..."
python manage.py migrate
echo "Collecting STATIC..."
python manage.py collectstatic --noinput

echo "Running server!"

gunicorn --bind 0.0.0.0:8000 proyecto.wsgi:application --forwarded-allow-ips="*"