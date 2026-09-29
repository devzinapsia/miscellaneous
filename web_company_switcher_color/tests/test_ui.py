from odoo.tests import no_retry, tagged

from .common import CompanyColorCase


def hoot_job_hash(name):
    """Same hash HOOT uses to filter a test suite by id (see
    web/tests/test_js.py, HOOTCommon._generate_hash)."""
    value = 0
    for char in name:
        value = (value << 5) - value + ord(char)
        value = value & 0xFFFFFFFF
    return f"{value:08x}"


@tagged("post_install", "-at_install")
class TestUi(CompanyColorCase):
    @no_retry
    def test_hoot_unit_tests(self):
        suite_id = hoot_job_hash("@web_company_switcher_color")
        self.browser_js(
            f"/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&id={suite_id}",
            "",
            "",
            login="admin",
            timeout=600,
            success_signal="[HOOT] Test suite succeeded",
            error_checker=lambda message: "[HOOT]" not in message,
        )

    def test_switcher_tour(self):
        self.start_tour("/odoo", "web_company_switcher_color_tour", login="admin")
