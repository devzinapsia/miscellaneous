import base64
import io
import re
from datetime import datetime
from datetime import time as dt_time

import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang


class EdenredImportWizard(models.TransientModel):
    _name = 'edenred.import.wizard'
    _description = 'Edenred Fuel Invoice Import Wizard'

    # Default code used only to look up a sensible default for
    # `fallback_account_id` / `subtotal_difference_account_id` - not
    # referenced anywhere else in the module.
    _FALLBACK_ACCOUNT_DEFAULT_CODE = '5.3.1.01.148'
    _SUBTOTAL_DIFFERENCE_ACCOUNT_DEFAULT_CODE = '5.3.1.01.148'

    # "Edenred" is not a Studio field: it's a "tags"-type entry inside
    # Odoo's standard product.product_properties field (fields.Properties,
    # defined per product category via categ_id.product_properties_definition
    # - Settings > Technical > Database Structure > Fields confirms
    # product_properties as the technical name). Matched by its label
    # ("Edenred") rather than an opaque per-database generated key, so no
    # per-database technical name needs confirming.
    _EDENRED_PROPERTIES_FIELD = 'product_properties'
    _EDENRED_PROPERTY_LABEL = 'Edenred'

    # The 6-product catalog this client uses instead of matching by product
    # name: which 3 apply depends on whether the row's plate matched a
    # fleet.vehicle ("autos") or not ("maquinarias"); within those 3, the
    # actual product is picked by matching the Excel's "Producto / Servicio"
    # text against each candidate's Edenred tags. No tag match -> the
    # category's own "Otros gastos no combustible" product.
    _PRODUCT_CATEGORY_AUTOS_NAMES = [
        'Diesel (autos)', 'Nafta (autos)', 'Otros gastos no combustible (autos)']
    _PRODUCT_CATEGORY_MAQUINARIAS_NAMES = [
        'Diesel (maquinarias)', 'Nafta (maquinarias)', 'Otros gastos no combustible (maquinarias)']
    _PRODUCT_FALLBACK_AUTOS_NAME = 'Otros gastos no combustible (autos)'
    _PRODUCT_FALLBACK_MAQUINARIAS_NAME = 'Otros gastos no combustible (maquinarias)'

    _EXCEL_COLUMN_PLATE = 'Placa'
    _EXCEL_COLUMN_PRODUCT = 'Producto / Servicio'
    # 'Precio neto' is always 0.0 in the real Edenred export (unused/dead
    # column); 'Neto' is the actual net transaction amount (verified against
    # a real file: Neto == Litros * "Neto unitario Lts").
    _EXCEL_COLUMN_PRICE = 'Neto'
    _EXCEL_COLUMN_DATE = 'Fecha'
    _EXCEL_COLUMN_TIME = 'hora'
    _EXCEL_COLUMN_DRIVER = 'Conductor'
    _EXCEL_COLUMN_DRIVER_CODE = 'Código de conductor'
    _EXCEL_COLUMN_STATION = 'Estación de servicio'
    _EXCEL_COLUMN_STATION_ADDRESS = 'Dirección Estación'
    _EXCEL_COLUMN_TRANSACTION = 'No. Transacción'
    _EXCEL_COLUMN_ODOMETER = 'Último odómetro'
    _EXCEL_COLUMN_LITERS = 'Litros'

    _EXPECTED_COLUMNS = [
        _EXCEL_COLUMN_PLATE,
        _EXCEL_COLUMN_PRODUCT,
        _EXCEL_COLUMN_PRICE,
        _EXCEL_COLUMN_DATE,
        _EXCEL_COLUMN_TIME,
        _EXCEL_COLUMN_DRIVER,
        _EXCEL_COLUMN_DRIVER_CODE,
        _EXCEL_COLUMN_STATION,
        _EXCEL_COLUMN_STATION_ADDRESS,
        _EXCEL_COLUMN_TRANSACTION,
        _EXCEL_COLUMN_ODOMETER,
        _EXCEL_COLUMN_LITERS,
    ]

    # Data record shipped by account_fleet, reused so services created here
    # look the same as the ones account_fleet would auto-create at posting.
    _FLEET_SERVICE_TYPE_XMLID = 'account_fleet.data_fleet_service_type_vendor_bill'

    # Exact names of the 3 fixed-amount taxes whose totals this client
    # provides directly (from the Edenred PDF) rather than trusting Odoo's
    # naive per-line fixed-amount computation (see _apply_fixed_tax_totals).
    _TAX_NAME_ITC = 'ITC'
    _TAX_NAME_IDC = 'IDC'
    _TAX_NAME_INTERNAL = 'Impuestos internos'

    excel_file = fields.Binary(string='Excel file', required=True)
    excel_filename = fields.Char(string='Excel filename')
    pdf_file = fields.Binary(string='PDF file', required=True)
    pdf_filename = fields.Char(string='PDF filename')

    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='company_id.currency_id', readonly=True)

    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True,
        domain="[('type', '=', 'purchase'), ('company_id', '=', company_id)]")

    invoice_date = fields.Date(
        string='Invoice date', default=fields.Date.context_today, required=True)
    date = fields.Date(
        string='Accounting date', default=fields.Date.context_today, required=True)

    subtotal = fields.Monetary(
        string='Subtotal', required=True, currency_field='currency_id')

    itc_total = fields.Monetary(
        string='Total ITC', required=True, currency_field='currency_id')
    idc_total = fields.Monetary(
        string='Total IDC', required=True, currency_field='currency_id')
    internal_tax_total = fields.Monetary(
        string='Total Impuestos internos', required=True, currency_field='currency_id')

    # Not required=True at the field level on purpose: action_confirm raises
    # its own UserError when this is empty, which needs to actually be
    # reachable instead of the ORM refusing the record before the button
    # method ever runs. The view marks it required for the user instead.
    fallback_account_id = fields.Many2one(
        'account.account', string='Account for lines without vehicle',
        domain="[('company_ids', 'in', company_id)]")

    # Same reasoning as fallback_account_id re: not required=True here.
    subtotal_difference_account_id = fields.Many2one(
        'account.account', string='Target account for subtotal difference',
        domain="[('company_ids', 'in', company_id)]")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        company = self.env.company

        if 'partner_id' in fields_list and not res.get('partner_id'):
            partner = self.env['res.partner'].search(
                [('name', 'ilike', 'Edenred')], limit=1)
            if partner:
                res['partner_id'] = partner.id

        if 'journal_id' in fields_list and not res.get('journal_id'):
            journal = self.env['account.journal'].search([
                ('type', '=', 'purchase'),
                ('company_id', '=', company.id),
            ], order='id', limit=1)
            if journal:
                res['journal_id'] = journal.id

        if 'fallback_account_id' in fields_list and not res.get('fallback_account_id'):
            account = self.env['account.account'].search([
                ('code', '=', self._FALLBACK_ACCOUNT_DEFAULT_CODE),
                ('company_ids', 'in', company.id),
            ], limit=1)
            if account:
                res['fallback_account_id'] = account.id

        if 'subtotal_difference_account_id' in fields_list and not res.get('subtotal_difference_account_id'):
            account = self.env['account.account'].search([
                ('code', '=', self._SUBTOTAL_DIFFERENCE_ACCOUNT_DEFAULT_CODE),
                ('company_ids', 'in', company.id),
            ], limit=1)
            if account:
                res['subtotal_difference_account_id'] = account.id

        return res

    # -- Excel reading -------------------------------------------------

    def _read_excel_dataframe(self):
        try:
            decoded = base64.b64decode(self.excel_file)
            df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')
        except Exception as e:
            raise UserError(_('Error reading the Excel file: %s', str(e)))

        df.columns = df.columns.str.strip()
        missing = [col for col in self._EXPECTED_COLUMNS if col not in df.columns]
        if missing:
            raise UserError(_(
                'The Excel file is missing the following expected columns: %s',
                ', '.join(missing),
            ))
        return df

    def _filter_valid_rows(self, df):
        product_col = self._EXCEL_COLUMN_PRODUCT
        price_col = self._EXCEL_COLUMN_PRICE
        price_values = pd.to_numeric(df[price_col], errors='coerce').fillna(0)
        mask = (
            df[product_col].notna() & (df[product_col].astype(str).str.strip() != '') &
            (price_values != 0)
        )
        return df[mask].reset_index(drop=True)

    def _parse_row_datetime(self, row):
        fecha_val = row[self._EXCEL_COLUMN_DATE]
        hora_val = row[self._EXCEL_COLUMN_TIME]

        # dayfirst=True: the real Edenred export stores Fecha as DD/MM/YYYY
        # text (Argentine convention), which pandas would otherwise parse as
        # month-first and silently swap day/month (e.g. 11/8 -> November 8
        # instead of August 11).
        fecha_ts = pd.to_datetime(fecha_val, dayfirst=True)
        date_part = fecha_ts.date()

        if pd.isna(hora_val):
            time_part = fecha_ts.time()
        elif isinstance(hora_val, dt_time):
            time_part = hora_val
        elif isinstance(hora_val, datetime):
            time_part = hora_val.time()
        else:
            time_part = pd.to_datetime(str(hora_val)).time()

        return datetime.combine(date_part, time_part)

    # -- Matching --------------------------------------------------------

    def _get_edenred_tags(self, product):
        """Return the set of (normalized) tag labels currently selected in
        the "Edenred" property (a 'tags'-type entry in product_properties,
        defined per product category) for this product.
        """
        properties = product.read([self._EDENRED_PROPERTIES_FIELD])[0][self._EDENRED_PROPERTIES_FIELD]
        prop = next(
            (p for p in properties if p.get('string') == self._EDENRED_PROPERTY_LABEL),
            None,
        )
        if not prop or prop.get('type') != 'tags':
            return set()
        selected_keys = set(prop.get('value') or [])
        return {
            str(label).strip().upper()
            for key, label, *_rest in (prop.get('tags') or [])
            if key in selected_keys
        }

    def _select_product(self, vehicle, product_name):
        if vehicle:
            candidate_names = self._PRODUCT_CATEGORY_AUTOS_NAMES
            fallback_name = self._PRODUCT_FALLBACK_AUTOS_NAME
        else:
            candidate_names = self._PRODUCT_CATEGORY_MAQUINARIAS_NAMES
            fallback_name = self._PRODUCT_FALLBACK_MAQUINARIAS_NAME

        candidates = self.env['product.product'].search([('name', 'in', candidate_names)])
        target = str(product_name).strip().upper()
        if target:
            for product in candidates:
                if target in self._get_edenred_tags(product):
                    return product

        fallback_product = candidates.filtered(lambda p: p.name == fallback_name)
        if not fallback_product:
            raise UserError(_('Could not find the "%s" product.', fallback_name))
        return fallback_product[:1]

    def _match_vehicle(self, plate):
        clean_plate = str(plate).strip().upper()
        if not clean_plate:
            return self.env['fleet.vehicle']
        vehicles = self.env['fleet.vehicle'].search([
            ('company_id', 'in', [self.company_id.id, False]),
        ])
        return vehicles.filtered(
            lambda v: (v.license_plate or '').strip().upper() == clean_plate
        )[:1]

    def _normalize_name(self, name):
        return sorted(re.sub(r'\s+', ' ', str(name or '')).strip().upper().split(' '))

    def _match_driver_partner(self, conductor_name):
        target = self._normalize_name(conductor_name)
        if not target or target == ['']:
            return self.env['res.partner']
        employees = self.env['hr.employee'].search([('work_contact_id', '!=', False)])
        matches = employees.filtered(lambda e: self._normalize_name(e.name) == target)
        if len(matches) == 1:
            return matches.work_contact_id
        return self.env['res.partner']

    # -- Line building -----------------------------------------------------

    def _build_line_description(self, row, row_datetime):
        return '%(datetime)s - %(driver)s (%(driver_code)s) - %(station)s (%(address)s) - %(transaction)s' % {
            'datetime': row_datetime.strftime('%d/%m/%Y %H:%M'),
            'driver': str(row[self._EXCEL_COLUMN_DRIVER]).strip(),
            'driver_code': str(row[self._EXCEL_COLUMN_DRIVER_CODE]).strip(),
            'station': str(row[self._EXCEL_COLUMN_STATION]).strip(),
            'address': str(row[self._EXCEL_COLUMN_STATION_ADDRESS]).strip(),
            'transaction': str(row[self._EXCEL_COLUMN_TRANSACTION]).strip(),
        }

    def _build_service_description(self, row):
        product_name = str(row[self._EXCEL_COLUMN_PRODUCT]).strip()
        liters = row[self._EXCEL_COLUMN_LITERS]
        liters_value = 0.0 if pd.isna(liters) else float(liters)
        return '%s %.2f L' % (product_name, liters_value)

    def _prepare_line_vals(self, row, row_datetime):
        vehicle = self._match_vehicle(row[self._EXCEL_COLUMN_PLATE])
        product = self._select_product(vehicle, row[self._EXCEL_COLUMN_PRODUCT])
        name = self._build_line_description(row, row_datetime)

        vals = {
            'name': name,
            'quantity': 1.0,
            'price_unit': float(row[self._EXCEL_COLUMN_PRICE]),
            'product_id': product.id,
        }
        if vehicle:
            vals['vehicle_id'] = vehicle.id
        else:
            # No fleet.vehicle match -> keep the product (from the
            # "maquinarias" catalog) but override its own account with the
            # fallback, per the confirmed rule.
            vals['account_id'] = self.fallback_account_id.id
        return vals, vehicle

    # -- Vehicle driver / odometer sync -------------------------------------

    def _upsert_odometer(self, vehicle, log_date, value, driver_partner):
        odometer = self.env['fleet.vehicle.odometer'].search([
            ('vehicle_id', '=', vehicle.id),
            ('date', '=', log_date),
        ], limit=1)
        vals = {
            'value': value,
            'driver_id': driver_partner.id if driver_partner else False,
        }
        if odometer:
            odometer.write(vals)
        else:
            vals.update({'vehicle_id': vehicle.id, 'date': log_date})
            self.env['fleet.vehicle.odometer'].create(vals)

    def _sync_vehicles_drivers_and_odometers(self, vehicle_rows):
        for vehicle, rows in vehicle_rows.items():
            row_datetime, row = max(rows, key=lambda item: item[0])
            driver_partner = self._match_driver_partner(row[self._EXCEL_COLUMN_DRIVER])

            if driver_partner and vehicle.driver_id != driver_partner:
                vehicle.write({'driver_id': driver_partner.id})

            odometer_value = row[self._EXCEL_COLUMN_ODOMETER]
            self._upsert_odometer(
                vehicle, row_datetime.date(), float(odometer_value), driver_partner)

    def _create_fleet_log_services(self, move, line_extras):
        """Create the per-line fleet.vehicle.log.services records ourselves,
        with the actual row data, instead of letting account_fleet's own
        _post() auto-create bare ones later. Linking account_move_line_id
        here makes line.vehicle_log_service_ids non-empty, which is exactly
        the condition account_fleet checks to skip its own auto-creation -
        so no duplicates get created once the bill is posted.
        """
        service_type = self.env.ref(self._FLEET_SERVICE_TYPE_XMLID, raise_if_not_found=False)
        if not service_type:
            return

        product_lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        row_lines = product_lines[:len(line_extras)]

        vals_list = []
        for line, extra in zip(row_lines, line_extras):
            vehicle = extra['vehicle']
            if not vehicle:
                continue
            odometer = self.env['fleet.vehicle.odometer'].search([
                ('vehicle_id', '=', vehicle.id),
                ('date', '=', extra['row_datetime'].date()),
            ], limit=1)
            vals_list.append({
                'vehicle_id': vehicle.id,
                'service_type_id': service_type.id,
                'vendor_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'account_move_line_id': line.id,
                'description': extra['service_description'],
                'date': extra['row_datetime'].date(),
                'notes': extra['notes'],
                'odometer_id': odometer.id if odometer else False,
            })
        if vals_list:
            self.env['fleet.vehicle.log.services'].create(vals_list)

    def _set_tax_total(self, move, tax_name, target_total):
        """Force the total of a fixed-amount tax's line(s) on `move` to
        `target_total`, without ever deleting a tax line.

        The 3 fixed-amount taxes (ITC, IDC, Impuestos internos) are all
        configured with a placeholder amount (1.00 per unit); the real
        totals come from the Edenred PDF instead and are entered on the
        wizard. Since edenred doesn't use analytic_distribution, all the
        product lines sharing a given tax normally consolidate into a
        single tax line - but just in case they don't (e.g. a future
        change reintroduces a distinguishing dimension), the total is
        redistributed proportionally across every existing line for that
        tax, with the last one absorbing the rounding, exactly like
        ypf_route's fix for the same "never delete a tax line" constraint
        (PostgreSQL's check_amount_currency_balance_sign check breaks
        otherwise on the next edit).
        """
        tax_lines = move.line_ids.filtered(
            lambda l: l.tax_line_id and l.tax_line_id.name == tax_name)
        if not tax_lines:
            if move.currency_id.is_zero(target_total):
                return
            raise UserError(_(
                'Could not find a tax line named "%s" on the created bill.', tax_name))

        sign = -1 if move.is_inbound() else 1
        target = float(target_total) * sign
        current_total = sum(tax_lines.mapped('amount_currency'))

        remaining = target
        for line in tax_lines[:-1]:
            if move.currency_id.is_zero(current_total):
                share = move.currency_id.round(target / len(tax_lines))
            else:
                share = move.currency_id.round(line.amount_currency / current_total * target)
            line.with_context(check_move_validity=False).amount_currency = share
            remaining -= share
        tax_lines[-1].with_context(check_move_validity=False).amount_currency = remaining

    def _apply_fixed_tax_totals(self, move):
        internal_tax_net = self.internal_tax_total - self.itc_total - self.idc_total
        self._set_tax_total(move, self._TAX_NAME_ITC, self.itc_total)
        self._set_tax_total(move, self._TAX_NAME_IDC, self.idc_total)
        self._set_tax_total(move, self._TAX_NAME_INTERNAL, internal_tax_net)
        move._compute_amount()

    def _prepare_subtotal_difference_line_vals(self, diff, taxes):
        """`taxes` is the union of every real (product-matched) line's own
        purchase taxes, attached here too so the difference line is taxed
        the same way as the rest of the invoice (IVA, ITC, IDC, Impuestos
        internos all included when the invoice's products carry them) -
        it's still part of the taxable net amount, not an untaxed line.

        This has to happen at build time, before the move is created: the
        fixed-amount taxes (ITC/IDC/Impuestos internos) get their totals
        redistributed across whatever lines carry them in
        _apply_fixed_tax_totals, so the difference line needs to already
        be one of those lines when that runs, not patched in afterwards
        (which would silently add its own extra $1-per-tax contribution
        on top of the totals we just set).
        """
        vals = {
            'name': _('Subtotal difference'),
            'quantity': 1.0,
            'price_unit': diff,
            'account_id': self.subtotal_difference_account_id.id,
        }
        if taxes:
            vals['tax_ids'] = [(6, 0, taxes.ids)]
        return vals

    def _finalize_subtotal_difference_line(self, move):
        """Hook for country-specific glue modules that need to double-check
        the subtotal-difference line after the move is created (e.g.
        confirming a localization's own tax-group rule is satisfied). Only
        ever ADD taxes here (never replace tax_ids outright) - the line
        already carries the real lines' own taxes from
        _prepare_subtotal_difference_line_vals by this point. No-op here:
        the base module doesn't assume any particular tax setup.
        """

    # -- Move creation -------------------------------------------------------

    def _prepare_move_vals(self):
        self.ensure_one()
        return {
            'move_type': 'in_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': self.invoice_date,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
        }

    def _attach_source_files(self, move):
        self.env['ir.attachment'].create([
            {
                'name': self.excel_filename or 'Edenred.xlsx',
                'datas': self.excel_file,
                'res_model': 'account.move',
                'res_id': move.id,
                'type': 'binary',
            },
            {
                'name': self.pdf_filename or 'Edenred.pdf',
                'datas': self.pdf_file,
                'res_model': 'account.move',
                'res_id': move.id,
                'type': 'binary',
            },
        ])

    def _post_import_notes(self, move, unmatched_plates, diff):
        sections = []
        if unmatched_plates:
            plate_lines = '<br/>'.join(
                '* %s' % plate for plate in sorted(unmatched_plates))
            sections.append(
                'Patentes que no figuran en el módulo de Flotilla:<br/>%s' % plate_lines)
        if abs(diff) > 0.01:
            amount = formatLang(self.env, diff, currency_obj=move.currency_id)
            sections.append(
                'Se encontró una diferencia entre el excel y el subtotal '
                'de la factura por %s' % amount)
        if sections:
            move.message_post(body='<p>%s</p>' % '</p><br/><p>'.join(sections))

    def action_confirm(self):
        self.ensure_one()
        if not self.fallback_account_id:
            raise UserError(_('Please set an account for lines without a matched vehicle.'))
        if not self.subtotal_difference_account_id:
            raise UserError(_('Please set a target account for the subtotal difference.'))

        df = self._read_excel_dataframe()
        df = self._filter_valid_rows(df)
        if df.empty:
            raise UserError(_('No valid rows were found in the Excel file.'))

        invoice_lines = []
        vehicle_rows = {}
        line_extras = []
        line_taxes = self.env['account.tax']
        unmatched_plates = set()

        for _index, row in df.iterrows():
            row_datetime = self._parse_row_datetime(row)
            vals, vehicle = self._prepare_line_vals(row, row_datetime)
            invoice_lines.append((0, 0, vals))
            line_extras.append({
                'vehicle': vehicle,
                'row_datetime': row_datetime,
                'service_description': self._build_service_description(row),
                'notes': vals['name'],
            })
            if vehicle:
                vehicle_rows.setdefault(vehicle, []).append((row_datetime, row))
            else:
                plate = str(row[self._EXCEL_COLUMN_PLATE]).strip().upper()
                if plate:
                    unmatched_plates.add(plate)
            product = self.env['product.product'].browse(vals['product_id'])
            line_taxes |= product.supplier_taxes_id.filtered(
                lambda t: t.type_tax_use == 'purchase')

        lines_total = sum(vals['price_unit'] for _cmd, _id, vals in invoice_lines)
        diff = self.subtotal - lines_total
        if abs(diff) > 0.01:
            invoice_lines.append(
                (0, 0, self._prepare_subtotal_difference_line_vals(diff, line_taxes)))

        move_vals = self._prepare_move_vals()
        move_vals['invoice_line_ids'] = invoice_lines
        move = self.env['account.move'].create(move_vals)

        self._apply_fixed_tax_totals(move)
        self._finalize_subtotal_difference_line(move)
        self._sync_vehicles_drivers_and_odometers(vehicle_rows)
        self._create_fleet_log_services(move, line_extras)
        self._attach_source_files(move)
        self._post_import_notes(move, unmatched_plates, diff)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
            'target': 'current',
        }
