Go to **Settings ‣ Users & Companies ‣ Companies**, open each company and
pick a color in its **Color** field.

Notes on how Odoo itself handles this field:

* The color is stored on the partner of the **root** company, so branches
  always share the color of their parent company.
* A company whose color was never set (or set to "No color") gets an
  automatic color from Odoo's palette, so in practice every company is
  colored; set a color explicitly to choose which one.
