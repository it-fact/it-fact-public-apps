from odoo import _, api, fields, models
from odoo.tools.misc import format_date


class AccountMove(models.Model):
    _inherit = "account.move"

    service_date_invoice_text = fields.Text(string="Service Date", compute="_compute_service_date_invoice_text")
    mixed_service_dates = fields.Boolean(compute="_compute_service_date_invoice_text")
    refresh = fields.Boolean()

    @api.depends(
        "line_ids.start_date",
        "line_ids.end_date",
        "refresh",
        "invoice_date",
        "delivery_date",
    )
    def _compute_service_date_invoice_text(self):  # NOSONAR
        for record in self:
            record.mixed_service_dates = False
            for _idx, move in enumerate(record.invoice_line_ids):
                if _idx == 0:
                    # For the first record, we initialize start and end
                    record.service_date_invoice_text = move.service_date_invoice_text
                elif record.service_date_invoice_text != move.service_date_invoice_text:
                    record.mixed_service_dates = True
                    record.service_date_invoice_text = _("see positions")
                    break
                else:
                    record.service_date_invoice_text = _("see positions")
            # if there are no positions:
            record.service_date_invoice_text = format_date(self.env, record.date) or ""
