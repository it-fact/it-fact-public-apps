import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ChatGPTMassEdit(models.TransientModel):
    _name = "gpt_wizard"
    _inherit = ["chat_gpt_mass_edit_base.transient.mixin", "gpt_wizard"]
    _description = "Create Mass Edits of ChatGPT promts"
