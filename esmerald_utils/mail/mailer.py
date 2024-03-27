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
    __slot__ = (
        "subject",
        "sender_email",
        "admin_password",
        "admin_email",
        "email_host",
        "email_server_port",
        "template_folder",
        "sender_brand_name",
        "use_google",
        "body",
        "template_name",
        "context",
    )

    def __init__(
        self,
        subject: str,
        sender_email: Optional[pydantic.EmailStr],
        admin_password: str,
        admin_email: str,
        email_host: str,
        email_server_port: int,
        template_folder: str = f"{os.getcwd()}'/template'",
        sender_brand_name: str | None = "noreply",
        use_google: Optional[bool] = True,
        body: Optional[str] = None,
        template_name: Optional[str] = None,
        context=None,
    ) -> None:
        super().__init__(template_folder)
        if context is None:
            context = {}
        self.admin_password = admin_password
        self.admin_email = admin_email
        self.template_name = template_name
        self.email_host = email_host
        self.email_server_port = email_server_port
        self.use_google = use_google
        self.sender_brand_name = sender_brand_name
        self.sender_email = sender_email
        self.body = body
        self.context = context
        self.subject = subject
        self.attachments = []

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
        email: Union[List[pydantic.EmailStr], pydantic.EmailStr],
    ):
        message = multipart.MIMEMultipart()
        if isinstance(email, list):
            message["To"] = ", ".join(email)
        if isinstance(email, str):
            message["To"] = email
        from_email = self.sender_email
        subject: str = self.subject
        message["Subject"] = subject
        message["From"] = formataddr((self.sender_brand_name, from_email))

        if self.template_name and self.template_folder:
            body_content = self.render(self.template_name, self.context)
            message.attach(text.MIMEText(body_content, "html"))
        elif self.body:
            body_content = self.body
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
                smtp.sendmail(from_email, email, message.as_string())
        except Exception as e:
            raise exception.EmailSendingError(f"Could not connect to mail server {e}")
