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
        """Retorna todos los impuestos del producto. Odoo los consolida al pie."""
        if not product:
            return []
        return product.supplier_taxes_id.ids

    def _apply_fixed_tax_amounts(self, df, move):
        """
        Para cada impuesto fijo (ITC, ICO2, Tasa vial):
        1. Elimina las líneas duplicadas del pie (una por cada artículo)
        2. Deja solo la primera línea con el monto total del Excel
        Replica el comportamiento de editar manualmente el pie de la factura.
        """
        # in_invoice es inbound → sign = -1
        sign = -1 if move.is_inbound() else 1

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
            if not tax:
                continue

            # Buscar todas las líneas del pie correspondientes a este impuesto
            tax_lines = move.line_ids.filtered(
                lambda l, t=tax.id: l.tax_line_id.id == t
            )
            if not tax_lines:
                continue

            # Eliminar duplicados — dejar solo la primera línea
            first_line = tax_lines[0]
            duplicates = tax_lines[1:]
            if duplicates:
                duplicates.with_context(
                    dynamic_unlink=True,
                    check_move_validity=False,
                ).unlink()

            # Ajustar el monto de la primera línea al total del Excel
            first_line.with_context(
                check_move_validity=False
            ).amount_currency = float(total) * sign

        # Recomputar totales del move
        move._compute_amount()

    def action_confirm(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.pop('default_move_type', None)

        try:
            decoded_data = base64.b64decode(self.excel_file)
            df = pd.read_excel(io.BytesIO(decoded_data), engine='openpyxl')
            df.columns = df.columns.str.strip()
            df = df.dropna(how='all').reset_index(drop=True)
        except Exception as e:
            raise UserError("Error al procesar el archivo Excel: %s" % str(e))

        col_product = 'PRODUCTO'
        col_total = 'IMP TOT YER'
        col_dominio = 'IDENTIFICACION TARJETA'
        tax_columns = ['IVA', 'IMP CO2', 'TASA VIAL', 'IMP COMB LIQ']

        # Filtrar filas de totales y vacías
        df = self._filter_valid_rows(df, col_product)

        invoice_lines = []

        if self.group_type == 'line':
            for _, row in df.iterrows():
                total_row = float(row.get(col_total, 0) or 0)
                taxes_sum = sum(float(row.get(tax, 0) or 0) for tax in tax_columns if tax in row)
                price = total_row - taxes_sum
                if price <= 0:
                    continue
                vals = self._prepare_line_vals(
                    product_name=str(row.get(col_product, '')).strip(),
                    price=price,
                    domain=row.get(col_dominio, False)
                )
                invoice_lines.append((0, 0, vals))

        else:  # Agrupado por Producto
            df_filled = df.fillna(0)
            available_tax_cols = [t for t in tax_columns if t in df_filled.columns]
            grouped = df_filled.groupby(col_product)[[col_total] + available_tax_cols].sum().reset_index()

            for _, row in grouped.iterrows():
                total_prod_group = float(row[col_total])
                taxes_sum = sum(float(row.get(tax, 0)) for tax in available_tax_cols)
                price = total_prod_group - taxes_sum
                if price <= 0:
                    continue

                distribution = {}
                if self.use_analytic_domain:
                    sub_df = df_filled[df_filled[col_product] == row[col_product]]
                    for _, sub_row in sub_df.iterrows():
                        clean_pat = str(sub_row.get(col_dominio, '')).replace(" ", "").upper()
                        if not clean_pat or clean_pat == '0':
                            continue
                        ana_acc = self.env['account.analytic.account'].search([
                            ('name', 'ilike', clean_pat + '%')
                        ], limit=1)
                        if ana_acc:
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

        # 1. Crear la factura con TODOS los impuestos en las líneas
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

        # 2. Consolidar impuestos fijos: eliminar duplicados y setear monto del Excel
        self._apply_fixed_tax_amounts(df, move)

        # 3. Adjuntar el Excel original a la factura
        self.env['ir.attachment'].create({
            'name': self.file_name if self.file_name and self.file_name.strip() else 'YPF_Ruta.xlsx',
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
            # Todos los impuestos del producto — Odoo los consolida al pie
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