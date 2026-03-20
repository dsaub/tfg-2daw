from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from .utilities import send_email, send_hemail
from .vars import login_message, verify_message
import random, string

from .models import User, VerificationCode
@shared_task
def enviar_correo_bienvenida(email_usuario: str, nombre_usuario: str):
    html_content = render_to_string(
        'emails/welcome.html',
        {
            "name": nombre_usuario
        },
        using='jinja2'
    )
    send_hemail(email_usuario, "Inicio de Sesión correcto", html_content, "Has iniciado sesión...")

@shared_task
def enviar_correo_confirmacion(usuario: User):
    code = VerificationCode.objects.create(
        user = usuario,
        code_mode = VerificationCode.VerificationModes.VERIFY_ACCOUNT,
        code = ''.join(random.choices(string.digits, k=12))
    )

    message = verify_message.format(name = usuario.get_full_name(), protocol = settings.PROTOCOL, domain = settings.DOMAIN, code = code.code)
    email_result = send_email(usuario.email, "Verificación de cuenta", message)