{
    "name": "Remove Phone from Order Reports",
    "summary": "Hide phone numbers in sale, invoice, and delivery report address blocks.",
    "author": "it-fact GmbH",
    "website": "https://www.it-fact.com",
    "category": "Sales",
    "version": "19.0.1.5",
    "price": "20.00",
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
    "images": [
        "static/img/banner.png",
        "static/img/report_address_without_phone.png",
    ],
}
