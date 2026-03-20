from django.core.mail import send_mail
import logging
from django.conf import settings


logger = logging.getLogger("email.system")
#
#def send_email(dest: str, title: str, body: str):
#    context = ssl.create_default_context()
#    try:
#        with smtplib.SMTP(settings.SMTP_ENDPOINT, settings.SMTP_PORT) as server:
#
#        
#            server.ehlo()
#            server.starttls(context=context)
#            server.ehlo()
#            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
#        
#            message = """\
#Subject: {}
#{}
#            """.format(title, body)
#            server.sendmail(settings.SMTP_EMAIL, dest, message)
#            logger.info("EMAIL_SENT to=%s subject=%s", dest, title)
#        
#    except Exception as e:
#        logger.exception("EMAIL_SEND_FAILED to=%s subject=%s error=%s", dest, title, str(e))
#        return (False, e)
#    
#    return (True,)

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
        return (True,)
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
        return (True,)
    except Exception as e:
        logger.exception("EMAIL_SEND_FAILED to=%s subject=%s error=%s", dest, title, str(e))
        return (False, e)