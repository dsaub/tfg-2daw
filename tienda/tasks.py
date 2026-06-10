import os
import secrets
import string

import boto3
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from . import pdf
from .models import Order, User, VerificationCode
from .utilities import send_email, send_hemail
from .vars import login_message, verify_message
@shared_task
def enviar_correo_bienvenida(email_usuario: str, nombre_usuario: str):
    html_content = render_to_string(
        'tienda/emails/welcome.html',
        {
            "name": nombre_usuario
        },
    )
    send_hemail(email_usuario, "Inicio de Sesión correcto", html_content, "Has iniciado sesión...")

@shared_task
def banear_usuario(email_usuario: str):
    html_content = render_to_string(
        'tienda/emails/ban.html',
        {
        },
    )

    send_hemail(email_usuario, "Cuenta Bloqueada", html_content, "Tu cuenta ha sido bloqueada...")

@shared_task
def desbanear_usuario(email_usuario: str):
    html_content = render_to_string(
        'tienda/emails/unban.html',
        {},
    )

    send_hemail(email_usuario, "Cuenta Desbloqueada", html_content, "Tu cuenta ha sido desbloqueada...")

@shared_task
def enviar_correo_confirmacion(id: int):
    usuario = User.objects.get(id=id)
    code = VerificationCode.objects.create(
        user = usuario,
        code_mode = VerificationCode.VerificationModes.VERIFY_ACCOUNT,
        code = ''.join(secrets.choice(string.digits) for _ in range(12))
    )

    message = verify_message.format(name = usuario.get_full_name(), protocol = settings.PROTOCOL, domain = settings.DOMAIN, code = code.code)
    email_result = send_email(usuario.email, "Verificación de cuenta", message)

@shared_task
def enviar_correo_recuperacion(email: str):
    usuario: User | None
    try:
        usuario = User.objects.get(email=email)
    except User.DoesNotExist as e:
        usuario = None
    if usuario is not None:
        ver_code = VerificationCode.objects.create(
            code_mode = VerificationCode.VerificationModes.RESET_PASSWORD,
            user = usuario,
            code = ''.join(secrets.choice(string.digits) for _ in range(12))
        )
        ver_code.save()
        html_content = render_to_string(
            'tienda/emails/reset_pass.html',
            {
                "name": usuario.get_full_name(),
                "domain": settings.DOMAIN,
                "protocol": settings.PROTOCOL,
                "code": ver_code.code
            },
        )

        send_hemail(email, "Reset de Contraseña", html_content, "Estas reseteando la contraseña...")
    else:
        print("User does not exist, Cancelling TASK.")

# Purchased items should be a list of dictionary, the dictionary must follow this tags: amount, product name, price (each)
@shared_task
def process_purchase(user_id: int, purchased_items: list, payment_method: str, transaction_code: str):
    user = User.objects.get(id=user_id)
    total = 0
    for i in purchased_items:
        total += i["price"]*i["amount"]
    pdf_data = pdf.generar_recibo(
        user.get_full_name(),
        total,
        purchased_items,
        payment_method,
        transaction_code,
    )

    if settings.S3_ENABLE:
        s3 = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        s3.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=f"recibos/{transaction_code}.pdf",
            Body=pdf_data,
            ContentType="application/pdf",
        )
        rel_path = f"recibos/{transaction_code}.pdf"
    else:
        rel_path = f"recibos/user_{user_id}/recibo_{transaction_code}.pdf"
        abs_dir = os.path.join(settings.MEDIA_ROOT, f"recibos/user_{user_id}")
        os.makedirs(abs_dir, exist_ok=True)
        abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        with open(abs_path, 'wb') as f:
            f.write(pdf_data)

    try:
        order = Order.objects.get(transaction_code=transaction_code)
        order.receipt_file = rel_path
        order.save(update_fields=['receipt_file'])
    except Order.DoesNotExist:
        pass

    email = EmailMessage(
        subject="Tu recibo de compra",
        body = "Hola, adjunto encontrarás el recibo de tu reciente transacción",
        from_email = settings.DEFAULT_FROM_EMAIL,
        to = [user.email]
    )

    email.attach("recibo.pdf", pdf_data, "application/pdf")

    email.send()