import base64
import io
from datetime import date, time

import pandas as pd

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEdenredL10nLatam(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.partner = cls.env['res.partner'].create({
            'name': 'Edenred Test',
            'supplier_rank': 1,
        })
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', cls.company.id),
        ], limit=1)

        cls.fallback_account = cls.env['account.account'].create({
            'name': 'Fallback Test',
            'code': '99999902',
            'account_type': 'expense',
            'company_ids': [(6, 0, [cls.company.id])],
        })
        cls.subtotal_diff_account = cls.env['account.account'].create({
            'name': 'Subtotal Difference Test',
            'code': '99999904',
            'account_type': 'expense',
            'company_ids': [(6, 0, [cls.company.id])],
        })
        # No fleet.vehicle is created in this test, so the row's plate never
        # matches -> the wizard falls back to the "maquinarias" catalog's
        # own fallback product (no Edenred tag configured for this test).
        cls.otros_maquinarias = cls.env['product.product'].create({
            'name': 'Otros gastos no combustible (maquinarias)',
            'type': 'consu',
            'purchase_ok': True,
        })
        cls.country = cls.env['res.country'].search([], limit=1)
        cls.doc_type = cls.env['l10n_latam.document.type'].create({
            'name': 'Test Invoice',
            'country_id': cls.country.id,
        })

    def setUp(self):
        super().setUp()
        self.patch(
            type(self.env['edenred.import.wizard']),
            '_EDENRED_TAG_FIELD',
            'product_tag_ids',
        )

    def _build_excel(self):
        row = {
            'Placa': 'AB123CD',
            'Producto / Servicio': 'GNC',
            'Neto': 1000.0,
            'Fecha': date(2026, 8, 5),
            'hora': time(10, 0),
            'Conductor': 'Juan Perez',
            'Código de conductor': 'C001',
            'Estación de servicio': 'Station 1',
            'Dirección Estación': 'Main St 123',
            'No. Transacción': 'T-0001',
            'Último odómetro': 12345.0,
            'Litros': 35.5,
        }
        df = pd.DataFrame({k: [v] for k, v in row.items()})
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine='openpyxl')
        return base64.b64encode(buf.getvalue())

    def test_l10n_latam_fields_available_and_passed_to_move(self):
        wizard = self.env['edenred.import.wizard'].create({
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'excel_file': self._build_excel(),
            'excel_filename': 'edenred.xlsx',
            'pdf_file': base64.b64encode(b'%PDF-1.4 test invoice'),
            'pdf_filename': 'edenred.pdf',
            'subtotal': 1000.0,
            'fallback_account_id': self.fallback_account.id,
            'subtotal_difference_account_id': self.subtotal_diff_account.id,
            'l10n_latam_document_type_id': self.doc_type.id,
            'document_number': '0001-00000001',
        })
        action = wizard.action_confirm()
        move = self.env['account.move'].browse(action['res_id'])

        self.assertEqual(move.l10n_latam_document_type_id, self.doc_type)
        self.assertEqual(move.l10n_latam_document_number, '0001-00000001')
