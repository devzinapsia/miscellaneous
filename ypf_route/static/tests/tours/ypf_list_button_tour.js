import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("ypf_route_list_button", {
    url: "/odoo/action-account.action_move_in_invoice_type",
    steps: () => [
        {
            content: "Abrir el wizard desde la lista de facturas de proveedor",
            trigger: ".o_control_panel_main_buttons .o_button_ypf_import",
            run: "click",
        },
        {
            content: "El wizard de importación YPF está abierto",
            trigger: ".modal .o_form_view .o_field_widget[name='excel_file']",
        },
    ],
});

registry.category("web_tour.tours").add("ypf_route_list_button_hidden", {
    url: "/odoo/action-account.action_move_out_invoice_type",
    steps: () => [
        {
            content: "En facturas de cliente no se muestra el botón YPF",
            trigger: ".o_list_view .o_control_panel_main_buttons:not(:has(.o_button_ypf_import))",
        },
    ],
});
