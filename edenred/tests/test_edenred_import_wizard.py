import base64
import io
from datetime import date, time
from unittest import mock

import pandas as pd

from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEdenredImportWizard(TransactionCase):

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
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Test Purchase Journal',
                'type': 'purchase',
                'code': 'TPUR',
                'company_id': cls.company.id,
            })

        cls.vehicle_account = cls.env['account.account'].create({
            'name': 'Vehicle Expenses Test',
            'code': '70000001',
            'account_type': 'expense',
            'company_ids': [(6, 0, [cls.company.id])],
        })
        cls.fallback_account = cls.env['account.account'].create({
            'name': 'Fallback Test',
            'code': '99999901',
            'account_type': 'expense',
            'company_ids': [(6, 0, [cls.company.id])],
        })

        cls.product = cls.env['product.product'].create({
            'name': 'GNC',
            'type': 'consu',
            'purchase_ok': True,
            'property_account_expense_id': cls.vehicle_account.id,
        })
        cls.nafta_super = cls.env['product.product'].create({
            'name': 'Nafta Super',
            'type': 'consu',
            'purchase_ok': True,
            'property_account_expense_id': cls.vehicle_account.id,
        })

        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'})
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': cls.brand.id,
        })
        cls.vehicle1 = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'AB123CD',
            'company_id': cls.company.id,
        })
        cls.vehicle2 = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'XY987ZZ',
            'company_id': cls.company.id,
        })

        cls.employee = cls.env['hr.employee'].create({'name': 'Juan Perez'})
        cls.employee2 = cls.env['hr.employee'].create({'name': 'Maria Gomez'})

    # -- helpers ---------------------------------------------------------

    def _row(self, **overrides):
        base = {
            'Placa': 'AB123CD',
            'Producto / Servicio': 'GNC',
            'Precio neto': 1000.0,
            'Fecha': date(2026, 8, 5),
            'hora': time(10, 0),
            'Conductor': 'Juan Perez',
            'Código de conductor': 'C001',
            'Estación de servicio': 'Station 1',
            'Dirección Estación': 'Main St 123',
            'No. Transacción': 'T-0001',
            'Último odómetro': 12345.0,
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
            'subtotal': sum(r['Precio neto'] for r in rows),
            'fallback_account_id': self.fallback_account.id,
        }
        vals.update(kwargs)
        return self.env['edenred.import.wizard'].create(vals)

    def _confirm_and_get_move(self, wizard):
        action = wizard.action_confirm()
        return self.env['account.move'].browse(action['res_id'])

    def _product_lines(self, move):
        return move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')

    # -- basic import ------------------------------------------------------

    def test_import_creates_balanced_invoice_with_one_line_per_row(self):
        rows = [self._row(), self._row(Placa='XY987ZZ', **{'No. Transacción': 'T-0002'})]
        wizard = self._create_wizard(rows)
        move = self._confirm_and_get_move(wizard)

        self.assertEqual(move.move_type, 'in_invoice')
        self.assertEqual(move.partner_id, self.partner)
        self.assertEqual(len(self._product_lines(move)), 2)
        debit = sum(move.line_ids.mapped('debit'))
        credit = sum(move.line_ids.mapped('credit'))
        self.assertAlmostEqual(debit, credit, places=2)

    def test_vehicle_matched_line_uses_product_account(self):
        wizard = self._create_wizard([self._row()])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)
        self.assertEqual(line.vehicle_id, self.vehicle1)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.account_id, self.vehicle_account)

    def test_vehicle_not_matched_uses_fallback_account(self):
        wizard = self._create_wizard([self._row(Placa='NOMATCH')])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)
        self.assertFalse(line.vehicle_id)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.account_id, self.fallback_account)

    def test_product_not_found_creates_line_without_product(self):
        wizard = self._create_wizard([self._row(**{'Producto / Servicio': 'Unknown Product'})])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)
        self.assertFalse(line.product_id)
        self.assertEqual(line.account_id, self.fallback_account)
        self.assertIn('Station 1', line.name)

    # -- fallback account default ------------------------------------------

    def test_fallback_account_default_found_by_code(self):
        magic_account = self.env['account.account'].create({
            'name': 'Magic Code Account',
            'code': '5.3.1.01.148',
            'account_type': 'expense',
            'company_ids': [(6, 0, [self.company.id])],
        })
        res = self.env['edenred.import.wizard'].default_get(['fallback_account_id'])
        self.assertEqual(res.get('fallback_account_id'), magic_account.id)

    def test_fallback_account_default_empty_when_not_found(self):
        res = self.env['edenred.import.wizard'].default_get(['fallback_account_id'])
        self.assertFalse(res.get('fallback_account_id'))

    def test_confirm_without_fallback_account_raises(self):
        wizard = self._create_wizard([self._row()], fallback_account_id=False)
        with self.assertRaises(UserError):
            wizard.action_confirm()

    # -- missing columns -----------------------------------------------------

    def test_missing_columns_raises_user_error(self):
        df = pd.DataFrame({'Placa': ['AB123CD'], 'Producto / Servicio': ['GNC']})
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine='openpyxl')
        wizard = self._create_wizard([self._row()])
        wizard.excel_file = base64.b64encode(buf.getvalue())
        with self.assertRaises(UserError):
            wizard.action_confirm()

    # -- driver / odometer ---------------------------------------------------

    def test_driver_and_odometer_taken_from_most_recent_row(self):
        rows = [
            self._row(Fecha=date(2026, 8, 1), hora=time(8, 0), Conductor='Maria Gomez',
                      **{'Último odómetro': 100.0, 'No. Transacción': 'T-0001'}),
            self._row(Fecha=date(2026, 8, 5), hora=time(9, 0), Conductor='Juan Perez',
                      **{'Último odómetro': 200.0, 'No. Transacción': 'T-0002'}),
        ]
        wizard = self._create_wizard(rows)
        self._confirm_and_get_move(wizard)

        self.vehicle1.invalidate_recordset()
        self.assertEqual(self.vehicle1.driver_id, self.employee.work_contact_id)

        odometer = self.env['fleet.vehicle.odometer'].search([
            ('vehicle_id', '=', self.vehicle1.id),
        ])
        self.assertEqual(len(odometer), 1)
        self.assertEqual(odometer.date, date(2026, 8, 5))
        self.assertEqual(odometer.value, 200.0)
        self.assertEqual(odometer.driver_id, self.employee.work_contact_id)

    def test_driver_name_reversed_order_matches(self):
        wizard = self._create_wizard([self._row(Conductor='Perez Juan')])
        self._confirm_and_get_move(wizard)
        self.vehicle1.invalidate_recordset()
        self.assertEqual(self.vehicle1.driver_id, self.employee.work_contact_id)

    def test_driver_no_match_or_ambiguous_does_not_assign(self):
        # A homonym sharing every name-word with cls.employee (just reversed
        # order) makes the word-set match for 'Juan Perez' ambiguous.
        self.env['hr.employee'].create({'name': 'Perez Juan'})
        self.vehicle1.driver_id = False
        wizard = self._create_wizard([self._row(Conductor='Juan Perez')])
        move = self._confirm_and_get_move(wizard)

        self.assertTrue(self._product_lines(move))
        self.vehicle1.invalidate_recordset()
        self.assertFalse(self.vehicle1.driver_id)

        odometer = self.env['fleet.vehicle.odometer'].search([
            ('vehicle_id', '=', self.vehicle1.id),
            ('date', '=', date(2026, 8, 5)),
        ])
        self.assertTrue(odometer)
        self.assertFalse(odometer.driver_id)

    def test_vehicle_driver_not_rewritten_when_same(self):
        self.vehicle1.driver_id = self.employee.work_contact_id
        with mock.patch.object(type(self.vehicle1), 'write', autospec=True) as mock_write:
            wizard = self._create_wizard([self._row(Conductor='Juan Perez')])
            wizard.action_confirm()
            mock_write.assert_not_called()

    def test_vehicle_driver_rewritten_when_different(self):
        other_partner = self.env['res.partner'].create({'name': 'Old Driver'})
        self.vehicle1.driver_id = other_partner
        wizard = self._create_wizard([self._row(Conductor='Juan Perez')])
        self._confirm_and_get_move(wizard)
        self.vehicle1.invalidate_recordset()
        self.assertEqual(self.vehicle1.driver_id, self.employee.work_contact_id)

    def test_reimport_same_vehicle_same_day_updates_odometer_not_duplicate(self):
        wizard1 = self._create_wizard([self._row(**{'Último odómetro': 100.0})])
        self._confirm_and_get_move(wizard1)

        wizard2 = self._create_wizard([self._row(**{'Último odómetro': 150.0})])
        self._confirm_and_get_move(wizard2)

        odometer = self.env['fleet.vehicle.odometer'].search([
            ('vehicle_id', '=', self.vehicle1.id),
            ('date', '=', date(2026, 8, 5)),
        ])
        self.assertEqual(len(odometer), 1)
        self.assertEqual(odometer.value, 150.0)

    def test_different_day_creates_new_odometer_record(self):
        wizard1 = self._create_wizard([self._row(Fecha=date(2026, 8, 5), **{'Último odómetro': 100.0})])
        self._confirm_and_get_move(wizard1)

        wizard2 = self._create_wizard([self._row(Fecha=date(2026, 8, 6), **{'Último odómetro': 150.0})])
        self._confirm_and_get_move(wizard2)

        odometers = self.env['fleet.vehicle.odometer'].search([
            ('vehicle_id', '=', self.vehicle1.id),
        ])
        self.assertEqual(len(odometers), 2)
        self.assertEqual(set(odometers.mapped('value')), {100.0, 150.0})

    # -- subtotal reconciliation ---------------------------------------------

    def test_subtotal_matches_no_adjustment_line(self):
        rows = [self._row()]
        wizard = self._create_wizard(rows)
        move = self._confirm_and_get_move(wizard)
        self.assertEqual(len(self._product_lines(move)), 1)

    def test_subtotal_mismatch_adds_nafta_super_line_positive(self):
        rows = [self._row()]
        wizard = self._create_wizard(rows, subtotal=1050.0)
        move = self._confirm_and_get_move(wizard)
        lines = self._product_lines(move)
        self.assertEqual(len(lines), 2)
        nafta_line = lines.filtered(lambda l: l.product_id == self.nafta_super)
        self.assertAlmostEqual(nafta_line.price_unit, 50.0, places=2)
        self.assertEqual(nafta_line.account_id, self.fallback_account)

    def test_subtotal_mismatch_adds_nafta_super_line_negative(self):
        rows = [self._row()]
        wizard = self._create_wizard(rows, subtotal=950.0)
        move = self._confirm_and_get_move(wizard)
        lines = self._product_lines(move)
        nafta_line = lines.filtered(lambda l: l.product_id == self.nafta_super)
        self.assertAlmostEqual(nafta_line.price_unit, -50.0, places=2)

    # -- attachments -----------------------------------------------------

    def test_excel_and_pdf_attached(self):
        wizard = self._create_wizard([self._row()])
        move = self._confirm_and_get_move(wizard)
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', move.id),
        ])
        self.assertEqual(len(attachments), 2)
        self.assertEqual(set(attachments.mapped('name')), {'edenred.xlsx', 'edenred.pdf'})

    # -- regression: editing a line after import must not raise --------------

    def test_edit_invoice_line_after_import_does_not_raise(self):
        wizard = self._create_wizard([self._row()])
        move = self._confirm_and_get_move(wizard)

        with Form(move) as move_form:
            with move_form.invoice_line_ids.edit(0) as line_form:
                line_form.price_unit = line_form.price_unit + 1.5

        move.invalidate_recordset()
        debit = sum(move.line_ids.mapped('debit'))
        credit = sum(move.line_ids.mapped('credit'))
        self.assertAlmostEqual(debit, credit, places=2)

        move.action_post()
        self.assertEqual(move.state, 'posted')
