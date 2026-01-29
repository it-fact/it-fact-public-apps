from datetime import date

from odoo.tests.common import TransactionCase


class TestAccountMove(TransactionCase):
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
        cls.sales_journal = cls.env["account.journal"].create(
            {
                "name": "Test Sales Journal",
                "code": "TSALE",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )

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

        cls.product_consu = cls.env["product.product"].create(
            {
                "name": "Consumable Product",
                "type": "consu",
                "list_price": 50.0,
            }
        )

    def _create_invoice(self, partner=None, invoice_lines=None):
        """Helper method to create invoice with lines"""
        if partner is None:
            partner = self.partner

        invoice_vals = {
            "partner_id": partner.id,
            "move_type": "out_invoice",
            "journal_id": self.sales_journal.id,
            "currency_id": self.currency.id,
        }

        if invoice_lines:
            invoice_vals["invoice_line_ids"] = [(0, 0, line) for line in invoice_lines]

        return self.env["account.move"].create(invoice_vals)

    def test_service_date_single_line_same_dates(self):
        """Test invoice with single line having same start and end dates"""
        invoice_lines = [
            {
                "product_id": self.product_service.id,
                "quantity": 1,
                "price_unit": 100.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            }
        ]

        invoice = self._create_invoice(invoice_lines=invoice_lines)

        self.assertFalse(invoice.mixed_service_dates)
        # Check for date format - could be YYYY-MM-DD or MM/DD/YYYY
        self.assertTrue(
            "01/01/2024" in invoice.service_date_invoice_text or "2024-01-01" in invoice.service_date_invoice_text
        )
        self.assertTrue(
            "01/31/2024" in invoice.service_date_invoice_text or "2024-01-31" in invoice.service_date_invoice_text
        )

    def test_service_date_multiple_lines_same_dates(self):
        """Test invoice with multiple lines having same start and end dates"""
        invoice_lines = [
            {
                "product_id": self.product_service.id,
                "quantity": 1,
                "price_unit": 100.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            },
            {
                "product_id": self.product_service.id,
                "quantity": 2,
                "price_unit": 150.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            },
        ]

        invoice = self._create_invoice(invoice_lines=invoice_lines)

        self.assertFalse(invoice.mixed_service_dates)
        # Check for date format - could be YYYY-MM-DD or MM/DD/YYYY
        self.assertTrue(
            "01/01/2024" in invoice.service_date_invoice_text or "2024-01-01" in invoice.service_date_invoice_text
        )
        self.assertTrue(
            "01/31/2024" in invoice.service_date_invoice_text or "2024-01-31" in invoice.service_date_invoice_text
        )

    def test_service_date_multiple_lines_different_dates(self):
        """Test invoice with multiple lines having different start and end dates"""
        invoice_lines = [
            {
                "product_id": self.product_service.id,
                "quantity": 1,
                "price_unit": 100.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            },
            {
                "product_id": self.product_service.id,
                "quantity": 2,
                "price_unit": 150.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 2, 1),
                "end_date": date(2024, 2, 28),
            },
        ]

        invoice = self._create_invoice(invoice_lines=invoice_lines)

        self.assertTrue(invoice.mixed_service_dates)
        self.assertEqual(invoice.service_date_invoice_text, "various service dates")

    def test_service_date_mixed_product_types(self):
        """Test invoice with mixed product types (service and consumable)"""
        invoice_lines = [
            {
                "product_id": self.product_service.id,
                "quantity": 1,
                "price_unit": 100.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            },
            {
                "product_id": self.product_consu.id,
                "quantity": 2,
                "price_unit": 50.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            },
        ]

        invoice = self._create_invoice(invoice_lines=invoice_lines)

        self.assertTrue(invoice.mixed_service_dates)
        self.assertEqual(invoice.service_date_invoice_text, "various service dates")

    def test_service_date_no_lines(self):
        """Test invoice with no lines"""
        invoice = self._create_invoice()

        self.assertFalse(invoice.mixed_service_dates)
        self.assertEqual(invoice.service_date_invoice_text, "")

    def test_service_date_refresh_trigger(self):
        """Test that changing refresh field triggers recomputation"""
        invoice_lines = [
            {
                "product_id": self.product_service.id,
                "quantity": 1,
                "price_unit": 100.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            }
        ]

        invoice = self._create_invoice(invoice_lines=invoice_lines)
        original_text = invoice.service_date_invoice_text

        # Trigger refresh
        invoice.refresh = not invoice.refresh

        # The computation should be triggered and result should be the same
        self.assertEqual(invoice.service_date_invoice_text, original_text)

    def test_service_date_line_dates_change(self):
        """Test that changing line dates updates invoice service date text"""
        invoice_lines = [
            {
                "product_id": self.product_service.id,
                "quantity": 1,
                "price_unit": 100.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 1, 31),
            }
        ]

        invoice = self._create_invoice(invoice_lines=invoice_lines)

        # Initially should not be mixed
        self.assertFalse(invoice.mixed_service_dates)

        # Add another line with different dates
        self.env["account.move.line"].create(
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

        # Should now be mixed
        self.assertTrue(invoice.mixed_service_dates)
        self.assertEqual(invoice.service_date_invoice_text, "various service dates")

    def test_service_date_with_months_only_product(self):
        """Test service date with product that uses months only"""
        invoice_lines = [
            {
                "product_id": self.product_service_months_only.id,
                "quantity": 1,
                "price_unit": 150.0,
                "account_id": self.account_revenue.id,
                "start_date": date(2024, 1, 15),
                "end_date": date(2024, 1, 25),
            }
        ]

        invoice = self._create_invoice(invoice_lines=invoice_lines)

        self.assertFalse(invoice.mixed_service_dates)
        # Should contain month and year format
        self.assertIn("January 2024", invoice.service_date_invoice_text)

    def test_service_date_empty_dates(self):
        """Test invoice with lines that have no start/end dates"""
        invoice_lines = [
            {
                "product_id": self.product_service.id,
                "quantity": 1,
                "price_unit": 100.0,
                "account_id": self.account_revenue.id,
                # No start_date and end_date
            }
        ]

        invoice = self._create_invoice(invoice_lines=invoice_lines)

        self.assertFalse(invoice.mixed_service_dates)
        self.assertEqual(invoice.service_date_invoice_text, "like invoice date")
