This module adds a wizard to import an Edenred fuel consumption Excel
spreadsheet (plus its accompanying PDF invoice) directly into a vendor
bill (``account.move``), one invoice line per valid row.

For each row, the wizard:

* Matches the vehicle by its exact license plate (``Placa`` column,
  trimmed and upper-cased). Links the invoice line to the vehicle using
  the standard ``account.move.line.vehicle_id`` field (added by the
  ``account_fleet`` bridge module) whenever the plate matches.
* Picks the product from a fixed 6-product catalog instead of matching by
  name: whether the plate matched a vehicle decides which 3 of the 6
  apply ("(autos)" if matched, "(maquinarias)" if not); within those 3,
  the row's ``Producto / Servicio`` text is matched against each
  candidate's "Edenred" property tags (``product.product_properties``).
  No tag match falls back to that category's own "Otros gastos no
  combustible" product.
* Uses the matched product's own account when the vehicle matched;
  otherwise uses a configurable fallback account instead.
* After the invoice lines are built, for each vehicle that had at least
  one matched row, updates the vehicle's current driver
  (``fleet.vehicle.driver_id``) and logs/updates an odometer reading
  (``fleet.vehicle.odometer``) based on the most recent row (by date and
  time) for that vehicle.
* Creates a ``fleet.vehicle.log.services`` record for every vehicle-matched
  line, with the product/liters, date, odometer and full row description.
* Reconciles the sum of all line amounts against the subtotal declared in
  the wizard, adding an adjustment line (no product, just an account) for
  any difference.
* Forces the ITC, IDC and Impuestos internos fixed-amount tax lines to the
  totals declared in the wizard (see "Fixed-amount tax totals" below).

The original Excel and PDF files are attached to the created vendor bill.
