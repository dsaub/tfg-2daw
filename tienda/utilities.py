from django.core.mail import send_mail
import logging
from django.conf import settings


logger = logging.getLogger("email.system")

def send_email(dest: str, title: str, body: str):
    try:
        send_mail(
            subject=title,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[dest],
            fail_silently=False,
        )

        logger.info("EMAIL_SENT to=%s subject=%s", dest, title)
        return (True, None)
    except Exception as e:
        logger.exception("EMAIL_SEND_FAILED to=%s subject=%s error=%s", dest, title, str(e))
        return (False, e)

def send_hemail(dest: str, title: str, body: str, nbody: str):
    try:
        send_mail(
            subject=title,
            html_message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[dest],
            fail_silently=False,
            message=nbody
        )

        logger.info("EMAIL_SENT to=%s subject=%s", dest, title)
        return (True, None)
    except Exception as e:
        logger.exception("EMAIL_SEND_FAILED to=%s subject=%s error=%s", dest, title, str(e))
        return (False, e)