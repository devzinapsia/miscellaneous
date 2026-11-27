import { HomeMenu } from "@web_enterprise/webclient/home_menu/home_menu";
import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";

export const SUPPORT_EMAIL = "consultas@zinapsia.com";

patch(HomeMenu.prototype, {
    /**
     * Branding data for the home menu side panels and footer.
     * The active company comes from the user's session, which is reloaded
     * when switching companies, so the panel always shows the current one.
     */
    get homeBranding() {
        const company = user.activeCompany;
        let companyLogoUrl = false;
        if (company && company.home_branding_has_logo) {
            const unique = company.home_branding_logo_unique
                ? `?unique=${encodeURIComponent(company.home_branding_logo_unique)}`
                : "";
            companyLogoUrl = `/web/image/res.company/${company.id}/logo${unique}`;
        }
        return {
            zinapsiaLogoUrl: "/web_home_menu_branding/static/src/img/zinapsia_logo.png",
            companyName: company?.name || "",
            companyLogoUrl,
            supportEmail: SUPPORT_EMAIL,
        };
    },
});
