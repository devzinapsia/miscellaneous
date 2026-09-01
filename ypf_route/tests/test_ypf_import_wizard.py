import base64
import io

import pandas as pd

from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestYpfImportWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.partner = cls.env['res.partner'].create({
            'name': 'YPF Test',
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
        cls.doc_type = cls.env['l10n_latam.document.type'].search([
            ('code', '=', '1'),
            ('country_id.code', '=', 'AR'),
        ], limit=1)

        cls.tax_iva = cls.env['account.tax'].create({
            'name': 'IVA 21% Test',
            'amount': 21.0,
            'amount_type': 'percent',
            'type_tax_use': 'purchase',
            'company_id': cls.company.id,
        })
        cls.tax_ico2 = cls._make_fixed_tax('ICO2')
        cls.tax_vial = cls._make_fixed_tax('Tasa vial')
        cls.tax_itc = cls._make_fixed_tax('ITC')

        cls.product = cls.env['product.product'].create({
            'name': 'NAFTA SUPER',
            'type': 'consu',
            'purchase_ok': True,
            'company_id': cls.company.id,
            'supplier_taxes_id': [(6, 0, [
                cls.tax_iva.id, cls.tax_ico2.id, cls.tax_vial.id, cls.tax_itc.id,
            ])],
        })

        cls.ana_plan = cls.env['account.analytic.plan'].search([], limit=1)
        if not cls.ana_plan:
            cls.ana_plan = cls.env['account.analytic.plan'].create({'name': 'Vehiculos Test'})
        cls.ana_veh1 = cls.env['account.analytic.account'].create({
            'name': 'AB123CD - Vehiculo 1',
            'plan_id': cls.ana_plan.id,
            'company_id': cls.company.id,
        })
        cls.ana_veh2 = cls.env['account.analytic.account'].create({
            'name': 'XY987ZZ - Vehiculo 2',
            'plan_id': cls.ana_plan.id,
            'company_id': cls.company.id,
        })

    @classmethod
    def _make_fixed_tax(cls, name):
        return cls.env['account.tax'].create({
            'name': name,
            'amount': 1.0,
            'amount_type': 'fixed',
            'type_tax_use': 'purchase',
            'company_id': cls.company.id,
        })

    @classmethod
    def _build_excel(cls, rows):
        df = pd.DataFrame(rows)
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine='openpyxl')
        return base64.b64encode(buf.getvalue())

    def _create_wizard(self, rows, **kwargs):
        vals = {
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'l10n_latam_document_type_id': self.doc_type.id,
            'document_number': '0001-00000001',
            'excel_file': self._build_excel(rows),
            'file_name': 'test.xlsx',
            'group_type': 'product',
            'use_analytic_domain': True,
        }
        vals.update(kwargs)
        return self.env['ypf.import.wizard'].create(vals)

    def _two_vehicle_rows(self):
        return {
            'PRODUCTO': ['NAFTA SUPER', 'NAFTA SUPER'],
            'IDENTIFICACION TARJETA': ['AB123CD', 'XY987ZZ'],
            'IMP TOT YER': [10000.33, 15000.67],
            'IVA': [1735.87, 2603.98],
            'IMP CO2': [120.10, 180.15],
            'TASA VIAL': [80.05, 120.08],
            'IMP COMB LIQ': [500.20, 750.30],
        }

    def _move_balance(self, move):
        return (
            sum(move.line_ids.mapped('debit')),
            sum(move.line_ids.mapped('credit')),
        )

    def test_import_creates_balanced_invoice(self):
        wizard = self._create_wizard(self._two_vehicle_rows())
        action = wizard.action_confirm()
        move = self.env['account.move'].browse(action['res_id'])

        self.assertEqual(move.move_type, 'in_invoice')
        self.assertEqual(move.partner_id, self.partner)
        debit, credit = self._move_balance(move)
        self.assertAlmostEqual(debit, credit, places=2)

        # in_invoice is NOT is_inbound() in Odoo's terminology (money flows
        # out to pay the vendor), so the wizard's sign ends up positive here
        # despite the misleading comment in _apply_fixed_tax_amounts.
        ico2_lines = move.line_ids.filtered(lambda l: l.tax_line_id == self.tax_ico2)
        self.assertAlmostEqual(
            sum(ico2_lines.mapped('amount_currency')),
            120.10 + 180.15,
            places=2,
        )

    def test_analytic_distribution_weighted_by_vehicle(self):
        wizard = self._create_wizard(self._two_vehicle_rows())
        action = wizard.action_confirm()
        move = self.env['account.move'].browse(action['res_id'])

        product_line = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        self.assertEqual(len(product_line), 1)
        distribution = product_line.analytic_distribution
        self.assertIn(str(self.ana_veh1.id), distribution)
        self.assertIn(str(self.ana_veh2.id), distribution)
        total_weight = sum(distribution.values())
        self.assertAlmostEqual(total_weight, 100.0, places=1)

    def test_line_mode_creates_one_line_per_row(self):
        wizard = self._create_wizard(self._two_vehicle_rows(), group_type='line')
        action = wizard.action_confirm()
        move = self.env['account.move'].browse(action['res_id'])

        product_lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        self.assertEqual(len(product_lines), 2)
        for line in product_lines:
            self.assertEqual(len(line.analytic_distribution or {}), 1)

    def test_filters_total_and_empty_rows(self):
        rows = self._two_vehicle_rows()
        for key in rows:
            rows[key].append(0 if key != 'PRODUCTO' else 0)
        wizard = self._create_wizard(rows)
        action = wizard.action_confirm()
        move = self.env['account.move'].browse(action['res_id'])

        product_lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        self.assertEqual(len(product_lines), 1)

    def test_no_valid_rows_raises_user_error(self):
        rows = {
            'PRODUCTO': [0, ''],
            'IDENTIFICACION TARJETA': ['AB123CD', 'XY987ZZ'],
            'IMP TOT YER': [100.0, 200.0],
            'IVA': [0, 0],
            'IMP CO2': [0, 0],
            'TASA VIAL': [0, 0],
            'IMP COMB LIQ': [0, 0],
        }
        wizard = self._create_wizard(rows)
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_missing_tax_is_skipped_without_error(self):
        self.tax_ico2.name = 'ICO2 renamed, no longer matches'
        wizard = self._create_wizard(self._two_vehicle_rows())
        action = wizard.action_confirm()
        move = self.env['account.move'].browse(action['res_id'])
        debit, credit = self._move_balance(move)
        self.assertAlmostEqual(debit, credit, places=2)

    def test_edit_invoice_line_after_import_does_not_raise(self):
        """Regression test: editing a line after import used to break the
        consolidated fixed-tax lines and raise a check_amount_currency_balance_sign
        constraint violation on save (see readme/DEVELOPMENT_NOTES.md)."""
        wizard = self._create_wizard(self._two_vehicle_rows(), group_type='line')
        action = wizard.action_confirm()
        move = self.env['account.move'].browse(action['res_id'])

        with Form(move) as move_form:
            with move_form.invoice_line_ids.edit(0) as line_form:
                line_form.price_unit = line_form.price_unit + 1.5

        move.invalidate_recordset()
        debit, credit = self._move_balance(move)
        self.assertAlmostEqual(debit, credit, places=2)

        move.action_post()
        self.assertEqual(move.state, 'posted')
