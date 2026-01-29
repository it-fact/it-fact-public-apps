from odoo import fields, models

from .chat_gpt_mixin_base import ChatGPTMixinBase

DEFAULT_LIBRARY_ENDPOINT = "https://media-api.odoo.com"
DEFAULT_OLG_ENDPOINT = "https://olg.api.odoo.com"


class ChatGPT(ChatGPTMixinBase, models.TransientModel):
    _name = "chat_gpt_mass_edit_base.transient.mixin"
    _description = "Description"

    gpt_question_template = fields.Text(
        string="GPT Question Template",
        default=("create a description in german for the field {name} with about 50 words"),
        help=("This is the template for your chat gpt question, ", "add field names in this model with {{title}}"),
    )
    gpt_extra_template = fields.Text(
        help=(
            "Holds extra information which get's added to the gpt prompt. "
            "It's separated to have a clear focus on the question."
        )
    )
    gpt_question = fields.Text(compute="_compute_gpt_question_wizard", string="GPT Question", store=True)
    records_effected = fields.Integer(readonly=True)
    gpt_answer = fields.Text(string="GPT Answer")
    res_model_id = fields.Many2one("ir.model", string="Model", readonly=True)
    res_model_IDS = fields.Char()
    sample_product_template_id = fields.Integer()
    dynamic_chat_gpt_info = fields.Char()

    gpt_field_for_input_image = fields.Many2one(
        "ir.model.fields",
        string="Field to map answer",
        domain="""[('model_id', '=', res_model_id),
        ('ttype', '=', 'binary'),
        ('store', '=', True)]""",
    )

    gpt_field_to_map_answer = fields.Many2one(
        "ir.model.fields",
        string="Field to map answer",
        domain="""[('model_id', '=', res_model_id),
        ('ttype', 'in', ('char', 'text')),
        ('store', '=', True)]""",
    )

    gpt_field_to_map_image = fields.Many2one(
        "ir.model.fields",
        string="Image export to",
        domain="""[('model_id', '=', res_model_id),
        ('ttype', '=', 'binary'),
        ('store', '=', True),
        ('readonly', '=', False)
        ]

        """,
        compute="_compute_gpt_field_to_map_image",
    )

    json_extra_info = fields.Char(help="This info is added to any json block")

    # There are more methods in chat_gpt_mixin_base. These are shared with the transient model for the wizard.
    # To avoid code duplication the methods are in the extra mixin file.
