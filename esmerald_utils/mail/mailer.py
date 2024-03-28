import os
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
import smtplib
from email.mime import multipart, text
from email.utils import formataddr
from typing import Optional, List, Union
import pydantic
from esmerald_utils.mail import exception
from esmerald_utils.mail import template_finder


class Mailer(template_finder.MailTemplate):
    attachments = []
    __slot__ = (
        "sender_email",
        "admin_password",
        "admin_email",
        "email_host",
        "email_server_port",
        "template_folder",
        "sender_brand_name",
        "use_google",
    )

    def __init__(
        self,
        sender_email: Optional[pydantic.EmailStr],
        admin_password: str,
        admin_email: str,
        email_host: str,
        email_server_port: int,
        template_folder: str = f"{os.getcwd()}'/template'",
        sender_brand_name: str | None = "noreply",
        use_google: Optional[bool] = True,
    ) -> None:
        super().__init__(template_folder)

        self.admin_password = admin_password
        self.admin_email = admin_email
        self.email_host = email_host
        self.email_server_port = email_server_port
        self.use_google = use_google
        self.sender_brand_name = sender_brand_name
        self.sender_email = sender_email

    def add_attachment(self, attachment_paths: List[str]) -> None:
        for attachment_path in attachment_paths:
            with open(attachment_path, "rb") as f:
                attachment = MIMEBase("application", "octet-stream")
                attachment.set_payload(f.read(1024 * 1024))
                encoders.encode_base64(attachment)
                attachment.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}",
                )
                self.attachments.append(attachment)

    def send_mail(
        self,
        subject: str,
        email: Union[List[pydantic.EmailStr], pydantic.EmailStr],
        body: Optional[str] = None,
        template_name: Optional[str] = None,
        context=None,
    ):
        message = multipart.MIMEMultipart()
        if isinstance(email, list):
            message["To"] = ", ".join(email)
        if isinstance(email, str):
            message["To"] = email
        from_email = self.sender_email
        message["Subject"] = subject
        message["From"] = formataddr((self.sender_brand_name, from_email))

        if template_name and self.template_folder:
            body_content = self.render(template_name, context)
            message.attach(text.MIMEText(body_content, "html"))
        elif body:
            body_content = body
            message.attach(text.MIMEText(body_content, "plain"))
        else:
            raise exception.InvalidEmailContentError("Email body content is required")
        if self.attachments:
            for attachment in self.attachments:
                message.attach(attachment)
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(
                host=self.email_host, port=self.email_server_port
            ) as smtp:
                smtp.starttls(context=context)
                smtp.login(
                    user=self.admin_email,
                    password=self.admin_password,
                )
                smtp.sendmail(self.admin_email, email, message.as_string())
        except Exception as e:
            raise exception.EmailSendingError(f"Could not connect to mail server {e}")
