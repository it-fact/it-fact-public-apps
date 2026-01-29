def post_init_hook(env):
    env["ir.config_parameter"].set_param("chat_gpt_mass_edit_base.use_odoo_default", True)
