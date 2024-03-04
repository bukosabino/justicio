import logging as lg
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, Email, Mail, To

from src.initialize import initialize_logging

initialize_logging()


def send_email(config_loader, subject: str, content: str) -> None:
    logger = lg.getLogger(send_email.__name__)
    logger.info("Sending email")
    sg = SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email(config_loader["admin_email"])
    to_email = To(config_loader["admin_email"])
    content = Content("text/plain", content)
    mail = Mail(from_email, to_email, subject, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    logger.info("Sent email with status %s", response)
