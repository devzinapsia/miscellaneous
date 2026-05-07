{
    "name": "YPF Ruta - Importación de Facturas",
    "version": "18.0.1.0.2",
    "category": "Accounting",
    "summary": "Importación automática de planillas YPF Ruta",
    "author": "Zinapsia",
    "website": "https://github.com/devzinapsia/miscellaneous",
    "depends": [
        "account",
        "l10n_ar",
        "analytic",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/ypf_import_wizard_view.xml",
        "wizard/ypf_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ypf_route/static/src/js/ypf_list_button.js",
            "ypf_route/static/src/xml/ypf_list_button.xml",
        ],
    },
    "external_dependencies": {
        "python": ["pandas", "openpyxl"],
    },
    "installable": True,
    "license": "LGPL-3",
}