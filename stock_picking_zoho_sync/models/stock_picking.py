import json
import logging

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)

ZOHO_SYNC_TIMEOUT = 30


class StockPicking(models.Model):
    _inherit = "stock.picking"

    zoho_pending = fields.Boolean(string="Zoho pending", default=False)
    zoho_sent_date = fields.Datetime(string="Zoho sent on", readonly=True, copy=False)

    def _action_done(self):
        res = super()._action_done()
        incoming_done = self.filtered(
            lambda p: p.picking_type_id.code == "incoming" and p.state == "done"
        )
        if incoming_done:
            incoming_done.zoho_pending = True
        return res

    def _zoho_sync_get_document(self):
        self.ensure_one()
        detalle = []
        for move_line in self.move_line_ids.filtered(lambda ml: ml.quantity):
            product = move_line.product_id
            purchase_line = move_line.move_id.purchase_line_id
            if purchase_line:
                valor = purchase_line.price_unit
            else:
                # Fallback for manual receipts with no linked purchase order line.
                valor = product.standard_price
            detalle.append(
                {
                    "codigoProducto": product.default_code or product.barcode or product.name,
                    "descripcion": product.name,
                    "cantidad": move_line.quantity,
                    "valor": valor,
                }
            )
        return {
            "cabecera": {
                "fecha": self.date_done.date().isoformat(),
                "numeroDoc": self.name,
                "tipoDoc": "REMITO",
                "modo": "INS",
            },
            "detalle": detalle,
        }

    def _zoho_sync_send(self, url):
        self.ensure_one()
        documento = self._zoho_sync_get_document()
        payload = {"objJSON": json.dumps(documento)}
        response = requests.put(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=ZOHO_SYNC_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 3000 or data.get("result", {}).get("status") != "ok":
            raise ValueError("Unexpected Zoho response: %s" % data)

    def _cron_sync_zoho_pending_pickings(self):
        params = self.env["ir.config_parameter"].sudo()
        if not params.get_param("stock_picking_zoho_sync.enabled"):
            return
        url = params.get_param("stock_picking_zoho_sync.url")
        if not url:
            _logger.warning("Zoho sync is enabled but no URL is configured, skipping.")
            return
        pending_pickings = self.search(
            [
                ("zoho_pending", "=", True),
                ("zoho_sent_date", "=", False),
                ("picking_type_id.code", "=", "incoming"),
            ]
        )
        for picking in pending_pickings:
            try:
                picking._zoho_sync_send(url)
            except Exception:
                _logger.warning(
                    "Zoho sync failed for picking %s, will retry on the next run.",
                    picking.name,
                    exc_info=True,
                )
                continue
            picking.write(
                {
                    "zoho_pending": False,
                    "zoho_sent_date": fields.Datetime.now(),
                }
            )
