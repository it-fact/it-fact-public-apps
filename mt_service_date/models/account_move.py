from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    service_date_invoice_text = fields.Text(string="Service Date", compute="_compute_service_date_invoice_text")
    mixed_service_dates = fields.Boolean(compute="_compute_service_date_invoice_text")
    refresh = fields.Boolean()

    @api.depends(
        "invoice_line_ids.service_date_invoice_text",
        "invoice_line_ids.product_id.type",
        "refresh",
        "invoice_date",
        "delivery_date",
    )
    def _compute_service_date_invoice_text(self):  # NOSONAR
        for record in self:
            record.mixed_service_dates = False
            record.service_date_invoice_text = ""
            first_line_id = record.invoice_line_ids[:1]
            if not first_line_id:
                continue
            record.service_date_invoice_text = first_line_id.service_date_invoice_text
            for line_id in record.invoice_line_ids[1:]:
                if (
                    line_id.service_date_invoice_text != first_line_id.service_date_invoice_text
                    or line_id.product_id.type != first_line_id.product_id.type
                ):
                    record.mixed_service_dates = True
                    record.service_date_invoice_text = _("various service dates")
                    break
