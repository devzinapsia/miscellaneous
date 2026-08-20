from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    zoho_sync_enabled = fields.Boolean(
        string="Synchronize with Zoho",
        config_parameter="stock_picking_zoho_sync.enabled",
    )
    zoho_sync_url = fields.Char(
        string="URL",
        config_parameter="stock_picking_zoho_sync.url",
    )
    # Stored for future use. The current integration example embeds the
    # "publickey" directly in the URL and does not send this as a header,
    # so it is not concatenated into any outgoing request yet.
    zoho_sync_token = fields.Char(
        string="Token",
        config_parameter="stock_picking_zoho_sync.token",
    )
