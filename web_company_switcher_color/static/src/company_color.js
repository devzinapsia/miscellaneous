/**
 * Pure helpers to turn company color indexes into CSS backgrounds and
 * readable text colors. No OWL/DOM dependency, so they can be reused and
 * unit tested in isolation.
 */

/**
 * Hex values of Odoo's `$o-colors` palette
 * (web/static/src/scss/secondary_variables.scss), indexed like the integer
 * `color` field of res.company / res.partner. Index 0 means "No color".
 */
export const COMPANY_COLOR_PALETTE = [
    null,
    "#ee2d2d", // 1 Red
    "#dc8534", // 2 Orange
    "#e8bb1d", // 3 Yellow
    "#5794dd", // 4 Cyan
    "#9f628f", // 5 Purple
    "#db8865", // 6 Almond
    "#41a9a2", // 7 Teal
    "#304be0", // 8 Blue
    "#ee2f8a", // 9 Raspberry
    "#61c36e", // 10 Green
    "#9872e6", // 11 Violet
];

/** Stripe color used for a selected company that has no color. */
export const NEUTRAL_STRIPE_COLOR = "#a2a2a2";

/** Above this many selected companies, a rainbow is shown instead. */
export const MAX_STRIPES = 5;

/** Palette colors reordered by hue, used for the "many companies" background. */
export const RAINBOW_COLORS = [1, 2, 3, 10, 7, 4, 8, 11, 5, 9].map(
    (index) => COMPANY_COLOR_PALETTE[index]
);

const BLACK = "#000000";
const WHITE = "#ffffff";

/**
 * @param {number} index color index of a company
 * @returns {string|null} hex color, or null when the company has no color
 */
export function colorIndexToHex(index) {
    if (!Number.isInteger(index)) {
        return null;
    }
    return COMPANY_COLOR_PALETTE[index] || null;
}

/**
 * @param {string} hex "#rgb" or "#rrggbb"
 * @returns {number[]} [r, g, b] in the 0-255 range
 */
function hexToRgb(hex) {
    let value = hex.replace("#", "");
    if (value.length === 3) {
        value = [...value].map((char) => char + char).join("");
    }
    if (!/^[0-9a-f]{6}$/i.test(value)) {
        throw new Error(`Invalid hex color: ${hex}`);
    }
    return [0, 2, 4].map((start) => parseInt(value.slice(start, start + 2), 16));
}

/**
 * WCAG 2.x relative luminance.
 *
 * @param {string} hex
 * @returns {number} between 0 (black) and 1 (white)
 */
export function getRelativeLuminance(hex) {
    const [r, g, b] = hexToRgb(hex).map((channel) => {
        const c = channel / 255;
        return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Pick black or white text, whichever has the higher WCAG contrast ratio
 * against the given background.
 *
 * @param {string} hex background color
 * @returns {"#000000"|"#ffffff"}
 */
export function getContrastTextColor(hex) {
    const luminance = getRelativeLuminance(hex);
    const contrastWithWhite = 1.05 / (luminance + 0.05);
    const contrastWithBlack = (luminance + 0.05) / 0.05;
    return contrastWithBlack >= contrastWithWhite ? BLACK : WHITE;
}

function formatPercent(value) {
    return `${Math.round(value * 100) / 100}%`;
}

/**
 * Build a background made of equal-width vertical stripes with hard edges
 * (no smooth blending between colors).
 *
 * @param {string[]} colors
 * @returns {string|null} a CSS color or linear-gradient, null if no colors
 */
export function buildStripedBackground(colors) {
    if (!colors.length) {
        return null;
    }
    if (colors.length === 1) {
        return colors[0];
    }
    const step = 100 / colors.length;
    const stops = colors.map(
        (color, i) => `${color} ${formatPercent(i * step)} ${formatPercent((i + 1) * step)}`
    );
    return `linear-gradient(to right, ${stops.join(", ")})`;
}

/**
 * Order companies the way the switcher menu lists them: root companies by
 * sequence, each followed by its branches (depth first).
 *
 * @param {Object[]} companies every company shown in the menu
 * @returns {number[]} company ids in menu order
 */
export function getMenuOrder(companies) {
    const byId = new Map(companies.map((company) => [company.id, company]));
    const order = [];
    const visit = (company) => {
        order.push(company.id);
        for (const childId of company.child_ids || []) {
            const child = byId.get(childId);
            if (child) {
                visit(child);
            }
        }
    };
    companies
        .filter((company) => !company.parent_id)
        .sort((c1, c2) => c1.sequence - c2.sequence)
        .forEach(visit);
    return order;
}

/**
 * Keep the current company first and sort the other active companies in
 * menu order.
 *
 * @param {Object[]} activeCompanies current company first
 * @param {Object[]} menuCompanies every company shown in the menu
 * @returns {Object[]}
 */
export function sortActiveCompanies(activeCompanies, menuCompanies) {
    if (!activeCompanies.length) {
        return [];
    }
    const [current, ...others] = activeCompanies;
    const rank = new Map(getMenuOrder(menuCompanies).map((id, i) => [id, i]));
    const rankOf = (company) => rank.get(company.id) ?? Number.MAX_SAFE_INTEGER;
    others.sort((c1, c2) => rankOf(c1) - rankOf(c2));
    return [current, ...others];
}

/**
 * Compute how the company switcher button must be painted.
 *
 * @param {Object[]} companies active companies, current company first
 * @returns {{background: string, textColor: string, shadowColor: string, multiple: boolean}|null}
 *     null when no active company has a color (keep Odoo's default style)
 */
export function getCompanySwitcherStyle(companies) {
    const hexColors = companies.map((company) => colorIndexToHex(company.color));
    if (!hexColors.some(Boolean)) {
        return null;
    }
    const multiple = companies.length > 1;
    const background =
        companies.length > MAX_STRIPES
            ? buildStripedBackground(RAINBOW_COLORS)
            : buildStripedBackground(hexColors.map((hex) => hex || NEUTRAL_STRIPE_COLOR));
    const textColor = getContrastTextColor(hexColors[0] || NEUTRAL_STRIPE_COLOR);
    return {
        background,
        textColor,
        shadowColor: textColor === BLACK ? WHITE : BLACK,
        multiple,
    };
}
