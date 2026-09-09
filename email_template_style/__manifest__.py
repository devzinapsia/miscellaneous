{
    "name": "Email Template Style",
    "version": "19.0.1.1.0",
    "category": "Accounting",
    "summary": "Switch Odoo's default email templates between Zinapsia Formal and Informal styles",
    "author": "Zinapsia",
    "website": "https://www.zinapsia.com",
    "license": "AGPL-3",
    "depends": [
        "account",
        "sale",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
