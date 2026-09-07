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
        cls.subtotal_diff_account = cls.env['account.account'].create({
            'name': 'Subtotal Difference Test',
            'code': '99999903',
            'account_type': 'expense',
            'company_ids': [(6, 0, [cls.company.id])],
        })

        # The "Edenred" property (a "Tags" type entry in the standard
        # product.product_properties field) is defined per product
        # category, via categ_id.product_properties_definition.
        cls.category = cls.env['product.category'].create({'name': 'Edenred Test Category'})
        cls.category.product_properties_definition = [{
            'name': 'edenred_tags',
            'string': 'Edenred',
            'type': 'tags',
            'tags': [
                ['diesel_super', 'DIESEL SUPER', 1],
                ['diesel_premium', 'DIESEL PREMIUM', 2],
                ['nafta_super', 'NAFTA SUPER', 3],
                ['nafta_premium', 'NAFTA PREMIUM', 4],
            ],
        }]

        cls.tax_account_itc = cls.env['account.account'].create({
            'name': 'ITC Tax Account Test',
            'code': '54101030',
            'account_type': 'expense',
            'company_ids': [(6, 0, [cls.company.id])],
        })
        cls.tax_account_idc = cls.env['account.account'].create({
            'name': 'IDC Tax Account Test',
            'code': '54101031',
            'account_type': 'expense',
            'company_ids': [(6, 0, [cls.company.id])],
        })

        def _make_fixed_tax(name, account):
            return cls.env['account.tax'].create({
                'name': name,
                'amount_type': 'fixed',
                'amount': 1.0,
                'type_tax_use': 'purchase',
                'company_id': cls.company.id,
                'invoice_repartition_line_ids': [
                    (0, 0, {'repartition_type': 'base'}),
                    (0, 0, {'repartition_type': 'tax', 'account_id': account.id}),
                ],
                'refund_repartition_line_ids': [
                    (0, 0, {'repartition_type': 'base'}),
                    (0, 0, {'repartition_type': 'tax', 'account_id': account.id}),
                ],
            })

        cls.tax_iva = cls.env['account.tax'].create({
            'name': 'IVA 21%',
            'amount_type': 'percent',
            'amount': 21.0,
            'type_tax_use': 'purchase',
            'company_id': cls.company.id,
        })
        cls.tax_itc = _make_fixed_tax('ITC', cls.tax_account_itc)
        cls.tax_idc = _make_fixed_tax('IDC', cls.tax_account_idc)
        # Real config: "Impuestos internos" posts to the same account as ITC.
        cls.tax_internal = _make_fixed_tax('Impuestos internos', cls.tax_account_itc)

        def _make_catalog_product(name, tag_keys=None, taxes=None):
            return cls.env['product.product'].create({
                'name': name,
                'type': 'consu',
                'purchase_ok': True,
                'categ_id': cls.category.id,
                'property_account_expense_id': cls.vehicle_account.id,
                'product_properties': {'edenred_tags': tag_keys or []},
                'supplier_taxes_id': [(6, 0, taxes.ids)] if taxes else False,
            })

        cls.fuel_taxes = cls.tax_iva + cls.tax_itc + cls.tax_idc + cls.tax_internal
        cls.diesel_autos = _make_catalog_product(
            'Diesel (autos)', ['diesel_super', 'diesel_premium'], cls.fuel_taxes)
        cls.nafta_autos = _make_catalog_product(
            'Nafta (autos)', ['nafta_super', 'nafta_premium'])
        cls.otros_autos = _make_catalog_product('Otros gastos no combustible (autos)')
        cls.diesel_maquinarias = _make_catalog_product(
            'Diesel (maquinarias)', ['diesel_super', 'diesel_premium'])
        cls.nafta_maquinarias = _make_catalog_product(
            'Nafta (maquinarias)', ['nafta_super', 'nafta_premium'])
        cls.otros_maquinarias = _make_catalog_product('Otros gastos no combustible (maquinarias)')

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

    # -- product selection: 6-product catalog by tag ------------------------

    def test_vehicle_matched_tag_match_uses_autos_product_and_own_account(self):
        wizard = self._create_wizard([self._row(**{'Producto / Servicio': 'DIESEL SUPER'})])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)
        self.assertEqual(line.vehicle_id, self.vehicle1)
        self.assertEqual(line.product_id, self.diesel_autos)
        self.assertEqual(line.account_id, self.vehicle_account)
        self.assertEqual(line.price_unit, 1000.0)

    def test_vehicle_not_matched_tag_match_uses_maquinarias_product_but_fallback_account(self):
        wizard = self._create_wizard(
            [self._row(Placa='NOMATCH', **{'Producto / Servicio': 'DIESEL SUPER'})])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)
        self.assertFalse(line.vehicle_id)
        self.assertEqual(line.product_id, self.diesel_maquinarias)
        self.assertEqual(line.account_id, self.fallback_account)

    def test_vehicle_matched_no_tag_match_falls_back_to_otros_autos(self):
        wizard = self._create_wizard([self._row(**{'Producto / Servicio': 'Unknown Product'})])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)
        self.assertEqual(line.product_id, self.otros_autos)
        self.assertEqual(line.account_id, self.vehicle_account)
        self.assertIn('Station 1', line.name)

    def test_vehicle_not_matched_no_tag_match_falls_back_to_otros_maquinarias(self):
        wizard = self._create_wizard(
            [self._row(Placa='NOMATCH', **{'Producto / Servicio': 'Unknown Product'})])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)
        self.assertEqual(line.product_id, self.otros_maquinarias)
        self.assertEqual(line.account_id, self.fallback_account)

    def test_tag_match_is_case_insensitive(self):
        wizard = self._create_wizard([self._row(**{'Producto / Servicio': 'diesel super'})])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)
        self.assertEqual(line.product_id, self.diesel_autos)

    def test_missing_fallback_catalog_product_raises_clear_error(self):
        self.otros_autos.unlink()
        wizard = self._create_wizard([self._row(**{'Producto / Servicio': 'Unknown Product'})])
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_zero_amount_row_excluded_from_invoice_lines(self):
        rows = [
            self._row(**{'No. Transacción': 'T-0001'}),
            self._row(Neto=0.0, **{'No. Transacción': 'T-0002'}),
        ]
        wizard = self._create_wizard(rows)
        move = self._confirm_and_get_move(wizard)
        self.assertEqual(len(self._product_lines(move)), 1)

    def test_zero_amount_row_excluded_from_odometer_processing(self):
        # A vehicle whose only row has Neto == 0 must not get an odometer
        # log at all - the row is dropped before any downstream processing.
        rows = [
            self._row(Placa='XY987ZZ', **{'No. Transacción': 'T-0001'}),
            self._row(Neto=0.0, **{'No. Transacción': 'T-0002'}),
        ]
        wizard = self._create_wizard(rows)
        self._confirm_and_get_move(wizard)
        odometer_vehicle1 = self.env['fleet.vehicle.odometer'].search([
            ('vehicle_id', '=', self.vehicle1.id),
        ])
        odometer_vehicle2 = self.env['fleet.vehicle.odometer'].search([
            ('vehicle_id', '=', self.vehicle2.id),
        ])
        self.assertFalse(odometer_vehicle1)
        self.assertTrue(odometer_vehicle2)

    # -- fallback / subtotal-difference account defaults ---------------------

    def test_fallback_account_default_found_by_code(self):
        magic_account = self.env['account.account'].create({
            'name': 'Magic Code Account',
            'code': '5.3.1.01.148',
            'account_type': 'expense',
            'company_ids': [(6, 0, [self.company.id])],
        })
        res = self.env['edenred.import.wizard'].default_get(
            ['fallback_account_id', 'subtotal_difference_account_id'])
        self.assertEqual(res.get('fallback_account_id'), magic_account.id)
        self.assertEqual(res.get('subtotal_difference_account_id'), magic_account.id)

    def test_fallback_account_default_empty_when_not_found(self):
        res = self.env['edenred.import.wizard'].default_get(
            ['fallback_account_id', 'subtotal_difference_account_id'])
        self.assertFalse(res.get('fallback_account_id'))
        self.assertFalse(res.get('subtotal_difference_account_id'))

    def test_confirm_without_fallback_account_raises(self):
        wizard = self._create_wizard([self._row()], fallback_account_id=False)
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_confirm_without_subtotal_difference_account_raises(self):
        wizard = self._create_wizard([self._row()], subtotal_difference_account_id=False)
        with self.assertRaises(UserError):
            wizard.action_confirm()

    # -- missing columns -----------------------------------------------------

    def test_missing_columns_raises_user_error(self):
        df = pd.DataFrame({'Placa': ['AB123CD'], 'Producto / Servicio': ['DIESEL SUPER']})
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

    def test_fecha_string_is_parsed_day_first(self):
        # Regression: the real Edenred export stores Fecha as "DD/MM/YYYY"
        # text (Argentine convention). Without dayfirst=True, pandas parses
        # it month-first and silently swaps day/month (11/08 -> Nov 8
        # instead of Aug 11).
        wizard = self._create_wizard([self._row(Fecha='11/08/2026', hora='14:30:00')])
        self._confirm_and_get_move(wizard)
        odometer = self.env['fleet.vehicle.odometer'].search([
            ('vehicle_id', '=', self.vehicle1.id),
        ])
        self.assertEqual(odometer.date, date(2026, 8, 11))

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

    # -- fixed tax totals (ITC / IDC / Impuestos internos) -------------------

    def _tax_line(self, move, tax):
        return move.line_ids.filtered(lambda l: l.tax_line_id == tax)

    def test_fixed_tax_totals_applied_from_wizard_inputs(self):
        # internal_tax_total is the gross figure from the Edenred PDF,
        # which bundles ITC+IDC into it - the net "Impuestos internos"
        # tax line must be the residual after subtracting both.
        wizard = self._create_wizard(
            [self._row()],
            itc_total=252000.0,
            idc_total=1500000.0,
            internal_tax_total=1892000.0,
        )
        move = self._confirm_and_get_move(wizard)

        itc_line = self._tax_line(move, self.tax_itc)
        idc_line = self._tax_line(move, self.tax_idc)
        internal_line = self._tax_line(move, self.tax_internal)

        self.assertAlmostEqual(itc_line.amount_currency, 252000.0, places=2)
        self.assertAlmostEqual(idc_line.amount_currency, 1500000.0, places=2)
        self.assertAlmostEqual(internal_line.amount_currency, 140000.0, places=2)

    def test_fixed_tax_totals_missing_tax_line_raises_when_nonzero(self):
        # otros_autos doesn't carry the ITC/IDC/Impuestos internos taxes.
        wizard = self._create_wizard(
            [self._row(**{'Producto / Servicio': 'Unknown Product'})],
            itc_total=100.0,
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_fixed_tax_totals_zero_and_no_tax_line_does_not_raise(self):
        wizard = self._create_wizard([self._row(**{'Producto / Servicio': 'Unknown Product'})])
        move = self._confirm_and_get_move(wizard)
        self.assertTrue(move)

    def test_move_stays_balanced_after_fixed_tax_totals(self):
        wizard = self._create_wizard(
            [self._row(), self._row(Placa='XY987ZZ', **{'No. Transacción': 'T-0002'})],
            subtotal=2000.0,
            itc_total=252000.0,
            idc_total=1500000.0,
            internal_tax_total=1892000.0,
        )
        move = self._confirm_and_get_move(wizard)
        debit = sum(move.line_ids.mapped('debit'))
        credit = sum(move.line_ids.mapped('credit'))
        self.assertAlmostEqual(debit, credit, places=2)

    # -- subtotal reconciliation ---------------------------------------------

    def test_subtotal_matches_no_adjustment_line(self):
        rows = [self._row()]
        wizard = self._create_wizard(rows)
        move = self._confirm_and_get_move(wizard)
        self.assertEqual(len(self._product_lines(move)), 1)

    def test_subtotal_mismatch_adds_difference_line_positive(self):
        rows = [self._row()]
        wizard = self._create_wizard(rows, subtotal=1050.0)
        move = self._confirm_and_get_move(wizard)
        lines = self._product_lines(move)
        self.assertEqual(len(lines), 2)
        diff_line = lines.filtered(lambda l: not l.product_id)
        self.assertTrue(diff_line)
        self.assertAlmostEqual(diff_line.price_unit, 50.0, places=2)
        self.assertEqual(diff_line.account_id, self.subtotal_diff_account)
        # Must carry the same 4 taxes as the real line (diesel_autos), not
        # be left untaxed - it's still part of the taxable net amount.
        self.assertEqual(diff_line.tax_ids, self.fuel_taxes)

    def test_subtotal_mismatch_adds_difference_line_negative(self):
        rows = [self._row()]
        wizard = self._create_wizard(rows, subtotal=950.0)
        move = self._confirm_and_get_move(wizard)
        lines = self._product_lines(move)
        diff_line = lines.filtered(lambda l: not l.product_id)
        self.assertAlmostEqual(diff_line.price_unit, -50.0, places=2)

    # -- fleet service log --------------------------------------------------

    def test_fleet_log_service_created_with_row_data(self):
        wizard = self._create_wizard([self._row(Litros=35.5)])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)

        service = self.env['fleet.vehicle.log.services'].search([
            ('account_move_line_id', '=', line.id),
        ])
        self.assertEqual(len(service), 1)
        self.assertEqual(service.vehicle_id, self.vehicle1)
        self.assertEqual(service.description, 'DIESEL SUPER 35.50 L')
        self.assertEqual(service.date, date(2026, 8, 5))
        self.assertEqual(service.notes, line.name)

        odometer = self.env['fleet.vehicle.odometer'].search([
            ('vehicle_id', '=', self.vehicle1.id),
            ('date', '=', date(2026, 8, 5)),
        ])
        self.assertEqual(service.odometer_id, odometer)

    def test_fleet_log_service_not_created_without_vehicle_match(self):
        wizard = self._create_wizard([self._row(Placa='NOMATCH')])
        move = self._confirm_and_get_move(wizard)
        line = self._product_lines(move)
        service = self.env['fleet.vehicle.log.services'].search([
            ('account_move_line_id', '=', line.id),
        ])
        self.assertFalse(service)

    def test_fleet_log_service_not_duplicated_when_posted(self):
        # account_fleet's own _post() would auto-create a bare service log
        # for any vehicle-matched line without one already - since we create
        # ours upfront, it must skip that and not create a second one.
        wizard = self._create_wizard([self._row()])
        move = self._confirm_and_get_move(wizard)
        move.action_post()
        line = self._product_lines(move)
        services = self.env['fleet.vehicle.log.services'].search([
            ('account_move_line_id', '=', line.id),
        ])
        self.assertEqual(len(services), 1)

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
