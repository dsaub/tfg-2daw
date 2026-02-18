#!/bin/bash

figlet Proyecto MVC

echo "Running DB migrations..."
python manage.py migrate
echo "Collecting STATIC..."
yes | python manage.py collectstatic

echo "Running server!"

gunicorn --bind 0.0.0.0:8000 proyecto.wsgi:application