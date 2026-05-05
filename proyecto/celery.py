from celery import Celery
import os

app = Celery('proyecto')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
app.config_from_object('django.conf:settings', namespace="CELERY")

# Tasks loaded via CELERY_IMPORTS in settings.py