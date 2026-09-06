from odoo import fields, models


class EdenredImportWizard(models.TransientModel):
    _inherit = 'edenred.import.wizard'

    l10n_latam_document_type_id = fields.Many2one(
        'l10n_latam.document.type', string='Document type')
    document_number = fields.Char(string='Document number')

    def _prepare_move_vals(self):
        vals = super()._prepare_move_vals()
        vals.update({
            'l10n_latam_document_type_id': self.l10n_latam_document_type_id.id,
            'l10n_latam_document_number': self.document_number,
        })
        return vals
