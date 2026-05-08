web: gunicorn proyecto.wsgi --bind 0.0.0.0:$PORT
worker: celery -A proyecto worker --loglevel=info