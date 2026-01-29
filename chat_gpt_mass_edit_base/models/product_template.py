from odoo import models


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "chat_gpt_mass_edit_base.mixin"]
