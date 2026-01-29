import logging

from odoo import _, api, fields, models
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    refresh = fields.Boolean()

    # these fields are from module: accountant
    # it's not a hard dependency, but if the module is installed,
    # we want use all the features

    deferred_start_date = fields.Date()
    deferred_end_date = fields.Date()

    # alternatively the start and end field of OCA account_invoice_start_end_dates
    # can be used but are also not a hard requirement
    start_date = fields.Date()
    end_date = fields.Date()

    service_date_invoice_text = fields.Text(
        string="Service Date", compute="_compute_service_date_invoice_text", store=True
    )
    service_date_show_on_lines = fields.Boolean(compute="_compute_service_date_show_on_lines", store=True)

    def _compute_service_date_show_on_lines(self):
        # If the invoice has mixed service dates, we show the service date on each line
        # otherwise we only show it on the invoice header
        for line in self:
            line.service_date_show_on_lines = line.move_id.mixed_service_dates

    def format_with_only_months(self, line, start, end):
        start_date = format_date(self.env, start, date_format="MMM YY")
        end_date = format_date(self.env, end, date_format="MMM YY")
        if start_date == end_date:
            return start_date
        else:
            return self.env._(
                "%(start_date)s to %(end_date)s",
                start_date=start_date,
                end_date=end_date,
            )

    def create_string_from_both_dates(self, line):
        start_date = line.deferred_start_date or line.start_date
        end_date = line.deferred_end_date or line.end_date
        if start_date == end_date:
            return format_date(self.env, start_date)
        if line.product_id.service_date_only_months:
            return self.format_with_only_months(line, start_date, end_date)
        return _(
            "%(start_date_formatted)s to %(end_date_formatted)s",
            start_date_formatted=format_date(self.env, start_date),
            end_date_formatted=format_date(self.env, end_date),
        )

    @api.depends(
        "start_date",
        "end_date",
        "product_id",
        "deferred_start_date",
        "deferred_end_date",
        "move_id.invoice_date",
        "move_id.delivery_date",
        "refresh",
        "product_id.service_date_only_months",
    )
    def _compute_service_date_invoice_text(self):
        for line in self:
            line.service_date_invoice_text = ""
            start_date = line.deferred_start_date or line.start_date
            end_date = line.deferred_end_date or line.end_date
            invoice_date_formatted = self.env._("like invoice date")
            if line.move_id.invoice_date:
                invoice_date_formatted = format_date(self.env, line.move_id.invoice_date) or ""
            # 1) If it's a product and the service date is not set,
            # we use the delivery date from the header
            if line.product_id.type == "consu" and not start_date and line.move_id.delivery_date:
                line.service_date_invoice_text = format_date(self.env, line.move_id.delivery_date) or ""
            # 2) If no service date is set, we use "like invoice date"
            elif not start_date and not end_date:
                line.service_date_invoice_text = invoice_date_formatted
            # 3) If date range is set we format it accordingly
            elif start_date and end_date:
                res = self.create_string_from_both_dates(line)
                line.service_date_invoice_text = res
            # 4) If only start date is set, we use the start date
            # this is not possible but just in case
            elif start_date:
                line.service_date_invoice_text = format_date(self.env, start_date) or ""
            # 5) If there is no delivery date and no start end date on the position,AccountMoveLine
            # we use the invoice date
            elif not line.service_date_invoice_text:
                line.service_date_invoice_text = invoice_date_formatted
            # 4) Warn if ther is unexpected behavior
            else:
                _logger.warning("There is an unexpected case in service date formatting.")
                line.service_date_invoice_text = ""
