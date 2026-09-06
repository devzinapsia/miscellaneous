{
    "name": "Edenred - Fuel Invoice Import",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Import Edenred fuel consumption spreadsheets into a vendor bill",
    "author": "Zinapsia",
    "website": "https://www.zinapsia.com",
    "license": "AGPL-3",
    "depends": [
        "account",
        "fleet",
        "hr",
        "account_fleet",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/edenred_import_wizard_views.xml",
        "wizard/edenred_menu.xml",
    ],
    "external_dependencies": {
        "python": ["pandas", "openpyxl"],
    },
    "installable": True,
    "auto_install": False,
}
