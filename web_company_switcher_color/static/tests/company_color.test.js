import { beforeEach, describe, expect, test } from "@odoo/hoot";
import {
    contains,
    mountWithCleanup,
    patchWithCleanup,
    serverState,
} from "@web/../tests/web_test_helpers";

import { cookie } from "@web/core/browser/cookie";
import { user } from "@web/core/user";
import { MobileSwitchCompanyMenu } from "@web/webclient/burger_menu/mobile_switch_company_menu/mobile_switch_company_menu";
import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";
import {
    MAX_STRIPES,
    NEUTRAL_STRIPE_COLOR,
    RAINBOW_COLORS,
    buildStripedBackground,
    colorIndexToHex,
    getCompanySwitcherStyle,
    getContrastTextColor,
    getMenuOrder,
    sortActiveCompanies,
} from "@web_company_switcher_color/company_color";

describe.current.tags("desktop");

describe("pure helpers", () => {
    test("colorIndexToHex maps Odoo's palette and treats 0/unknown as no color", () => {
        expect(colorIndexToHex(1)).toBe("#ee2d2d");
        expect(colorIndexToHex(3)).toBe("#e8bb1d");
        expect(colorIndexToHex(11)).toBe("#9872e6");
        expect(colorIndexToHex(0)).toBe(null);
        expect(colorIndexToHex(12)).toBe(null);
        expect(colorIndexToHex(-1)).toBe(null);
        expect(colorIndexToHex(undefined)).toBe(null);
        expect(colorIndexToHex(false)).toBe(null);
    });

    test("getContrastTextColor picks black on light and white on dark backgrounds", () => {
        expect(getContrastTextColor("#ffffff")).toBe("#000000");
        expect(getContrastTextColor("#fff")).toBe("#000000");
        expect(getContrastTextColor("#000000")).toBe("#ffffff");
        expect(getContrastTextColor("#e8bb1d")).toBe("#000000"); // yellow
        expect(getContrastTextColor("#304be0")).toBe("#ffffff"); // blue
        // Mid-tone purple: black wins by a hair under WCAG (4.62 vs 4.55).
        expect(getContrastTextColor("#9f628f")).toBe("#000000");
        expect(getContrastTextColor("#9872e6")).toBe("#000000"); // violet
        expect(getContrastTextColor("#61c36e")).toBe("#000000"); // green
    });

    test("getContrastTextColor rejects malformed colors", () => {
        expect(() => getContrastTextColor("red")).toThrow();
    });

    test("buildStripedBackground builds equal hard-edged stripes", () => {
        expect(buildStripedBackground([])).toBe(null);
        expect(buildStripedBackground(["#c00"])).toBe("#c00");
        expect(buildStripedBackground(["#c00", "#00c"])).toBe(
            "linear-gradient(to right, #c00 0% 50%, #00c 50% 100%)"
        );
        expect(buildStripedBackground(["#a", "#b", "#c"].map((c) => c + "00"))).toBe(
            "linear-gradient(to right, #a00 0% 33.33%, #b00 33.33% 66.67%, #c00 66.67% 100%)"
        );
    });

    test("menu order: roots by sequence, then their branches", () => {
        const companies = [
            { id: 1, sequence: 3, parent_id: false, child_ids: [4] },
            { id: 2, sequence: 2, parent_id: false, child_ids: [] },
            { id: 3, sequence: 1, parent_id: false, child_ids: [] },
            { id: 4, sequence: 4, parent_id: 1, child_ids: [] },
        ];
        expect(getMenuOrder(companies)).toEqual([3, 2, 1, 4]);
        const active = [companies[3], companies[0], companies[2]];
        expect(sortActiveCompanies(active, companies).map((c) => c.id)).toEqual([4, 3, 1]);
        expect(sortActiveCompanies([], companies)).toEqual([]);
    });

    test("switcher style: single company, stripes, neutral and rainbow fallbacks", () => {
        expect(getCompanySwitcherStyle([{ color: 0 }])).toBe(null);
        expect(getCompanySwitcherStyle([{ color: 0 }, { color: 0 }])).toBe(null);

        expect(getCompanySwitcherStyle([{ color: 8 }])).toEqual({
            background: "#304be0",
            textColor: "#ffffff",
            shadowColor: "#000000",
            multiple: false,
        });

        expect(getCompanySwitcherStyle([{ color: 3 }, { color: 1 }])).toEqual({
            background: "linear-gradient(to right, #e8bb1d 0% 50%, #ee2d2d 50% 100%)",
            textColor: "#000000",
            shadowColor: "#ffffff",
            multiple: true,
        });

        const withoutColor = getCompanySwitcherStyle([{ color: 0 }, { color: 8 }]);
        expect(withoutColor.background).toBe(
            `linear-gradient(to right, ${NEUTRAL_STRIPE_COLOR} 0% 50%, #304be0 50% 100%)`
        );

        const many = Array.from({ length: MAX_STRIPES + 1 }, (_, i) => ({ color: i + 1 }));
        expect(getCompanySwitcherStyle(many).background).toBe(
            buildStripedBackground(RAINBOW_COLORS)
        );
        expect(getCompanySwitcherStyle(many.slice(0, MAX_STRIPES)).background).toInclude(
            "80% 100%"
        );
    });
});

