"""
Servicio de Email SMTP.
Portado desde: container garzon_pedidos → app.py (enviar_email_smtp)
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger(__name__)


def enviar_email(
    destinatario: str,
    copia_oculta: list[str],
    asunto: str,
    cuerpo: str,
    smtp_password: str
) -> dict:
    """Envía email vía Gmail SMTP con App Password."""
    remitente = settings.smtp_email
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, smtp_password)
        destinatarios = [destinatario] + copia_oculta + [remitente]
        server.sendmail(remitente, destinatarios, msg.as_string())
        server.quit()
        logger.info(f"Email enviado a {destinatario}")
        return {"success": True, "message": "Email enviado correctamente"}
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return {"success": False, "message": str(e)}
