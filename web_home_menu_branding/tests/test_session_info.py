import base64

from odoo.tests import HttpCase, tagged

# 1x1 transparent PNG
PIXEL_PNG = base64.b64encode(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
        "1f15c4890000000d49444154789c6360000002000154a24f5d00000000"
        "49454e44ae426082"
    )
)


class HomeBrandingCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_logo = cls.env["res.company"].create(
            {"name": "Branding test with logo", "logo": PIXEL_PNG}
        )
        cls.company_no_logo = cls.env["res.company"].create(
            {"name": "Branding test without logo"}
        )
        cls.company_no_logo.logo = False
        cls.user = cls.env["res.users"].create(
            {
                "name": "Branding test user",
                "login": "web_home_menu_branding_user",
                "password": "web_home_menu_branding_user",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
                "company_id": cls.company_logo.id,
                "company_ids": [
                    (6, 0, [cls.company_logo.id, cls.company_no_logo.id])
                ],
            }
        )


@tagged("post_install", "-at_install")
class TestSessionInfo(HomeBrandingCase):
    def test_logo_flags(self):
        self.authenticate(self.user.login, self.user.login)
        info = self.make_jsonrpc_request("/web/session/get_session_info")
        companies = info["user_companies"]["allowed_companies"]
        with_logo = companies[str(self.company_logo.id)]
        without_logo = companies[str(self.company_no_logo.id)]
        self.assertTrue(with_logo["home_branding_has_logo"])
        self.assertTrue(with_logo["home_branding_logo_unique"])
        self.assertFalse(without_logo["home_branding_has_logo"])
        # The rest of the payload is untouched.
        self.assertEqual(with_logo["name"], "Branding test with logo")


@tagged("post_install", "-at_install")
class TestUi(HomeBrandingCase):
    def test_home_menu_branding_tour(self):
        self.start_tour(
            "/odoo", "web_home_menu_branding_tour", login=self.user.login
        )
