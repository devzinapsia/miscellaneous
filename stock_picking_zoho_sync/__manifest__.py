{
    "name": "Stock Picking Zoho Sync",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Synchronize validated incoming stock receipts with Zoho",
    "author": "Zinapsia",
    "website": "https://www.zinapsia.com",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "purchase_stock",
    ],
    "data": [
        "data/ir_cron_data.xml",
        "views/res_config_settings_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
}
