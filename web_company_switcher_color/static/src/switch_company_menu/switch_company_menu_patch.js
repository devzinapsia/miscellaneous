import { patch } from "@web/core/utils/patch";
import { SwitchCompanyItem } from "@web/webclient/switch_company_menu/switch_company_item";
import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";
import {
    colorIndexToHex,
    getCompanySwitcherStyle,
    sortActiveCompanies,
} from "@web_company_switcher_color/company_color";

patch(SwitchCompanyMenu.prototype, {
    get companyColorStyle() {
        const companies = sortActiveCompanies(
            this.user.activeCompanies,
            this.user.allowedCompaniesWithAncestors
        );
        return getCompanySwitcherStyle(companies);
    },

    get companyColorButtonStyle() {
        const style = this.companyColorStyle;
        if (!style) {
            return undefined;
        }
        return [
            `--o-company-bg: ${style.background}`,
            `--o-company-fg: ${style.textColor}`,
            `--o-company-shadow: ${style.shadowColor}`,
        ].join("; ");
    },

    get companyColorButtonTitle() {
        return this.user.activeCompanies.map((company) => company.name).join(", ");
    },
});

patch(SwitchCompanyItem.prototype, {
    get companyColor() {
        return colorIndexToHex(this.props.company.color);
    },

    get companyColorCellStyle() {
        const color = this.companyColor;
        return color ? `--o-company-bg: ${color}` : undefined;
    },
});
