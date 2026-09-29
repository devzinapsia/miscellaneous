from odoo.tests import HttpCase


class CompanyColorCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_main = cls.env.ref("base.main_company")
        cls.company_red = cls.env["res.company"].create({"name": "Red company"})
        cls.company_blue = cls.env["res.company"].create({"name": "Blue company"})
        cls.company_red_branch = cls.env["res.company"].create(
            {"name": "Red branch", "parent_id": cls.company_red.id}
        )
        cls.company_main.color = 3
        cls.company_red.color = 1
        cls.company_blue.color = 8
        cls.admin = cls.env.ref("base.user_admin")
        cls.admin.write(
            {
                "company_ids": [
                    (4, company.id)
                    for company in (
                        cls.company_main,
                        cls.company_red,
                        cls.company_blue,
                        cls.company_red_branch,
                    )
                ],
                "company_id": cls.company_main.id,
            }
        )
