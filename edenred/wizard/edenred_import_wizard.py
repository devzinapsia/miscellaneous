import base64
import io
import re
from datetime import datetime
from datetime import time as dt_time

import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EdenredImportWizard(models.TransientModel):
    _name = 'edenred.import.wizard'
    _description = 'Edenred Fuel Invoice Import Wizard'

    # Default code used only to look up a sensible default for
    # `fallback_account_id` - not referenced anywhere else in the module.
    _FALLBACK_ACCOUNT_DEFAULT_CODE = '5.3.1.01.148'
    _NAFTA_SUPER_PRODUCT_NAME = 'Nafta Super'

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

    # Not required=True at the field level on purpose: action_confirm raises
    # its own UserError when this is empty, which needs to actually be
    # reachable instead of the ORM refusing the record before the button
    # method ever runs. The view marks it required for the user instead.
    fallback_account_id = fields.Many2one(
        'account.account', string='Account for lines without vehicle',
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

    def _match_product(self, product_name):
        name = str(product_name).strip()
        if not name:
            return self.env['product.product']
        # Case-insensitive exact match ('=ilike' does not add wildcards): the
        # Excel and the product catalog don't always agree on case (e.g.
        # "Nafta Super" vs "NAFTA SUPER").
        return self.env['product.product'].search([('name', '=ilike', name)], limit=1)

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
        product = self._match_product(row[self._EXCEL_COLUMN_PRODUCT])
        vehicle = self._match_vehicle(row[self._EXCEL_COLUMN_PLATE])
        name = self._build_line_description(row, row_datetime)

        vals = {
            'name': name,
            'quantity': 1.0,
            'price_unit': float(row[self._EXCEL_COLUMN_PRICE]),
        }
        if vehicle:
            vals['vehicle_id'] = vehicle.id
        if product:
            vals['product_id'] = product.id
            if not vehicle:
                vals['account_id'] = self.fallback_account_id.id
        else:
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

    def action_confirm(self):
        self.ensure_one()
        if not self.fallback_account_id:
            raise UserError(_('Please set an account for lines without a matched vehicle.'))

        df = self._read_excel_dataframe()
        df = self._filter_valid_rows(df)
        if df.empty:
            raise UserError(_('No valid rows were found in the Excel file.'))

        invoice_lines = []
        vehicle_rows = {}
        line_extras = []

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

        lines_total = sum(vals['price_unit'] for _cmd, _id, vals in invoice_lines)
        diff = self.subtotal - lines_total
        if abs(diff) > 0.01:
            nafta_super = self.env['product.product'].search(
                [('name', '=ilike', self._NAFTA_SUPER_PRODUCT_NAME)], limit=1)
            if not nafta_super:
                raise UserError(_(
                    'Could not find a product named "%s" to post the subtotal difference.',
                    self._NAFTA_SUPER_PRODUCT_NAME,
                ))
            invoice_lines.append((0, 0, {
                'product_id': nafta_super.id,
                'name': nafta_super.name,
                'quantity': 1.0,
                'price_unit': diff,
                'account_id': self.fallback_account_id.id,
            }))

        move_vals = self._prepare_move_vals()
        move_vals['invoice_line_ids'] = invoice_lines
        move = self.env['account.move'].create(move_vals)

        self._sync_vehicles_drivers_and_odometers(vehicle_rows)
        self._create_fleet_log_services(move, line_extras)
        self._attach_source_files(move)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
            'target': 'current',
        }
