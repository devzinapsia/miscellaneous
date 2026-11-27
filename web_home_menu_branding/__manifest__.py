{
    "name": "Branding Zinapsia en el menú de aplicaciones",
    "version": "19.0.1.0.0",
    "summary": "Muestra el logo de Zinapsia, el logo y nombre de la empresa "
    "activa y el contacto de soporte en el menú de aplicaciones.",
    "author": "Zinapsia",
    "website": "https://www.zinapsia.com",
    "license": "LGPL-3",
    "category": "Hidden/Tools",
    "depends": ["web_enterprise"],
    "assets": {
        "web.assets_backend": [
            "web_home_menu_branding/static/src/home_menu/**/*",
        ],
        "web.assets_tests": [
            "web_home_menu_branding/static/tests/tours/**/*",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
}
