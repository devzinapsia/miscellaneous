import io
import base64
import pandas as pd
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class YpfImportWizard(models.TransientModel):
    _name = 'ypf.import.wizard'
    _description = 'Wizard Importador YPF Ruta'

    partner_id = fields.Many2one('res.partner', string='Proveedor', required=True)
    invoice_date = fields.Date(string='Fecha Factura', default=fields.Date.context_today, required=True)
    date = fields.Date(string='Fecha Contable', default=fields.Date.context_today, required=True)
    invoice_date_due = fields.Date(string='Fecha de Vencimiento')

    journal_id = fields.Many2one('account.journal', string='Diario',
        domain=[('type', '=', 'purchase')], required=True)

    l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo de documento')
    document_number = fields.Char(string='Número de Documento')

    excel_file = fields.Binary(string='Subir planilla excel', required=True)
    file_name = fields.Char(string='Nombre del archivo')

    group_type = fields.Selection([
        ('line', 'Abierto por Renglon'),
        ('product', 'Agrupado por Producto')
    ], string='Modo de Importación', default='product', required=True)

    use_analytic_domain = fields.Boolean(string='Usa cuenta analítica', default=True)

    # Impuestos fijos que vienen del Excel — se sacan de tax_ids de las líneas
    # y sus montos se sobreescriben via tax_override_data
    FIXED_TAX_NAMES = ['ITC', 'ICO2', 'Tasa vial']

    # Mapeo columna Excel -> nombre exacto del impuesto en Odoo
    TAX_COLUMN_MAP = {
        'IMP CO2':      'ICO2',
        'TASA VIAL':    'Tasa vial',
        'IMP COMB LIQ': 'ITC',
    }

    @api.model
    def default_get(self, fields_list):
        res = super(YpfImportWizard, self).default_get(fields_list)
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        res['journal_id'] = journal.id if journal else False
        doc_type = self.env['l10n_latam.document.type'].search([
            ('code', '=', '1'),
            ('country_id.code', '=', 'AR')
        ], limit=1)
        if doc_type:
            res['l10n_latam_document_type_id'] = doc_type.id
        return res

    def _filter_valid_rows(self, df, col_product):
        """Filtra filas con PRODUCTO válido, eliminando totales y filas vacías del Excel."""
        mask = (
            df[col_product].notna() &
            (df[col_product] != 0) &
            (df[col_product].astype(str).str.strip() != '') &
            (df[col_product].astype(str).str.strip() != '0')
        )
        return df[mask].reset_index(drop=True)

    def _get_product_taxes(self, product):
        """Retorna solo los impuestos NO fijos del Excel (IVA%, P.IIBB, Perc IVA, etc)."""
        if not product:
            return []
        return product.supplier_taxes_id.filtered(
            lambda t: t.name not in self.FIXED_TAX_NAMES
        ).ids

    def _build_tax_override_data(self, df):
        """
        Construye el dict tax_override_data para sobreescribir los montos
        de ITC, ICO2 y Tasa vial con los totales del Excel.
        Busca los IDs de impuestos dinámicamente.
        Formato: { str(tax_id): {'amount': total, 'rate': 1} }
        """
        override = {}
        for col, tax_name in self.TAX_COLUMN_MAP.items():
            if col not in df.columns:
                continue
            total = pd.to_numeric(df[col], errors='coerce').fillna(0).sum()
            if total <= 0:
                continue
            tax = self.env['account.tax'].search([
                ('name', '=', tax_name),
                ('type_tax_use', '=', 'purchase'),
            ], limit=1)
            if tax:
                override[str(tax.id)] = {'amount': float(total), 'rate': 1}
        return override

    def action_confirm(self):
        self.ensure_one()
        # check_move_validity=False permite modificar líneas sin que Odoo bloquee el asiento 
        # por estar temporalmente desbalanceado durante el ajuste.
        ctx = self.env.context.with_context(check_move_validity=False)

        try:
            decoded_data = base64.b64decode(self.excel_file)
            df = pd.read_excel(io.BytesIO(decoded_data), engine='openpyxl')
            df.columns = df.columns.str.strip()
            df = df.dropna(how='all').reset_index(drop=True)
            df = self._filter_valid_rows(df, 'PRODUCTO')
        except Exception as e:
            raise UserError("Error al procesar el archivo Excel: %s" % str(e))

        # --- PARTE 1: Líneas de productos ---
        invoice_lines = []
        for _, row in df.iterrows():
            # El neto para la línea lo calculamos restando TODOS los impuestos del total del renglón
            total_row = float(row.get('IMP TOT YER', 0))
            iva_row = float(row.get('IVA', 0))
            itc_row = float(row.get('IMP COMB LIQ', 0))
            ico2_row = float(row.get('IMP CO2', 0))
            tasa_row = float(row.get('TASA VIAL', 0))
            
            # Neto que Odoo usará como base imponible
            price_neto = total_row - iva_row - itc_row - ico2_row - tasa_row
            
            if price_neto <= 0: continue
            
            vals = self._prepare_line_vals(
                product_name=str(row.get('PRODUCTO', '')).strip(),
                price=price_neto,
                domain=row.get('IDENTIFICACION TARJETA', False)
            )
            invoice_lines.append((0, 0, vals))

        # --- PARTE 2: Crear factura ---
        move = self.env['account.move'].with_context(ctx).create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': self.invoice_date,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'l10n_latam_document_type_id': self.l10n_latam_document_type_id.id,
            'l10n_latam_document_number': self.document_number,
            'invoice_line_ids': invoice_lines,
        })

        # --- PARTE 3: El "Ajuste Fino" (Sustento en l10n_ar grep) ---
        # Recolectamos los totales reales del Excel
        excel_taxes = {
            '01': df['IVA'].sum(),            # IVA
            '04': df['IMP COMB LIQ'].sum() + df['IMP CO2'].sum(), # Internos
            '99': df['TASA VIAL'].sum(),       # Otros (Tasa vial suele ir como 99 u 08)
        }

        # Buscamos las líneas de impuestos que Odoo creó y pisamos sus montos
        for line in move.line_ids.filtered(lambda l: l.display_type == 'tax'):
            afip_code = line.tax_line_id.tax_group_id.l10n_ar_tribute_afip_code
            if afip_code in excel_taxes:
                monto_real = excel_taxes[afip_code]
                # En facturas de proveedor, el impuesto va al Debe (positivo)
                line.update({
                    'debit': monto_real,
                    'credit': 0.0,
                    'amount_currency': monto_real if move.currency_id == move.company_id.currency_id else line.amount_currency
                })

        # --- PARTE 4: Balancear la cuenta a pagar ---
        # Una vez ajustados los impuestos, el total de la factura (cuenta a pagar) 
        # debe ser la suma exacta de todo lo anterior.
        total_final_excel = df['IMP TOT YER'].sum()
        payable_line = move.line_ids.filtered(lambda l: l.display_type == 'payment_term')
        if payable_line:
            payable_line.update({
                'debit': 0.0,
                'credit': total_final_excel,
                'amount_currency': -total_final_excel if move.currency_id == move.company_id.currency_id else payable_line.amount_currency
            })

        # Adjunto de auditoría
        self.env['ir.attachment'].create({
            'name': self.file_name or 'YPF_Ruta.xlsx',
            'datas': self.excel_file,
            'res_model': 'account.move', 'res_id': move.id, 'type': 'binary',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _prepare_line_vals(self, product_name, price, domain=False, analytic_dist=False):
        product = self.env['product.product'].search([('name', '=', product_name)], limit=1)
        res = {
            'product_id': product.id if product else False,
            'name': product_name,
            'quantity': 1.0,
            'price_unit': price,
            # Solo impuestos NO fijos del Excel — IVA%, P.IIBB, Perc IVA quedan
            # ITC, ICO2, Tasa vial se sobreescriben via tax_override_data
            'tax_ids': [(6, 0, self._get_product_taxes(product))],
        }
        if self.use_analytic_domain:
            if analytic_dist:
                res['analytic_distribution'] = {str(k): round(v, 2) for k, v in analytic_dist.items()}
            elif domain:
                clean_pat = str(domain).replace(" ", "").upper()
                if clean_pat and clean_pat != '0':
                    ana_acc = self.env['account.analytic.account'].search([
                        ('name', 'ilike', clean_pat + '%')
                    ], limit=1)
                    if ana_acc:
                        res['analytic_distribution'] = {str(ana_acc.id): 100}
        return res