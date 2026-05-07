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
    file_name = fields.Char(string='Nombre del archivo') # Para el adjunto

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
            ('code', '=', '1'), 
            ('country_id.code', '=', 'AR')
        ], limit=1)
        if doc_type:
            res['l10n_latam_document_type_id'] = doc_type.id
        return res

    def action_confirm(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.pop('default_move_type', None)
        
        try:
            decoded_data = base64.b64decode(self.excel_file)
            df = pd.read_excel(io.BytesIO(decoded_data), engine='openpyxl')
            df.columns = df.columns.str.strip()
            # Limpieza básica de filas vacías al final
            df = df.dropna(how='all').reset_index(drop=True)
        except Exception as e:
            raise UserError("Error al procesar el archivo Excel: %s" % str(e))
        
        invoice_lines = []
        col_product = 'PRODUCTO'
        col_total = 'IMP TOT YER'
        col_dominio = 'IDENTIFICACION TARJETA'
        tax_columns = ['IVA', 'IMP CO2', 'TASA VIAL', 'IMP COMB LIQ']

        if self.group_type == 'line':
            for _, row in df.iterrows():
                total_row = float(row.get(col_total, 0) or 0)
                taxes_sum = sum(float(row.get(tax, 0) or 0) for tax in tax_columns if tax in row)
                price = total_row - taxes_sum
                if price <= 0: continue

                vals = self._prepare_line_vals(
                    product_name=str(row.get(col_product, '')).strip(), 
                    price=price, 
                    domain=row.get(col_dominio, False)
                )
                invoice_lines.append((0, 0, vals))
        
        else: # Agrupado por Producto
            df = df.fillna(0)
            available_tax_cols = [t for t in tax_columns if t in df.columns]
            grouped = df.groupby(col_product)[[col_total] + available_tax_cols].sum().reset_index()

            for _, row in grouped.iterrows():
                total_prod_group = float(row[col_total])
                taxes_sum = sum(float(row.get(tax, 0)) for tax in available_tax_cols)
                price = total_prod_group - taxes_sum
                if price <= 0: continue
                
                distribution = {}
                if self.use_analytic_domain:
                    # Buscamos todas las líneas originales de este producto
                    sub_df = df[df[col_product] == row[col_product]]
                    for _, sub_row in sub_df.iterrows():
                        clean_pat = str(sub_row.get(col_dominio, '')).replace(" ", "").upper()
                        if not clean_pat: continue
                        
                        ana_acc = self.env['account.analytic.account'].search([
                            ('name', 'ilike', clean_pat + '%')
                        ], limit=1)
                        
                        if ana_acc:
                            # Calculamos el peso proporcional de esta carga sobre el total del grupo
                            weight = (sub_row[col_total] / total_prod_group) * 100
                            distribution[str(ana_acc.id)] = distribution.get(str(ana_acc.id), 0) + weight

                vals = self._prepare_line_vals(
                    product_name=str(row[col_product]).strip(), 
                    price=price, 
                    analytic_dist=distribution
                )
                invoice_lines.append((0, 0, vals))

        if not invoice_lines:
            raise UserError("No se encontraron líneas válidas.")

        # Crear Factura
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

        # --- PUNTO 1: Adjuntar archivo ---
        self.env['ir.attachment'].create({
            'name': self.file_name or 'YPF_Ruta.xlsx',
            'datas': self.excel_file,
            'res_model': 'account.move',
            'res_id': move.id,
            'type': 'binary',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
            'target': 'current',
        }

    def _prepare_line_vals(self, product_name, price, domain=False, analytic_dist=False):
        product = self.env['product.product'].search([('name', '=', product_name)], limit=1)
        res = {
            'product_id': product.id if product else False,
            'name': product_name,
            'quantity': 1.0,
            'price_unit': price,
            'tax_ids': [(6, 0, product.supplier_taxes_id.ids)] if product else [],
        }
        if self.use_analytic_domain:
            if analytic_dist:
                res['analytic_distribution'] = {str(k): round(v, 2) for k, v in analytic_dist.items()}
            elif domain:
                clean_pat = str(domain).replace(" ", "").upper()
                ana_acc = self.env['account.analytic.account'].search([('name', 'ilike', clean_pat + '%')], limit=1)
                if ana_acc:
                    res['analytic_distribution'] = {str(ana_acc.id): 100}
        return res