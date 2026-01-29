import asyncio
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MailTemplate(models.Model):
    _name = "mail.template"
    _inherit = ["mail.template", "chat_gpt_mass_edit_base.mixin"]

    def translate_template(self):
        self.ensure_one()
        for record in self:
            asyncio.run(
                self.env["auto.translate.google.service"].async_translate_field_to_all_or_certain_language(
                    record, "body_html", source_field="body_html"
                )
            )
