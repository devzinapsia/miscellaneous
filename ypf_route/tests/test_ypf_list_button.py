from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestYpfListButton(HttpCase):

    def test_button_opens_wizard_from_vendor_bills(self):
        self.start_tour('/odoo/action-account.action_move_in_invoice_type', 'ypf_route_list_button', login='admin')

    def test_button_hidden_on_customer_invoices(self):
        self.start_tour('/odoo/action-account.action_move_out_invoice_type', 'ypf_route_list_button_hidden', login='admin')
