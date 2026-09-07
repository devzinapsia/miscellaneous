import base64
import io
from datetime import date, time

import pandas as pd

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEdenredL10nAr(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.account_fiscal_country_id = cls.env.ref('base.ar')

        cls.partner = cls.env['res.partner'].create({
            'name': 'Edenred Test',
            'supplier_rank': 1,
        })
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Test Purchase Journal',
                'type': 'purchase',
                'code': 'TPUR',
                'company_id': cls.company.id,
            })
        cls.journal.l10n_latam_use_documents = True

        cls.fallback_account = cls.env['account.account'].create({
            'name': 'Fallback Test',
            'code': '99999905',
            'account_type': 'expense',
            'company_ids': [(6, 0, [cls.company.id])],
        })
        cls.subtotal_diff_account = cls.env['account.account'].create({
            'name': 'Subtotal Difference Test',
            'code': '99999906',
            'account_type': 'expense',
            'company_ids': [(6, 0, [cls.company.id])],
        })

        cls.vat_tax_group = cls.env['account.tax.group'].create({
            'name': 'VAT 21% Test',
            'l10n_ar_vat_afip_code': '5',
        })
        cls.vat_tax = cls.env['account.tax'].create({
            'name': 'IVA 21% AR Test',
            'amount_type': 'percent',
            'amount': 21.0,
            'type_tax_use': 'purchase',
            'company_id': cls.company.id,
            'tax_group_id': cls.vat_tax_group.id,
        })

        cls.category = cls.env['product.category'].create({'name': 'Edenred AR Test Category'})
        cls.category.product_properties_definition = [{
            'name': 'edenred_tags',
            'string': 'Edenred',
            'type': 'tags',
            'tags': [['diesel_super', 'DIESEL SUPER', 1]],
        }]
        cls.diesel_autos = cls.env['product.product'].create({
            'name': 'Diesel (autos)',
            'type': 'consu',
            'purchase_ok': True,
            'categ_id': cls.category.id,
            'property_account_expense_id': cls.fallback_account.id,
            'product_properties': {'edenred_tags': ['diesel_super']},
            'supplier_taxes_id': [(6, 0, [cls.vat_tax.id])],
        })
        cls.otros_maquinarias = cls.env['product.product'].create({
            'name': 'Otros gastos no combustible (maquinarias)',
            'type': 'consu',
            'purchase_ok': True,
        })

        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand AR'})
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model AR',
            'brand_id': cls.brand.id,
        })
        cls.vehicle1 = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'AR123CD',
            'company_id': cls.company.id,
        })

    def _row(self, **overrides):
        base = {
            'Placa': 'AR123CD',
            'Producto / Servicio': 'DIESEL SUPER',
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
        base.update(overrides)
        return base

    def _build_excel(self, rows):
        columns = {}
        for row in rows:
            for key, value in row.items():
                columns.setdefault(key, []).append(value)
        df = pd.DataFrame(columns)
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine='openpyxl')
        return base64.b64encode(buf.getvalue())

    def _create_wizard(self, rows, **kwargs):
        vals = {
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'excel_file': self._build_excel(rows),
            'excel_filename': 'edenred.xlsx',
            'pdf_file': base64.b64encode(b'%PDF-1.4 test invoice'),
            'pdf_filename': 'edenred.pdf',
            'subtotal': sum(r['Neto'] for r in rows),
            'itc_total': 0.0,
            'idc_total': 0.0,
            'internal_tax_total': 0.0,
            'fallback_account_id': self.fallback_account.id,
            'subtotal_difference_account_id': self.subtotal_diff_account.id,
        }
        vals.update(kwargs)
        return self.env['edenred.import.wizard'].create(vals)

    def test_subtotal_difference_line_gets_vat_tax_for_ar_company(self):
        wizard = self._create_wizard([self._row()], subtotal=1050.0)
        action = wizard.action_confirm()
        move = self.env['account.move'].browse(action['res_id'])

        diff_line = move.invoice_line_ids.filtered(lambda l: not l.product_id)
        self.assertTrue(diff_line)
        self.assertIn(self.vat_tax, diff_line.tax_ids)

        # This is the actual check that was failing before this module
        # existed - proves the fix satisfies l10n_ar's own validation.
        move._check_argentinean_invoice_taxes()

    def test_subtotal_difference_line_untouched_when_subtotal_matches(self):
        wizard = self._create_wizard([self._row()])
        action = wizard.action_confirm()
        move = self.env['account.move'].browse(action['res_id'])
        diff_line = move.invoice_line_ids.filtered(lambda l: not l.product_id)
        self.assertFalse(diff_line)
