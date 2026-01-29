from odoo import models


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "chat_gpt_mass_edit_base.mixin"]
