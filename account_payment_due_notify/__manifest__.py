{
    "name": "Payment Due Notifications",
    "version": "19.0.1.0.0",
    "summary": "Automatically notify configured users before payable "
    "journal items become due.",
    "author": "Zinapsia",
    "website": "https://www.zinapsia.com",
    "license": "AGPL-3",
    "category": "Accounting/Accounting",
    "depends": ["account"],
    "data": [
        "data/ir_cron_data.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
