from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .utilities import send_email, send_hemail
from .vars import login_message, verify_message
import random, string
from . import pdf

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
def enviar_correo_confirmacion(id: int):
    usuario = User.objects.get(id=id)
    code = VerificationCode.objects.create(
        user = usuario,
        code_mode = VerificationCode.VerificationModes.VERIFY_ACCOUNT,
        code = ''.join(random.choices(string.digits, k=12))
    )

    message = verify_message.format(name = usuario.get_full_name(), protocol = settings.PROTOCOL, domain = settings.DOMAIN, code = code.code)
    email_result = send_email(usuario.email, "Verificación de cuenta", message)

@shared_task
def enviar_correo_recuperacion(email: str):
    usuario = User.objects.get(email=email)
    if usuario is not None:
        ver_code = VerificationCode.objects.create(
            code_mode = VerificationCode.VerificationModes.RESET_PASSWORD,
            user = usuario,
            code = ''.join(random.choices(string.digits, k=12))
        )
        ver_code.save()
        html_content = render_to_string(
            'emails/reset_pass.html',
            {
                "name": usuario.get_full_name(),
                "domain": settings.DOMAIN,
                "protocol": settings.PROTOCOL,
                "code": ver_code.code
            },
            using='jinja2'
        )

        send_hemail(email, "Reset de Contraseña", html_content, "Estas reseteando la contraseña...")


# Purchased items should be a list of dictionary, the dictionary must follow this tags: amount, product name, price (each)
@shared_task
def process_purchase(user_id: int, purchased_items: list, payment_method: str):
    user = User.objects.get(id=user_id)
    total = 0
    for i in purchased_items:
        total += i["price"]*i["amount"]
    pdf_data = pdf.generar_recibo(user.get_full_name(), total, purchased_items, payment_method)
    
    email = EmailMessage(
        subject="Tu recibo de compra",
        body = "Hola, adjunto encontrarás el recibo de tu reciente transacción",
        from_email = settings.DEFAULT_FROM_EMAIL,
        to = [user.email]
    )

    email.attach("recibo.pdf", pdf_data, "application/pdf")

    email.send()