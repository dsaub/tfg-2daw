from celery import shared_task
from django.conf import settings
from .utilities import send_email
from .vars import login_message, verify_message
import random, string

from .models import User, VerificationCode
@shared_task
def enviar_correo_bienvenida(email_usuario: str, nombre_usuario: str):
    send_email(email_usuario, "Inicio de Sesión correcto", login_message.format(name = nombre_usuario))

@shared_task
def enviar_correo_confirmacion(usuario: User):
    code = VerificationCode.objects.create(
        user = usuario,
        code_mode = VerificationCode.VerificationModes.VERIFY_ACCOUNT,
        code = ''.join(random.choices(string.digits, k=12))
    )

    message = verify_message.format(name = usuario.get_full_name(), protocol = settings.PROTOCOL, domain = settings.DOMAIN, code = code.code)
    email_result = send_email(usuario.email, "Verificación de cuenta", message)