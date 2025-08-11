import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable


class MailSendError(Exception):
    pass


def _send_via_smtp(sender: str, recipients: Iterable[str], subject: str, body_text: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    if not smtp_host:
        raise MailSendError("SMTP_HOST is not configured")

    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.attach(MIMEText(body_text, "plain"))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
        if use_tls:
            server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.sendmail(sender, list(recipients), message.as_string())


def send_email(recipients: Iterable[str], subject: str, body_text: str) -> None:
    """
    Send an email to recipients. Uses SMTP when configured, otherwise logs to stdout.
    Required env vars for SMTP: SMTP_HOST (and optionally SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_USE_TLS).
    MAIL_FROM must be set as sender address.
    """
    sender = os.getenv("MAIL_FROM")
    if not sender:
        raise MailSendError("MAIL_FROM is not configured")

    recipients = [r.strip() for r in recipients if r and r.strip()]
    if not recipients:
        raise MailSendError("No recipients specified")

    if os.getenv("SMTP_HOST"):
        _send_via_smtp(sender, recipients, subject, body_text)
    else:
        # Fallback: print to stdout (useful for local/dev)
        print("=== EMAIL (dev fallback) ===")
        print(f"From: {sender}")
        print(f"To: {', '.join(recipients)}")
        print(f"Subject: {subject}")
        print("")
        print(body_text)
        print("=== END EMAIL ===")