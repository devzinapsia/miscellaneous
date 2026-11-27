from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """Tell the web client whether each allowed company has a logo, plus a
        cache-busting token for it, so the home menu can show the logo (or
        only the company name when there is none)."""
        session_info = super().session_info()
        user_companies = session_info.get("user_companies")
        if not user_companies:
            return session_info
        company_dicts = user_companies.get("allowed_companies", {})
        # sudo: same as super(), the companies are already filtered to the
        # ones the user is allowed to log into.
        for company in self.env["res.company"].sudo().browse(list(company_dicts)):
            vals = company_dicts[company.id]
            vals["home_branding_has_logo"] = bool(company.logo)
            write_date = company.partner_id.write_date or company.write_date
            vals["home_branding_logo_unique"] = (
                write_date.strftime("%Y%m%d%H%M%S") if write_date else ""
            )
        return session_info
