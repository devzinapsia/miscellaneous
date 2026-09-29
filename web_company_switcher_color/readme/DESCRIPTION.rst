In a multi-company database it is easy to lose track of which company (or
companies) are currently active. This module paints the company switcher
with the color defined on each company, so the active selection is
obvious at a glance:

* **Systray button** (top right): with one company selected, its name is
  shown on that company's color. With several companies selected, the
  background is split into equal vertical stripes with hard edges, one per
  selected company: the current company first, then the others in the
  order of the menu.
* **Dropdown menu**: in every row, the checkbox column becomes a solid,
  full-height block of that company's color, whether it is selected or
  not, so the rows form a continuous column of colors. The rest of the
  row keeps Odoo's native style. The same applies to the company list in
  the mobile burger menu.

Text color is chosen automatically (black or white) from the WCAG relative
luminance of the background, for readable contrast on any color.
