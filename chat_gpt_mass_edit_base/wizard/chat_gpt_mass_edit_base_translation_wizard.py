import logging
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ChatGPTMassEditTranslate(models.TransientModel):
    _name = "gpt_wizard_translate"
    _inherit = ["gpt_wizard"]
    _description = "Create Mass Edits of ChatGPT promts"

    def _default_gpt_question_template(self):
        return f"""{{{self.gpt_field_to_map_answer.name}}}"""

    type_of_prompt = fields.Selection(
        selection_add=[
            ("translation", "Translation"),
        ],
        default="translation",
    )

    gpt_field_to_map_answer = fields.Many2one(
        "ir.model.fields",
        domain="""[('model_id', '=', res_model_id),
        ('ttype', 'in', ('char', 'text')),
        ('store', '=', True),
        ('translate', '=', True),
        ]""",
    )

    gpt_question_template = fields.Text(default=False)  # _default_gpt_question_template,

    # pylint: disable=W8110
    @api.depends(
        "gpt_question_template",
        "lang",
        "gpt_field_to_map_answer.name",
        "dynamic_chat_gpt_info",
    )
    def _compute_gpt_question_wizard(self):
        super()._compute_gpt_question_wizard()  # pylint: disable=W8110
        for record in self:
            if not record.gpt_question_template:
                record.gpt_question_template = self._default_gpt_question_template()
                record.gpt_question_template += (
                    "\nAnswer only with the translated text "
                    "if there is markup keep it but do not add any other markup."
                )
                if record.dynamic_chat_gpt_info:
                    record.gpt_question_template += "Additional info {record.dynamic_chat_gpt_info}"

            if record.type_of_prompt == "translation":
                record.error_message = ""
                if record._transient:
                    if record.gpt_question_template:
                        placeholders = re.findall(r"{(\w+)}", record.gpt_question_template)
                        result = f"create a translation to the language {record.lang} for the following text:\n"
                        result += record.gpt_question_template

                        for placeholder in placeholders:
                            record_model = self.env[record.res_model_id.model].browse(
                                record.sample_product_template_id
                            )
                            try:
                                if replace_with := getattr(record_model, placeholder):
                                    result = result.replace(f"{{{placeholder}}}", replace_with)
                                else:
                                    continue
                            except AttributeError:
                                result = result.replace(f"{{{placeholder}}}", "False")
                                record.error_message += (
                                    f"Field: {placeholder} not found in model: {record.res_model_id.model}\n"
                                )
                            except Exception as e:
                                _logger.warning(e)
                        record.gpt_question = result
                    else:
                        record.gpt_question = False

    def get_results_from_gpt_wizard_translate(self):
        if not self.lang:
            raise UserError(_("Please select a target language"))
        for record_wizard in self:
            answer = record_wizard._get_chatgpt_response(record_wizard.gpt_question)
            if record_wizard.gpt_field_to_map_answer:
                record_model = self.env[record_wizard.res_model_id.model].browse(
                    record_wizard.sample_product_template_id
                )
                # setattr(record_model, record.gpt_field_to_map_answer.name, answer)

                field_name = record_wizard.gpt_field_to_map_answer.name
                lang = record_wizard.lang
                new_content = answer

                field = record_model._fields[field_name]
                translations = field._get_stored_translations(record_model)
                translations[lang] = new_content

                record_model.env.cache.update_raw(record_model, field, [translations], dirty=True)
                record_model.modified([field_name])
