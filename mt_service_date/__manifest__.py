{
    "name": "service date",
    "summary": """
        Allows to specify service start and end dates on invoices
        and print them on the invoice PDF. With this module
        austrian and german legal requirements can be fulfilled.""",
    "author": "mytime.click",
    "website": "https://github.com/OCA/partner-contact",
    "category": "Uncategorized",
    "version": "19.0.1.2",
    "price": 79.99,
    "license": "OPL-1",
    "depends": [
        "product",
        "account",
    ],  # "account_invoice_start_end_dates",
    "data": [
        "reports/report_invoice.xml",
        "views/account_move_views.xml",
        "views/product_template_views.xml",
    ],
}
