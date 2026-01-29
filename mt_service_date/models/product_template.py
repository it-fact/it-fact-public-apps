from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    service_date_only_months = fields.Boolean(
        string="Service Date in Months",
        help=("If checked, only the month and year will be considered for service dates."),
    )
