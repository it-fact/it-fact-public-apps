from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    openapi_api_key = fields.Char(
        string="API Key",
        help="Provide the API key here",
        config_parameter="chat_gpt_mass_edit_base.openapi_api_key",
    )
    chatgpt_model_id = fields.Many2one(
        "chatgpt.model",
        "ChatGPT Model",
        ondelete="cascade",
        # default=_get_default_chatgpt_model,
        config_parameter="chat_gpt_mass_edit_base.chatgpt_model",
    )

    org_id = fields.Char(config_parameter="chat_gpt_mass_edit_base.org_id")
    project = fields.Char(config_parameter="chat_gpt_mass_edit_base.project")

    dummy_mode = fields.Boolean(
        "DummyMode",
        config_parameter="is_chatgpt_integration.dummy_mode",
    )
    dummy_value = fields.Char(
        "DummyValue",
        config_parameter="is_chatgpt_integration.dummy_value",
    )
    use_odoo_default = fields.Boolean(
        default=True,
        help=(
            "Use the odoo default with IAP. If you need more queries or advanced features "
            "like image analytics you have to provide your own Chat GPT API Credentials."
        ),
    )

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].set_param("chat_gpt_mass_edit_base.openapi_api_key", self.openapi_api_key)
        self.env["ir.config_parameter"].set_param(
            "chat_gpt_mass_edit_base.chatgpt_model_id", self.chatgpt_model_id.id
        )
        self.env["ir.config_parameter"].set_param("chat_gpt_mass_edit_base.org_id", self.org_id)
        self.env["ir.config_parameter"].set_param("chat_gpt_mass_edit_base.project", self.project)
        self.env["ir.config_parameter"].set_param(
            "chat_gpt_mass_edit_base.use_odoo_default", self.use_odoo_default
        )
        self.env["ir.config_parameter"].set_param("chat_gpt_mass_edit_base.dummy_mode", self.dummy_mode)
        self.env["ir.config_parameter"].set_param("chat_gpt_mass_edit_base.dummy_value", self.dummy_value)

        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        res.update(openapi_api_key=params.get_param("chat_gpt_mass_edit_base.openapi_api_key"))
        model = params.get_param("chat_gpt_mass_edit_base.chatgpt_model_id")
        model_id = self.env["chatgpt.model"].browse(int(model))

        res.update(
            chatgpt_model_id=model_id,
            org_id=params.get_param("chat_gpt_mass_edit_base.org_id"),
            project=params.get_param("chat_gpt_mass_edit_base.project"),
            dummy_mode=params.get_param("chat_gpt_mass_edit_base.dummy_mode"),
            dummy_value=params.get_param("chat_gpt_mass_edit_base.dummy_value"),
            use_odoo_default=params.get_param("chat_gpt_mass_edit_base.use_odoo_default"),
        )

        return res