function patchUserActiveCompanies(cids) {
    patchWithCleanup(
        user.activeCompanies,
        cids.map((cid) => serverState.companies.find((company) => company.id === cid))
    );
}

describe("company switcher rendering", () => {
    beforeEach(() => {
        cookie.set("cids", "2");
        serverState.companies = [
            { id: 1, name: "Yellow", sequence: 1, parent_id: false, child_ids: [4], color: 3 },
            { id: 2, name: "Red", sequence: 2, parent_id: false, child_ids: [], color: 1 },
            { id: 3, name: "Plain", sequence: 3, parent_id: false, child_ids: [], color: 0 },
            { id: 4, name: "Branch", sequence: 4, parent_id: 1, child_ids: [], color: 3 },
        ];
    });

    test("single colored company paints the systray button", async () => {
        patchUserActiveCompanies([2]);
        await mountWithCleanup(SwitchCompanyMenu);
        expect(".o_company_color_switcher").toHaveCount(1);
        expect(".o_company_color_multi").toHaveCount(0);
        expect(".o_company_color_switcher").toHaveAttribute("style", /--o-company-bg: #ee2d2d/);
        expect(".o_company_color_switcher").toHaveAttribute("style", /--o-company-fg: #000000/);
    });

    test("several companies are striped, current company first", async () => {
        patchUserActiveCompanies([2, 1]);
        await mountWithCleanup(SwitchCompanyMenu);
        expect(".o_company_color_multi").toHaveCount(1);
        expect(".o_company_color_switcher").toHaveAttribute(
            "style",
            /linear-gradient\(to right, #ee2d2d 0% 50%, #e8bb1d 50% 100%\)/
        );
        expect(".o_company_color_switcher").toHaveAttribute("title", "Red, Yellow");
    });

    test("company without color keeps the native button", async () => {
        patchUserActiveCompanies([3]);
        await mountWithCleanup(SwitchCompanyMenu);
        expect(".o_company_color_switcher").toHaveCount(0);
        expect(".o_switch_company_menu button").not.toHaveAttribute("style");
    });

    test("dropdown rows show a color block whether selected or not", async () => {
        patchUserActiveCompanies([2]);
        await mountWithCleanup(SwitchCompanyMenu);
        await contains(".dropdown-toggle").click();
        expect(".o_company_color_cell").toHaveCount(3);
        expect("[data-company-id='1'] .o_company_color_cell").toHaveAttribute(
            "style",
            "--o-company-bg: #e8bb1d"
        );
        expect("[data-company-id='4'] .o_company_color_cell").toHaveCount(1);
        // No color: native cell, native border.
        expect("[data-company-id='3'] [role=menuitemcheckbox]").not.toHaveClass(
            "o_company_color_cell"
        );
        expect("[data-company-id='3'] [role=menuitemcheckbox]").toHaveClass("border-end");
        expect("[data-company-id='2'] [role=menuitemcheckbox]").not.toHaveClass("border-end");
    });

    test("mobile burger menu rows get the same color blocks", async () => {
        patchUserActiveCompanies([2]);
        await mountWithCleanup(MobileSwitchCompanyMenu);
        expect(".o_burger_menu_companies .o_company_color_cell").toHaveCount(3);
        expect("[data-company-id='2'] .o_company_color_cell").toHaveAttribute(
            "style",
            "--o-company-bg: #ee2d2d"
        );
    });
});
