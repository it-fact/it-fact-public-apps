from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAccountMoveLine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test company and currency
        cls.company = cls.env.ref("base.main_company")
        cls.currency = cls.env.ref("base.EUR")

        # Create test accounts
        cls.account_receivable = cls.env["account.account"].create(
            {
                "name": "Test Receivable",
                "code": "RECV001",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )

        cls.account_revenue = cls.env["account.account"].create(
            {
                "name": "Test Revenue",
                "code": "REV001",
                "account_type": "income",
            }
        )

        # Create sales journal
        journal_vals = {
            "name": "Test Sales Journal",
            "code": "TSALE",
            "type": "sale",
            "company_id": cls.company.id,
        }
        if "nacha_entry_class_code" in cls.env["account.journal"]._fields:
            journal_vals["nacha_entry_class_code"] = "CCD"
        cls.sales_journal = cls.env["account.journal"].create(journal_vals)

        # Create test partner
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "customer_rank": 1,
                "property_account_receivable_id": cls.account_receivable.id,
            }
        )

        # Create test products
        cls.product_service = cls.env["product.product"].create(
            {
                "name": "Service Product",
                "type": "service",
                "list_price": 100.0,
            }
        )

        cls.product_service_months_only = cls.env["product.product"].create(
            {
                "name": "Service Product (Months Only)",
                "type": "service",
                "list_price": 150.0,
                "service_date_only_months": True,
            }
        )

    def _create_invoice_with_line(self, start_date=None, end_date=None, product=None):
        """Helper method to create invoice with a single line"""
        if product is None:
            product = self.product_service

        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "move_type": "out_invoice",
                "journal_id": self.sales_journal.id,
                "currency_id": self.currency.id,
            }
        )

        line_vals = {
            "move_id": invoice.id,
            "product_id": product.id,
            "quantity": 1,
            "price_unit": 100.0,
            "account_id": self.account_revenue.id,
        }

        if start_date is not None:
            line_vals["start_date"] = start_date
        if end_date is not None:
            line_vals["end_date"] = end_date

        line = self.env["account.move.line"].create(line_vals)
        return invoice, line

    def test_service_date_text_no_dates(self):
        """Test service date text when no start/end dates are set"""
        _, line = self._create_invoice_with_line()

        self.assertEqual(line.service_date_invoice_text, "like invoice date")

    def test_service_date_text_same_start_end_date(self):
        """Test service date text when start and end dates are the same"""
        test_date = date(2024, 1, 15)
        _, line = self._create_invoice_with_line(start_date=test_date, end_date=test_date)

        self.assertTrue(
            "01/15/2024" in line.service_date_invoice_text or "2024-01-15" in line.service_date_invoice_text
        )

    def test_service_date_text_different_dates_normal_product(self):
        """Test service date text with different start/end dates for normal product"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        _, line = self._create_invoice_with_line(start_date=start_date, end_date=end_date)

        # Check for date format - could be YYYY-MM-DD or MM/DD/YYYY
        self.assertTrue(
            "01/01/2024" in line.service_date_invoice_text or "2024-01-01" in line.service_date_invoice_text
        )
        self.assertTrue(
            "01/31/2024" in line.service_date_invoice_text or "2024-01-31" in line.service_date_invoice_text
        )
        self.assertIn("to", line.service_date_invoice_text)

    def test_service_date_text_different_dates_months_only_same_month(self):
        """Test service date text with months only product in same month"""
        start_date = date(2024, 1, 5)
        end_date = date(2024, 1, 25)
        _, line = self._create_invoice_with_line(
            start_date=start_date, end_date=end_date, product=self.product_service_months_only
        )

        # Should show only "January 2024" since both dates are in same month
        self.assertEqual(line.service_date_invoice_text, "January 2024")

    def test_service_date_text_different_dates_months_only_different_months(self):
        """Test service date text with months only product across different months"""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 3, 15)
        _, line = self._create_invoice_with_line(
            start_date=start_date, end_date=end_date, product=self.product_service_months_only
        )

        # Should show "January 2024 to March 2024"
        self.assertIn("January 2024", line.service_date_invoice_text)
        self.assertIn("March 2024", line.service_date_invoice_text)
        self.assertIn("to", line.service_date_invoice_text)

    def test_service_date_text_partial_dates_validation(self):
        """Test that validation prevents creating lines with only start or end date"""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 15)

        # Test that we can't create a line with only start date
        with self.assertRaises(ValidationError):
            self._create_invoice_with_line(start_date=start_date)

        # Test that we can't create a line with only end date
        with self.assertRaises(ValidationError):
            self._create_invoice_with_line(end_date=end_date)

    def test_service_date_show_on_lines_not_mixed(self):
        """Test that service_date_show_on_lines is False when invoice doesn't have mixed dates"""
        # Create invoice with single line
        _, line = self._create_invoice_with_line(start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))

        # Should not show on lines since invoice doesn't have mixed service dates
        self.assertFalse(line.service_date_show_on_lines)

    def test_service_date_show_on_lines_mixed(self):
        """Test that service_date_show_on_lines is True when invoice has mixed dates"""
        # Create invoice with multiple lines having different dates
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "move_type": "out_invoice",
                "journal_id": self.sales_journal.id,
                "currency_id": self.currency.id,
            }
        )

        # First line
        line1 = self.env["account.move.line"].create(
            {
                "move_id": invoice.id,
                "product_id": self.product_service.id,
                "quantity": 1,
                "price_unit": 100.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            }
        )

        # Second line with different dates
        line2 = self.env["account.move.line"].create(
            {
                "move_id": invoice.id,
                "product_id": self.product_service.id,
                "quantity": 1,
                "price_unit": 100.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 2, 1),
                "end_date": date(2024, 2, 28),
            }
        )

        # Should show on lines since invoice has mixed service dates
        self.assertTrue(line1.service_date_show_on_lines)
        self.assertTrue(line2.service_date_show_on_lines)

    def test_refresh_field_triggers_recomputation(self):
        """Test that changing refresh field triggers recomputation"""
        _, line = self._create_invoice_with_line(start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))

        original_text = line.service_date_invoice_text

        # Trigger refresh
        line.refresh = not line.refresh

        # The computation should be triggered and result should be the same
        self.assertEqual(line.service_date_invoice_text, original_text)

    def test_format_with_only_months_helper_method(self):
        """Test the format_with_only_months helper method directly"""
        start_date = date(2024, 1, 5)
        end_date = date(2024, 3, 25)
        _, line = self._create_invoice_with_line(
            start_date=start_date, end_date=end_date, product=self.product_service_months_only
        )

        # Call the helper method directly
        line.format_with_only_months(line)

        self.assertIn("January 2024", line.service_date_invoice_text)
        self.assertIn("March 2024", line.service_date_invoice_text)
        self.assertIn("to", line.service_date_invoice_text)

    def test_format_with_only_months_same_month_helper(self):
        """Test the format_with_only_months helper method with same month"""
        start_date = date(2024, 1, 5)
        end_date = date(2024, 1, 25)
        _, line = self._create_invoice_with_line(
            start_date=start_date, end_date=end_date, product=self.product_service_months_only
        )

        # Call the helper method directly
        line.format_with_only_months(line)

        self.assertEqual(line.service_date_invoice_text, "January 2024")

    def test_service_date_dependencies(self):
        """Test that all dependencies for computed fields are correct"""
        _, line = self._create_invoice_with_line(start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))

        original_text = line.service_date_invoice_text

        # Change both dates together to avoid validation issues
        line.write({"start_date": date(2024, 2, 1), "end_date": date(2024, 2, 28)})
        self.assertNotEqual(line.service_date_invoice_text, original_text)

        # Change to different dates - should trigger recomputation again
        line.write({"start_date": date(2024, 3, 1), "end_date": date(2024, 3, 31)})
        # The text should be different from original
        self.assertNotEqual(line.service_date_invoice_text, original_text)

    def test_product_service_date_only_months_dependency(self):
        """Test that product.service_date_only_months affects computation"""
        start_date = date(2024, 1, 5)
        end_date = date(2024, 1, 25)

        # First test with normal product
        _, line1 = self._create_invoice_with_line(
            start_date=start_date, end_date=end_date, product=self.product_service
        )

        # Then test with months-only product
        _, line2 = self._create_invoice_with_line(
            start_date=start_date, end_date=end_date, product=self.product_service_months_only
        )

        # Should have different formats
        self.assertNotEqual(line1.service_date_invoice_text, line2.service_date_invoice_text)
        # Check for date format - could be YYYY-MM-DD or MM/DD/YYYY
        self.assertTrue(
            "01/05/2024" in line1.service_date_invoice_text or "2024-01-05" in line1.service_date_invoice_text
        )  # Full date format
        self.assertIn("January 2024", line2.service_date_invoice_text)  # Month format

    def test_cross_year_months_only_format(self):
        """Test months only format across different years"""
        start_date = date(2024, 12, 15)
        end_date = date(2025, 2, 15)
        _, line = self._create_invoice_with_line(
            start_date=start_date, end_date=end_date, product=self.product_service_months_only
        )

        self.assertIn("December 2024", line.service_date_invoice_text)
        self.assertIn("February 2025", line.service_date_invoice_text)
        self.assertIn("to", line.service_date_invoice_text)
