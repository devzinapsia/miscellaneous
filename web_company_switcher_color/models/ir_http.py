from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """Add each company's color index to the companies sent to the web
        client, so the company switcher can paint them."""
        session_info = super().session_info()
        user_companies = session_info.get("user_companies")
        if not user_companies:
            return session_info
        company_dicts = {
            **user_companies.get("allowed_companies", {}),
            **user_companies.get("disallowed_ancestor_companies", {}),
        }
        # sudo: ancestor companies may not be readable by the user, same as
        # in the super() implementation.
        for company in self.env["res.company"].sudo().browse(list(company_dicts)):
            company_dicts[company.id]["color"] = company.color
        return session_info
