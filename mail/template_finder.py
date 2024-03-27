from pathlib import Path
from typing import Optional
import jinja2 as jj2
from jinja2.exceptions import TemplateNotFound
from mail.exception import (
    EmailTemplateNotFoundError,
)


class MailTemplate:
    def __init__(self, template_folder: Path = Path().cwd()) -> None:
        self.template = None
        try:
            self.template_folder = template_folder
            self.env: jj2.Environment = jj2.Environment(
                loader=jj2.FileSystemLoader(self.template_folder),
                autoescape=jj2.select_autoescape(),
            )
        except TemplateNotFound as e:
            raise EmailTemplateNotFoundError(
                f"Template not found in {self.template_folder}"
            ) from e

    def render(self, template_name: str, context: Optional[dict] = {}) -> str:
        self.template = self.env.get_template(template_name)
        return self.template.render(**context)
