This module adds a wizard to import an Edenred fuel consumption Excel
spreadsheet (plus its accompanying PDF invoice) directly into a vendor
bill (``account.move``), one invoice line per valid row.

For each row, the wizard:

* Looks up the product by its exact name (``Producto / Servicio`` column,
  trimmed) and the vehicle by its exact license plate (``Placa`` column,
  trimmed and upper-cased).
* Links the invoice line to the vehicle using the standard
  ``account.move.line.vehicle_id`` field (added by the ``account_fleet``
  bridge module) whenever the plate matches.
* Falls back to a configurable account whenever the product is not found,
  or the product is found but no vehicle matched.
* After the invoice lines are built, for each vehicle that had at least
  one matched row, updates the vehicle's current driver
  (``fleet.vehicle.driver_id``) and logs/updates an odometer reading
  (``fleet.vehicle.odometer``) based on the most recent row (by date and
  time) for that vehicle.
* Reconciles the sum of all line amounts against the subtotal declared in
  the wizard, adding an adjustment line on the "Nafta Super" product for
  any difference.

The original Excel and PDF files are attached to the created vendor bill.
