from odoo import models


class EdenredImportWizard(models.TransientModel):
    _inherit = 'edenred.import.wizard'

    def _finalize_subtotal_difference_line(self, move):
        super()._finalize_subtotal_difference_line(move)

        if not (move.company_id.account_fiscal_country_id.code == 'AR'
                and move.l10n_latam_use_documents):
            return

        diff_line = move.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product' and not l.product_id)
        if not diff_line:
            return

        # By this point the line should already carry every real line's own
        # taxes (see edenred's _prepare_subtotal_difference_line_vals); this
        # is only a backstop for l10n_ar's own
        # _check_argentinean_invoice_taxes() in case none of them included a
        # VAT-group tax. Only ADD the tax - never replace tax_ids, which
        # would wipe out the ITC/IDC/Impuestos internos it already carries.
        has_vat = diff_line.tax_ids.filtered(lambda t: t.tax_group_id.l10n_ar_vat_afip_code)
        if has_vat:
            return

        vat_tax = move.invoice_line_ids.filtered(lambda l: l.product_id).mapped(
            'tax_ids').filtered(lambda t: t.tax_group_id.l10n_ar_vat_afip_code)[:1]
        if vat_tax:
            diff_line.tax_ids = [(4, vat_tax.id)]
