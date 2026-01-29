# Test Documentation for mt_service_date Module

This document describes the comprehensive test suite created for the `mt_service_date`
Odoo module.

## Test Files Created

### 1. `tests/test_account_move.py`

Tests for the `AccountMove` model that handles service date computation at the invoice
level.

### 2. `tests/test_account_move_line.py`

Tests for the `AccountMoveLine` model that handles service date computation at the
individual line level.

## Test Coverage

### AccountMove Model Tests (`test_account_move.py`)

#### Key Test Scenarios:

- **Single line with same dates**: Validates service date text when invoice has one line
- **Multiple lines with same dates**: Tests when all lines have identical service
  periods
- **Multiple lines with different dates**: Verifies "mixed service dates" detection
- **Mixed product types**: Tests behavior with service and consumable products combined
- **Empty invoices**: Handles invoices with no lines
- **Refresh field**: Tests that the refresh field triggers recomputation
- **Dynamic line changes**: Tests adding lines with different dates
- **Months-only products**: Tests service dates for products with
  `service_date_only_months=True`
- **Empty dates**: Tests lines without start/end dates

#### Test Methods:

1. `test_service_date_single_line_same_dates()`
2. `test_service_date_multiple_lines_same_dates()`
3. `test_service_date_multiple_lines_different_dates()`
4. `test_service_date_mixed_product_types()`
5. `test_service_date_no_lines()`
6. `test_service_date_refresh_trigger()`
7. `test_service_date_line_dates_change()`
8. `test_service_date_with_months_only_product()`
9. `test_service_date_empty_dates()`

### AccountMoveLine Model Tests (`test_account_move_line.py`)

#### Key Test Scenarios:

- **No dates**: Tests "like invoice date" fallback
- **Same start/end dates**: Tests single date display
- **Different dates (normal product)**: Tests date range formatting
- **Different dates (months-only product)**: Tests month-year formatting
- **Same month (months-only)**: Tests single month display
- **Partial dates**: Tests with only start or end date
- **Mixed service dates display**: Tests `service_date_show_on_lines` field
- **Refresh triggers**: Tests field dependency system
- **Helper methods**: Tests `format_with_only_months()` directly
- **Field dependencies**: Tests all computed field dependencies
- **Cross-year formatting**: Tests month formatting across years

#### Test Methods:

1. `test_service_date_text_no_dates()`
2. `test_service_date_text_same_start_end_date()`
3. `test_service_date_text_different_dates_normal_product()`
4. `test_service_date_text_different_dates_months_only_same_month()`
5. `test_service_date_text_different_dates_months_only_different_months()`
6. `test_service_date_text_only_start_date()`
7. `test_service_date_text_only_end_date()`
8. `test_service_date_show_on_lines_not_mixed()`
9. `test_service_date_show_on_lines_mixed()`
10. `test_refresh_field_triggers_recomputation()`
11. `test_format_with_only_months_helper_method()`
12. `test_format_with_only_months_same_month_helper()`
13. `test_service_date_dependencies()`
14. `test_product_service_date_only_months_dependency()`
15. `test_cross_year_months_only_format()`

## Test Data Setup

Both test classes use a comprehensive `setUpClass()` method that creates:

- Test company and currency (EUR)
- Test customer partner
- Regular service product
- Service product with `service_date_only_months=True`
- Consumable product for mixed-type testing
- Test income account for invoice lines

## Helper Methods

### `_create_invoice()` (in TestAccountMove)

Creates invoices with optional pre-configured line data.

### `_create_invoice_with_line()` (in TestAccountMoveLine)

Creates an invoice with a single line, allowing customization of dates and products.

## Running the Tests

### Using Odoo Test Framework

```bash
# Run all module tests
odoo-bin -d your_database -i mt_service_date --test-enable --stop-after-init

# Run specific test files
odoo-bin -d your_database --test-file=addons/mt_service_date/tests/test_account_move.py --test-enable --stop-after-init
```

### Using pytest (if configured)

```bash
pytest /path/to/mt_service_date/tests/
```

## Test Validation

The `test_runner.py` script validates that:

- Test classes can be imported correctly
- All test methods are properly named (start with `test_`)
- Test structure follows Odoo conventions

Run validation with:

```bash
python test_runner.py
```

## Business Logic Coverage

### Service Date Computation Logic

- ✅ Single invoice line handling
- ✅ Multiple invoice lines with same dates
- ✅ Multiple invoice lines with different dates
- ✅ Mixed product types detection
- ✅ Empty date handling
- ✅ Month-only formatting for specific products

### Field Dependencies

- ✅ `start_date` and `end_date` dependencies
- ✅ `refresh` field triggers
- ✅ `product_id.service_date_only_months` dependency
- ✅ `move_id.mixed_service_dates` relationship

### Edge Cases

- ✅ No service dates (fallback to invoice date)
- ✅ Same start and end dates
- ✅ Only start date or only end date
- ✅ Cross-year date ranges
- ✅ Same month date ranges

## Quality Assurance

The tests include:

- Comprehensive assertions for all computed fields
- Edge case handling validation
- Business logic verification
- Field dependency testing
- Helper method testing
- Integration testing between models

Each test is focused, well-documented, and follows Odoo testing best practices using
`TransactionCase` for database transactions.
