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
    journal_id = fields.Many2one('account.journal', string='Diario', domain=[('type', '=', 'purchase')], required=True)
    l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo de documento')
    document_number = fields.Char(string='Número de Documento')
    excel_file = fields.Binary(string='Subir planilla excel', required=True)
    file_name = fields.Char(string='Nombre del archivo')
    group_type = fields.Selection([
        ('line', 'Abierto por Renglon'),
        ('product', 'Agrupado por Producto')
    ], string='Modo de Importación', default='product', required=True)
    use_analytic_domain = fields.Boolean(string='Usa cuenta analítica', default=True)

    @api.model
    def default_get(self, fields_list):
        res = super(YpfImportWizard, self).default_get(fields_list)
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        res['journal_id'] = journal.id if journal else False
        doc_type = self.env['l10n_latam.document.type'].search([
            ('code', '=', '1'), ('country_id.code', '=', 'AR')
        ], limit=1)
        if doc_type:
            res['l10n_latam_document_type_id'] = doc_type.id
        return res

    def _filter_valid_rows(self, df, col_product):
        mask = (df[col_product].notna() & (df[col_product] != 0) & 
                (df[col_product].astype(str).str.strip() != '') & 
                (df[col_product].astype(str).str.strip() != '0'))
        return df[mask].reset_index(drop=True)

    def action_confirm(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.pop('default_move_type', None)

        try:
            decoded_data = base64.b64decode(self.excel_file)
            df = pd.read_excel(io.BytesIO(decoded_data), engine='openpyxl')
            df.columns = df.columns.str.strip()
            df = df.dropna(how='all').reset_index(drop=True)
            df = self._filter_valid_rows(df, 'PRODUCTO')
            df_filled = df.fillna(0)
        except Exception as e:
            raise UserError("Error al procesar el archivo Excel: %s" % str(e))

        invoice_lines = []
        fixed_tax_cols = {
            'IMP COMB LIQ': 'ITC',
            'IMP CO2': 'ICO2',
            'TASA VIAL': 'Tasa vial'
        }

        # 1. PROCESAR PRODUCTOS (Sólo IVA)
        if self.group_type == 'line':
            for _, row in df_filled.iterrows():
                taxes_fijos_row = sum(float(row.get(c, 0)) for c in fixed_tax_cols.keys())
                iva_row = float(row.get('IVA', 0))
                price = float(row.get('IMP TOT YER', 0)) - iva_row - taxes_fijos_row
                
                if price <= 0: continue
                
                vals = self._prepare_line_vals(str(row.get('PRODUCTO', '')).strip(), price, domain=row.get('IDENTIFICACION TARJETA', False))
                invoice_lines.append((0, 0, vals))
        else:
            grouped = df_filled.groupby('PRODUCTO').sum(numeric_only=True).reset_index()
            for _, row in grouped.iterrows():
                taxes_fijos_group = sum(float(row.get(c, 0)) for c in fixed_tax_cols.keys())
                iva_group = float(row.get('IVA', 0))
                price = float(row['IMP TOT YER']) - iva_group - taxes_fijos_group
                
                if price <= 0: continue

                distribution = {}
                if self.use_analytic_domain:
                    sub_df = df_filled[df_filled['PRODUCTO'] == row['PRODUCTO']]
                    total_prod_group = row['IMP TOT YER']
                    for _, sub_row in sub_df.iterrows():
                        clean_pat = str(sub_row.get('IDENTIFICACION TARJETA', '')).replace(" ", "").upper()
                        ana_acc = self.env['account.analytic.account'].search([('name', 'ilike', clean_pat + '%')], limit=1)
                        if ana_acc:
                            weight = (sub_row['IMP TOT YER'] / total_prod_group) * 100
                            distribution[str(ana_acc.id)] = distribution.get(str(ana_acc.id), 0) + weight

                vals = self._prepare_line_vals(str(row['PRODUCTO']).strip(), price, analytic_dist=distribution)
                invoice_lines.append((0, 0, vals))

        # 2. PROCESAR IMPUESTOS FIJOS (Líneas de ajuste contable)
        for col, tax_name in fixed_tax_cols.items():
            total_tax_amount = df_filled[col].sum()
            if total_tax_amount > 0:
                tax_id = self.env['account.tax'].search([('name', '=', tax_name), ('type_tax_use', '=', 'purchase')], limit=1)
                account_id = False
                if tax_id:
                    repartition_line = tax_id.invoice_repartition_line_ids.filtered(lambda x: x.repartition_type == 'tax')
                    account_id = repartition_line.account_id.id if repartition_line else False
                
                invoice_lines.append((0, 0, {
                    'name': tax_name,
                    'quantity': 1.0,
                    'price_unit': total_tax_amount,
                    'tax_ids': [], 
                    'account_id': account_id or self.journal_id.default_account_id.id,
                }))

        # 3. CREAR FACTURA Y ADJUNTAR
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

        self.env['ir.attachment'].create({
            'name': self.file_name or 'YPF_Ruta.xlsx',
            'datas': self.excel_file,
            'res_model': 'account.move', 'res_id': move.id, 'type': 'binary',
        })

        return {'type': 'ir.actions.act_window', 'res_model': 'account.move', 'res_id': move.id, 'view_mode': 'form', 'target': 'current'}

    def _prepare_line_vals(self, product_name, price, domain=False, analytic_dist=False):
        product = self.env['product.product'].search([('name', '=', str(product_name).strip())], limit=1)
        taxes_to_apply = product.supplier_taxes_id.filtered(lambda t: t.name not in ['ITC', 'ICO2', 'Tasa vial']).ids if product else []
        res = {
            'product_id': product.id if product else False,
            'name': product_name,
            'quantity': 1.0,
            'price_unit': price,
            'tax_ids': [(6, 0, taxes_to_apply)],
        }
        if self.use_analytic_domain:
            if analytic_dist:
                res['analytic_distribution'] = {str(k): round(v, 2) for k, v in analytic_dist.items()}
            elif domain:
                clean_pat = str(domain).replace(" ", "").upper()
                if clean_pat and clean_pat != '0':
                    ana_acc = self.env['account.analytic.account'].search([('name', 'ilike', clean_pat + '%')], limit=1)
                    if ana_acc: res['analytic_distribution'] = {str(ana_acc.id): 100}
        return res