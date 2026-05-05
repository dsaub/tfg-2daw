from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')

app = Celery('proyecto')
app.config_from_object('django.conf:settings', namespace="CELERY")

import django
django.setup()

from tienda import tasks