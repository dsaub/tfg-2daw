from celery import shared_task
from .utilities import send_email
from .vars import login_message

@shared_task
def enviar_correo_bienvenida(email_usuario, nombre_usuario):
    send_email(email_usuario, "Inicio de Sesión correcto", login_message.format(name = nombre_usuario))