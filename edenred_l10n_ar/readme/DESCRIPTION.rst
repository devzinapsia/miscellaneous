Glue module: when ``l10n_ar`` is installed alongside ``edenred``, this
module attaches a VAT tax to the Edenred wizard's "subtotal difference"
adjustment line, so it satisfies ``l10n_ar``'s own invoice validation
(``_check_argentinean_invoice_taxes``), which requires exactly one
tax from the "VAT" tax group on every invoice line.

The VAT tax is copied from whichever tax the real (product-matched)
lines already carry, since the difference is still part of the
invoice's taxable net amount and should be taxed the same way.
