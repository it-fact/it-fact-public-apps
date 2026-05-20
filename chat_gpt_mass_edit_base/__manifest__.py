{
    "name": "Chat GPT (incl Image and Mass edit)",
    "summary": """
        Helps to mass edit products with Chat GPT.
        Images from Products and other fields can be also sent to chat GPT to analyse.
        GPT can also be used to create images from dynamic field information.""",
    "author": "mytime.click",
    "website": "https://apps.odoo.com/apps/modules/19.0/chat_gpt_mass_edit_base/",
    "category": "product",
    "version": "19.0.1.2",
    "license": "OPL-1",
    "depends": [
        "base",
        "base_setup",
        "product",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/chatgpt_model_data.xml",
        "views/res_config_settings_views.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
        "views/mail_template_views.xml",
        "wizard/chat_gpt_mass_edit_base_wizard_views.xml",
        "wizard/chat_gpt_mass_edit_base_translation_wizard_views.xml",
    ],
    "external_dependencies": {
        "python": [
            "openai",
        ]
    },
    "images": [
        "static/description/images/main_screenshot.png",
    ],
    "post_init_hook": "post_init_hook",
    "assets": {
        "web.assets_backend": [
            "chat_gpt_mass_edit_base/static/src/scss/chat_gpt_mass_edit_base.scss",
        ],
    },
}
