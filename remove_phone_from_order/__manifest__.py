{
    "name": "Remove phone from order reports",
    "summary": """
        Remove phone number from widget, + make font for shipping address bigger.""",
    "author": "it-fact GmbH",
    "website": "https://github.com/OCA/odoo-pim",
    "category": "Uncategorized",
    "version": "19.0.1.0",
    "license": "OPL-1",
    "depends": [
        "sale",
        "stock_delivery",
        "account",
    ],
    "data": [
        "views/sale_report_templates.xml",
        "views/report_invoice.xml",
        "views/report_delivery_slip.xml",
        "views/ir_qweb_widget_templates.xml",
    ],
}
