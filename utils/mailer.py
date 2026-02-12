import smtplib
from email.message import EmailMessage
from config import mail_config as cfg

def send_new_pending_email(username, role=None):
    subject = f"Nouvelle demande en attente : {username}"
    body = (
        f"Une nouvelle demande d'inscription est en attente.\n\n"
        f"Utilisateur : {username}\n"
        f"Rôle demandé : {role or '—'}\n\n"
        "Connectez-vous au panneau d'administration pour approuver ou refuser la demande : /admin/pending"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.MAIL_DEFAULT_SENDER
    msg["To"] = ", ".join(cfg.MAIL_ADMIN_RECIPIENTS)
    msg.set_content(body)

    try:
        if cfg.MAIL_USE_SSL:
            with smtplib.SMTP_SSL(cfg.MAIL_SERVER, cfg.MAIL_PORT) as smtp:
                smtp.login(cfg.MAIL_USERNAME, cfg.MAIL_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(cfg.MAIL_SERVER, cfg.MAIL_PORT) as smtp:
                if cfg.MAIL_USE_TLS:
                    smtp.starttls()
                if cfg.MAIL_USERNAME and cfg.MAIL_PASSWORD:
                    smtp.login(cfg.MAIL_USERNAME, cfg.MAIL_PASSWORD)
                smtp.send_message(msg)
    except Exception as e:
        # Ne pas casser le flux principal : log minimal
        print("send_new_pending_email error:", e)
