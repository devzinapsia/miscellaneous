{
    "name": "Color de empresa activa",
    "version": "19.0.1.0.0",
    "summary": "Muestra el color de cada empresa en el selector de empresas "
    "para identificar a simple vista cuáles están activas.",
    "author": "Zinapsia",
    "website": "https://www.zinapsia.com",
    "license": "AGPL-3",
    "category": "Hidden/Tools",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "web_company_switcher_color/static/src/**/*",
        ],
        "web.assets_unit_tests": [
            "web_company_switcher_color/static/tests/**/*.test.js",
        ],
        "web.assets_tests": [
            "web_company_switcher_color/static/tests/tours/**/*",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
