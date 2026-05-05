from celery import Celery
import os

app = Celery('proyecto')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
app.config_from_object('django.conf:settings', namespace="CELERY")

app.user_options = {}

app.autodiscover_tasks()