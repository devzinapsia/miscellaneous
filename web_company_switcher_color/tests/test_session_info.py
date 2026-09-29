from odoo.tests import tagged

from .common import CompanyColorCase


@tagged("post_install", "-at_install")
class TestSessionInfo(CompanyColorCase):
    def test_allowed_companies_include_color(self):
        self.authenticate("admin", "admin")
        info = self.make_jsonrpc_request("/web/session/get_session_info")
        companies = info["user_companies"]["allowed_companies"]
        self.assertEqual(companies[str(self.company_main.id)]["color"], 3)
        self.assertEqual(companies[str(self.company_red.id)]["color"], 1)
        self.assertEqual(companies[str(self.company_blue.id)]["color"], 8)
        # Branches share the color of their root company (native behavior).
        self.assertEqual(companies[str(self.company_red_branch.id)]["color"], 1)
        # The rest of the payload is untouched.
        self.assertEqual(companies[str(self.company_red.id)]["name"], "Red company")
        self.assertEqual(
            companies[str(self.company_red.id)]["child_ids"], [self.company_red_branch.id]
        )

    def test_disallowed_ancestor_includes_color(self):
        user = self.env["res.users"].create(
            {
                "name": "Branch only",
                "login": "branch_only",
                "password": "branch_only",
                "company_id": self.company_red_branch.id,
                "company_ids": [(6, 0, self.company_red_branch.ids)],
            }
        )
        self.authenticate(user.login, "branch_only")
        info = self.make_jsonrpc_request("/web/session/get_session_info")
        ancestors = info["user_companies"]["disallowed_ancestor_companies"]
        self.assertEqual(ancestors[str(self.company_red.id)]["color"], 1)
