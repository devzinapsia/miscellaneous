{
    "name": "Edenred - LATAM Document Type",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Add LATAM document type/number fields to the Edenred import wizard",
    "author": "Zinapsia",
    "website": "https://www.zinapsia.com",
    "license": "AGPL-3",
    "depends": [
        "edenred",
        "l10n_latam_invoice_document",
    ],
    "data": [
        "wizard/edenred_import_wizard_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
