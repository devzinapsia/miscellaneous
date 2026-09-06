from odoo import fields, models


class EdenredImportWizard(models.TransientModel):
    _inherit = 'edenred.import.wizard'

    # Not required=True at the field level: these land on the same DB table
    # as the base edenred.import.wizard (Odoo merges _inherit fields into one
    # table for TransientModels), so a model-level NOT NULL constraint here
    # would break every wizard creation - including edenred's own tests,
    # which know nothing about this glue module. Required only in the view.
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
