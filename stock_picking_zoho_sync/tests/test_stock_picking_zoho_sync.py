import json
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase


class TestStockPickingZohoSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Zoho Sync Test Product",
                "type": "consu",
                "is_storable": True,
                "standard_price": 20.0,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Zoho Sync Test Vendor"})

    def _validate(self, picking):
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()

    def test_new_incoming_picking_defaults_not_pending(self):
        po = self._create_purchase_order()
        po.button_confirm()
        picking = po.picking_ids[0]
        self.assertFalse(picking.zoho_pending)

    def test_validate_incoming_picking_sets_pending(self):
        po = self._create_purchase_order()
        po.button_confirm()
        picking = po.picking_ids[0]
        self._validate(picking)
        self.assertEqual(picking.state, "done")
        self.assertTrue(picking.zoho_pending)
        self.assertFalse(picking.zoho_sent_date)

    def test_validate_internal_picking_does_not_set_pending(self):
        internal_type = self.warehouse.int_type_id
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": internal_type.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.warehouse.view_location_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.warehouse.lot_stock_id.id,
                            "location_dest_id": self.warehouse.view_location_id.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.warehouse.lot_stock_id, 1
        )
        picking.action_assign()
        self._validate(picking)
        self.assertEqual(picking.state, "done")
        self.assertFalse(picking.zoho_pending)

    def test_cron_does_nothing_when_sync_disabled(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "stock_picking_zoho_sync.enabled", False
        )
        with patch(
            "odoo.addons.stock_picking_zoho_sync.models.stock_picking.requests.put"
        ) as mock_put:
            self.env["stock.picking"]._cron_sync_zoho_pending_pickings()
            mock_put.assert_not_called()

    def test_cron_sends_pending_picking_and_marks_it_sent(self):
        po = self._create_purchase_order()
        po.button_confirm()
        picking = po.picking_ids[0]
        self._validate(picking)
        self.assertTrue(picking.zoho_pending)

        self._enable_sync()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 3000,
            "result": {"status": "ok", "procesados": 1},
        }
        with patch(
            "odoo.addons.stock_picking_zoho_sync.models.stock_picking.requests.put",
            return_value=mock_response,
        ) as mock_put:
            self.env["stock.picking"]._cron_sync_zoho_pending_pickings()

        mock_put.assert_called_once()
        _args, kwargs = mock_put.call_args
        body = json.loads(kwargs["json"]["objJSON"])
        self.assertEqual(body["cabecera"]["numeroDoc"], picking.name)
        self.assertEqual(body["cabecera"]["tipoDoc"], "REMITO")
        self.assertEqual(body["cabecera"]["modo"], "INS")
        self.assertEqual(len(body["detalle"]), 1)
        self.assertEqual(body["detalle"][0]["cantidad"], 10)
        self.assertEqual(body["detalle"][0]["valor"], 100.0)

        self.assertFalse(picking.zoho_pending)
        self.assertTrue(picking.zoho_sent_date)

    def test_cron_keeps_pending_on_error_response(self):
        po = self._create_purchase_order()
        po.button_confirm()
        picking = po.picking_ids[0]
        self._validate(picking)

        self._enable_sync()
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 4000, "result": {"status": "error"}}
        with patch(
            "odoo.addons.stock_picking_zoho_sync.models.stock_picking.requests.put",
            return_value=mock_response,
        ):
            self.env["stock.picking"]._cron_sync_zoho_pending_pickings()

        self.assertTrue(picking.zoho_pending)
        self.assertFalse(picking.zoho_sent_date)

    def test_line_without_purchase_order_uses_standard_price_fallback(self):
        incoming_type = self.warehouse.in_type_id
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": incoming_type.id,
                "location_id": incoming_type.default_location_src_id.id,
                "location_dest_id": self.warehouse.lot_stock_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 3,
                            "product_uom": self.product.uom_id.id,
                            "location_id": incoming_type.default_location_src_id.id,
                            "location_dest_id": self.warehouse.lot_stock_id.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        self._validate(picking)
        self.assertTrue(picking.zoho_pending)

        document = picking._zoho_sync_get_document()
        self.assertEqual(len(document["detalle"]), 1)
        self.assertEqual(document["detalle"][0]["valor"], self.product.standard_price)

    def _create_purchase_order(self):
        return self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 10,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 100.0,
                            "name": self.product.name,
                            "date_planned": "2026-01-01",
                        },
                    )
                ],
            }
        )

    def _enable_sync(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("stock_picking_zoho_sync.enabled", True)
        params.set_param("stock_picking_zoho_sync.url", "https://example.com/zoho")
