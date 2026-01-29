import logging

from odoo import fields, models

from .chat_gpt_mixin_base import ChatGPTMixinBase

_logger = logging.getLogger(__name__)


class ChatGPT(ChatGPTMixinBase, models.Model):
    _name = "chat_gpt_mass_edit_base.mixin"
    _description = "Description"

    gpt_question_template = fields.Text(
        string="GPT Question Template",
        help=("This is the template for your chat gpt question, ", "add field names in this model with {{title}}"),
    )
    gpt_question = fields.Text(compute="_compute_gpt_question_model", string="GPT Question", store=True)

    gpt_answer = fields.Text(string="GPT Answer")

    res_model_id = fields.Many2one("ir.model", string="Model", compute="_compute_res_model_id", readonly=True)

    gpt_field_to_map_answer = fields.Many2one(
        "ir.model.fields",
        string="Field to map answer",
        domain="""[('model_id', '=', res_model_id),
        ('ttype', 'in', ('char', 'text')),
        ('store', '=', True)]""",
    )

    json_extra_info = fields.Char(help="This info is added to any json block")

    def open_chat_gpt_wizard(self):
        model_id = self.env["ir.model"].search([("model", "=", self._name)], limit=1)
        image_field_id = (
            self.env["ir.model.fields"]
            .search([("model_id", "=", model_id.id), ("name", "=", "image_256")], limit=1)
            .id
        )
        IDS = [str(id) for id in self.ids]
        return {
            "type": "ir.actions.act_window",
            "res_model": "gpt_wizard",
            "view_mode": "form",
            "target": "new",  # Opens the wizard as a popup
            "context": {
                "default_gpt_field_for_input_image": image_field_id,
                "default_current_lang": self.env.lang,
                "default_sample_product_template_id": self.ids[0],
                "default_res_model_IDS": ",".join(IDS),
                "default_records_effected": len(self),
                "default_res_model_id": model_id.id,
                "default_gpt_field_to_map_answer": self.env["ir.model.fields"]
                .search(
                    [
                        ("model_id", "=", model_id.id),
                        ("name", "=", "description_ecommerce"),
                    ],
                    limit=1,
                )
                .id,
            },
        }

    def open_chat_gpt_wizard_translate(self):
        model_id = self.env["ir.model"].search([("model", "=", self._name)], limit=1)
        image_field_id = (
            self.env["ir.model.fields"]
            .search([("model_id", "=", model_id.id), ("name", "=", "image_256")], limit=1)
            .id
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "gpt_wizard_translate",
            "view_mode": "form",
            "target": "new",  # Opens the wizard as a popup
            "context": {
                "default_gpt_field_for_input_image": image_field_id,
                "default_current_lang": self.env.lang,
                "default_sample_product_template_id": self.ids[0],
                "default_res_model_IDS": ",".join([str(id) for id in self.ids]),
                "default_records_effected": len(self),
                "default_res_model_id": model_id.id,
                "default_gpt_field_to_map_answer": self.env["ir.model.fields"]
                .search(
                    [
                        ("model_id", "=", model_id.id),
                        ("name", "=", "description_ecommerce"),
                    ],
                    limit=1,
                )
                .id,
            },
        }

    def _compute_res_model_id(self):
        for record in self:
            record.res_model_id = self.env["ir.model"].search([("model", "=", record._name)])

    # There are more methods in chat_gpt_mixin_base. These are shared with the transient model for the wizard.
    # To avoid code duplication the methods are in the extra mixin file.
