from odoo import models


class EdenredImportWizard(models.TransientModel):
    _inherit = 'edenred.import.wizard'

    def _finalize_subtotal_difference_line(self, move):
        super()._finalize_subtotal_difference_line(move)

        if not (move.company_id.account_fiscal_country_id.code == 'AR'
                and move.l10n_latam_use_documents):
            return

        # l10n_ar's own _check_argentinean_invoice_taxes() requires exactly
        # one VAT-group tax per product-type line - the subtotal-difference
        # line has none. Reuse whatever VAT tax the real lines already got
        # (from their product's supplier_taxes_id), since the difference is
        # still part of the invoice's taxable net amount.
        diff_line = move.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product' and not l.product_id)
        if not diff_line:
            return

        vat_tax = move.invoice_line_ids.filtered(lambda l: l.product_id).mapped(
            'tax_ids').filtered(lambda t: t.tax_group_id.l10n_ar_vat_afip_code)[:1]
        if vat_tax:
            diff_line.tax_ids = [(6, 0, vat_tax.ids)]
