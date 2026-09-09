from odoo import fields, models

from ..hooks import snapshot_odoo_defaults
from .template_content import (
    FORMAL_CONTENT,
    INFORMAL_CONTENT,
    TEMPLATE_XMLIDS,
    odoo_body_param,
    odoo_subject_param,
)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def _register_hook(self):
        # Runs on every registry load (install, update, and plain server
        # start), unlike post_init_hook which only runs on first install.
        # Keeps snapshots complete when a slug is added to TEMPLATE_XMLIDS in
        # a later version and the module is merely updated, not reinstalled.
        snapshot_odoo_defaults(self.env)
        return super()._register_hook()

    email_template_style = fields.Selection(
        selection=[
            ("odoo", "Odoo (predeterminado)"),
            ("formal", "Zinapsia Formal"),
            ("informal", "Zinapsia Informal"),
        ],
        string="Estilo de emails",
        config_parameter="email_template_style.active_style",
        default="odoo",
    )

    def set_values(self):
        super().set_values()
        self._apply_email_template_style(self.email_template_style)

    def _apply_email_template_style(self, style):
        icp = self.env["ir.config_parameter"].sudo()
        style_content = {"formal": FORMAL_CONTENT, "informal": INFORMAL_CONTENT}.get(style)

        for slug, xmlid in TEMPLATE_XMLIDS.items():
            template = self.env.ref(xmlid, raise_if_not_found=False)
            if not template:
                continue
            if style_content is not None:
                subject = style_content[slug]["subject"]
                body_html = style_content[slug]["body_html"]
            else:
                subject = icp.get_param(odoo_subject_param(slug)) or template.subject
                body_html = icp.get_param(odoo_body_param(slug)) or template.body_html
            template.write({"subject": subject, "body_html": body_html})
