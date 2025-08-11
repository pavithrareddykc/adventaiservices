import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable, Optional


class MailSendError(Exception):
    pass


def _send_via_smtp(sender: str, recipients: Iterable[str], subject: str, body_text: str, reply_to: Optional[str] = None, from_override: Optional[str] = None) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    if not smtp_host:
        raise MailSendError("SMTP_HOST is not configured")

    message = MIMEMultipart()
    display_from = from_override or sender
    message["From"] = display_from
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    if reply_to:
        message["Reply-To"] = reply_to
    message.attach(MIMEText(body_text, "plain"))

    envelope_from = display_from  # use visible From as envelope from when overridden
    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
        if use_tls:
            server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.sendmail(envelope_from, list(recipients), message.as_string())


def send_email(recipients: Iterable[str], subject: str, body_text: str, reply_to: Optional[str] = None, from_override: Optional[str] = None) -> None:
    """
    Send an email to recipients. Uses SMTP when configured, otherwise logs to stdout.
    Required env vars for SMTP: SMTP_HOST (and optionally SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_USE_TLS).
    MAIL_FROM must be set as default sender address.
    If ALLOW_SUBMITTER_AS_FROM is true and from_override is provided, it will be used as the visible From (and envelope from).
    Reply-To is added when provided.
    """
    sender = os.getenv("MAIL_FROM")
    if not sender and not from_override:
        raise MailSendError("MAIL_FROM is not configured")

    recipients = [r.strip() for r in recipients if r and r.strip()]
    if not recipients:
        raise MailSendError("No recipients specified")

    allow_override = os.getenv("ALLOW_SUBMITTER_AS_FROM", "false").lower() in {"1", "true", "yes"}
    effective_from_override = from_override if allow_override and from_override else None

    if os.getenv("SMTP_HOST"):
        _send_via_smtp(sender or effective_from_override or "", recipients, subject, body_text, reply_to=reply_to, from_override=effective_from_override)
    else:
        # Fallback: print to stdout (useful for local/dev)
        print("=== EMAIL (dev fallback) ===")
        print(f"From: {effective_from_override or sender}")
        print(f"To: {', '.join(recipients)}")
        if reply_to:
            print(f"Reply-To: {reply_to}")
        print(f"Subject: {subject}")
        print("")
        print(body_text)
        print("=== END EMAIL ===")