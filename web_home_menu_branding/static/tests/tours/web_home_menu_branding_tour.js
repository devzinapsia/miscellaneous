import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("web_home_menu_branding_tour", {
    url: "/odoo",
    steps: () => [
        {
            content: "The Zinapsia logo is shown on the left panel",
            trigger: ".o_home_menu .o_home_branding_panel_left img.o_home_branding_logo",
        },
        {
            content: "The active company logo and name are shown on the right panel",
            trigger:
                ".o_home_menu .o_home_branding_panel_right:has(img.o_home_branding_logo) .o_home_branding_name:contains(Branding test with logo)",
        },
        {
            content: "The support footer has a mailto link",
            trigger:
                ".o_home_menu .o_home_branding_footer a[href='mailto:consultas@zinapsia.com']",
        },
        {
            content: "The side panels never block clicks on the apps",
            trigger: ".o_home_menu .o_home_branding_panel_left",
            run() {
                for (const panel of document.querySelectorAll(".o_home_branding_panel")) {
                    const style = getComputedStyle(panel);
                    if (style.pointerEvents !== "none" || style.position !== "fixed") {
                        throw new Error(
                            `Unexpected panel style: pointer-events=${style.pointerEvents}, position=${style.position}`
                        );
                    }
                }
            },
        },
    ],
});
