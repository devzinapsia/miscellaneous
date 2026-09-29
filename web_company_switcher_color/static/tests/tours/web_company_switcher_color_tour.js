import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("web_company_switcher_color_tour", {
    url: "/odoo",
    steps: () => [
        {
            content: "The systray button is painted with the company color",
            trigger: ".o_switch_company_menu .o_company_color_switcher:not(.o_company_color_multi)",
            run: "click",
        },
        {
            content: "Every colored company shows its color block",
            trigger: ".o_switch_company_menu_items .o_company_color_cell",
        },
        {
            content: "Select a second company",
            trigger:
                ".o_switch_company_item:has(.fa-square-o) .o_company_color_cell[role=menuitemcheckbox]",
            run: "click",
        },
        {
            content: "Confirm the selection",
            trigger: ".o_switch_company_menu_buttons button:first",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "The systray button is now striped",
            trigger: ".o_switch_company_menu .o_company_color_switcher.o_company_color_multi",
        },
    ],
});
