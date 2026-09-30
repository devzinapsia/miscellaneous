=======================
Color de empresa activa
=======================

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

.. image:: https://raw.githubusercontent.com/devzinapsia/miscellaneous/19.0/web_company_switcher_color/static/description/switcher_menu.png
   :alt: Company switcher dropdown with a color block per company

.. image:: https://raw.githubusercontent.com/devzinapsia/miscellaneous/19.0/web_company_switcher_color/static/description/switcher_single.png
   :alt: Systray button painted with the color of the only selected company

**Table of contents**

.. contents::
   :local:

Configuration
=============

Go to **Settings ‣ Users & Companies ‣ Companies**, open each company and
pick a color in its **Color** field.

Notes on how Odoo itself handles this field:

* The color is stored on the partner of the **root** company, so branches
  always share the color of their parent company.
* A company whose color was never set (or set to "No color") gets an
  automatic color from Odoo's palette, so in practice every company is
  colored; set a color explicitly to choose which one.

Usage
=====

Nothing to do once colors are defined: use the company switcher as usual.

* **One company selected**: the systray button shows the company name on
  its color.
* **Two to five companies selected**: the button shows one stripe per
  selected company, the current company first. Selected companies without
  a color are shown as a neutral gray stripe, so the number of selected
  companies is still visible.
* **More than five companies selected**: the button shows a "rainbow" of
  Odoo's palette, meaning "many companies selected".
* **No selected company has a color**: Odoo's standard style is kept.
* With several companies selected, the text color follows the current
  company's color and gets a thin halo in the opposite color, so it stays
  readable over every stripe. Hovering the button lists every selected
  company.

Bug Tracker
===========

Bugs are tracked on
`GitHub Issues <https://github.com/devzinapsia/miscellaneous/issues>`_.
In case of trouble, please check there if your issue has already been
reported.

Credits
=======

Authors
-------

* Zinapsia

Maintainers
-----------

This module is maintained by Zinapsia.

This module is part of the
`miscellaneous <https://github.com/devzinapsia/miscellaneous>`_
project.
