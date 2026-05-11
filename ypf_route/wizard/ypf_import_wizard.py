import io
import base64
import pandas as pd
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class YpfImportWizard(models.TransientModel):
    _name = "ypf.import.wizard"
    _description = "Wizard Importador YPF Ruta"

    partner_id = fields.Many2one("res.partner", string="Proveedor", required=True)
    invoice_date = fields.Date(
        string="Fecha Factura", default=fields.Date.context_today, required=True
    )
    date = fields.Date(
        string="Fecha Contable", default=fields.Date.context_today, required=True
    )
    invoice_date_due = fields.Date(string="Fecha de Vencimiento")
    journal_id = fields.Many2one(
        "account.journal",
        string="Diario",
        domain=[("type", "=", "purchase")],
        required=True,
    )
    l10n_latam_document_type_id = fields.Many2one(
        "l10n_latam.document.type", string="Tipo de documento"
    )
    document_number = fields.Char(string="Número de Documento")
    excel_file = fields.Binary(string="Subir planilla excel", required=True)
    file_name = fields.Char(string="Nombre del archivo")
    group_type = fields.Selection(
        [("line", "Abierto por Renglon"), ("product", "Agrupado por Producto")],
        string="Modo de Importación",
        default="product",
        required=True,
    )
    use_analytic_domain = fields.Boolean(string="Usa cuenta analítica", default=True)

    @api.model
    def default_get(self, fields_list):
        res = super(YpfImportWizard, self).default_get(fields_list)
        journal = self.env["account.journal"].search(
            [("type", "=", "purchase")], limit=1
        )
        res["journal_id"] = journal.id if journal else False
        doc_type = self.env["l10n_latam.document.type"].search(
            [("code", "=", "1"), ("country_id.code", "=", "AR")], limit=1
        )
        if doc_type:
            res["l10n_latam_document_type_id"] = doc_type.id
        return res

    def _filter_valid_rows(self, df, col_product):
        mask = (
            df[col_product].notna()
            & (df[col_product] != 0)
            & (df[col_product].astype(str).str.strip() != "")
            & (df[col_product].astype(str).str.strip() != "0")
        )
        return df[mask].reset_index(drop=True)

    def action_confirm(self):
        self.ensure_one()

        try:
            decoded_data = base64.b64decode(self.excel_file)
            df = pd.read_excel(io.BytesIO(decoded_data), engine="openpyxl")
            df.columns = df.columns.str.strip()
            df = df.dropna(how="all").reset_index(drop=True)
            df = self._filter_valid_rows(df, "PRODUCTO")
            df_filled = df.fillna(0)
        except Exception as e:
            raise UserError("Error al procesar el archivo Excel: %s" % str(e))

        invoice_lines = []

        # 1. GENERACIÓN DE LÍNEAS DE PRODUCTOS
        if self.group_type == "line":
            for _, row in df_filled.iterrows():
                total_row = float(row.get("IMP TOT YER", 0))
                iva_row = float(row.get("IVA", 0))
                itc_row = float(row.get("IMP COMB LIQ", 0))
                ico2_row = float(row.get("IMP CO2", 0))
                tasa_row = float(row.get("TASA VIAL", 0))
                price_neto = total_row - iva_row - itc_row - ico2_row - tasa_row

                if price_neto <= 0:
                    continue

                vals = self._prepare_line_vals(
                    str(row.get("PRODUCTO", "")).strip(),
                    price_neto,
                    domain=row.get("IDENTIFICACION TARJETA", False),
                )
                invoice_lines.append((0, 0, vals))
        else:
            grouped = df_filled.groupby("PRODUCTO").sum(numeric_only=True).reset_index()
            for _, row in grouped.iterrows():
                total_prod = float(row["IMP TOT YER"])
                iva_prod = float(row.get("IVA", 0))
                especiales_prod = sum(
                    float(row.get(c, 0))
                    for c in ["IMP COMB LIQ", "IMP CO2", "TASA VIAL"]
                )
                price_neto = total_prod - iva_prod - especiales_prod

                if price_neto <= 0:
                    continue

                distribution = {}
                if self.use_analytic_domain:
                    sub_df = df_filled[df_filled["PRODUCTO"] == row["PRODUCTO"]]
                    for _, sub_row in sub_df.iterrows():
                        clean_pat = (
                            str(sub_row.get("IDENTIFICACION TARJETA", ""))
                            .replace(" ", "")
                            .upper()
                        )
                        ana_acc = self.env["account.analytic.account"].search(
                            [("name", "ilike", clean_pat + "%")], limit=1
                        )
                        if ana_acc:
                            weight = (sub_row["IMP TOT YER"] / total_prod) * 100
                            distribution[str(ana_acc.id)] = (
                                distribution.get(str(ana_acc.id), 0) + weight
                            )

                vals = self._prepare_line_vals(
                    str(row["PRODUCTO"]).strip(), price_neto, analytic_dist=distribution
                )
                invoice_lines.append((0, 0, vals))

        # 2. CREAR FACTURA (Con contexto corregido)
        # Usamos line_ids para asegurar que Odoo no recompute impuestos de forma agresiva
        move_model = self.env["account.move"].with_context(check_move_validity=False)
        move = move_model.create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_id.id,
                "invoice_date": self.invoice_date,
                "date": self.date,
                "journal_id": self.journal_id.id,
                "l10n_latam_document_type_id": self.l10n_latam_document_type_id.id,
                "l10n_latam_document_number": self.document_number,
                "invoice_line_ids": invoice_lines,
            }
        )

        # 3. AJUSTE DE LÍNEAS DE IMPUESTO (Sustento Grep l10n_ar)
        excel_taxes = {
            "01": df_filled["IVA"].sum(),
            "04": df_filled["IMP COMB LIQ"].sum() + df_filled["IMP CO2"].sum(),
            "99": df_filled["TASA VIAL"].sum(),
        }

        for line in move.line_ids.filtered(lambda l: l.display_type == "tax"):
            afip_code = line.tax_line_id.tax_group_id.l10n_ar_tribute_afip_code
            if afip_code in excel_taxes:
                monto = excel_taxes[afip_code]
                line.write(
                    {
                        "debit": monto,
                        "credit": 0.0,
                        "amount_currency": monto
                        if move.currency_id == move.company_id.currency_id
                        else line.amount_currency,
                    }
                )

        # 4. BALANCEAR LÍNEA DE PROVEEDOR
        total_excel = df_filled["IMP TOT YER"].sum()
        payable_line = move.line_ids.filtered(
            lambda l: l.display_type == "payment_term"
        )
        if payable_line:
            payable_line.write(
                {
                    "debit": 0.0,
                    "credit": total_excel,
                    "amount_currency": -total_excel
                    if move.currency_id == move.company_id.currency_id
                    else payable_line.amount_currency,
                }
            )

        # Adjunto
        self.env["ir.attachment"].create(
            {
                "name": self.file_name or "YPF_Ruta.xlsx",
                "datas": self.excel_file,
                "res_model": "account.move",
                "res_id": move.id,
                "type": "binary",
            }
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "target": "current",
        }

    def _prepare_line_vals(
        self, product_name, price, domain=False, analytic_dist=False
    ):
        product = self.env["product.product"].search(
            [("name", "=", str(product_name).strip())], limit=1
        )
        res = {
            "product_id": product.id if product else False,
            "name": product_name,
            "quantity": 1.0,
            "price_unit": price,
            "tax_ids": [(6, 0, product.supplier_taxes_id.ids)] if product else [],
        }
        if self.use_analytic_domain:
            if analytic_dist:
                res["analytic_distribution"] = {
                    str(k): round(v, 2) for k, v in analytic_dist.items()
                }
            elif domain:
                clean_pat = str(domain).replace(" ", "").upper()
                ana_acc = self.env["account.analytic.account"].search(
                    [("name", "ilike", clean_pat + "%")], limit=1
                )
                if ana_acc:
                    res["analytic_distribution"] = {str(ana_acc.id): 100}
        return res
