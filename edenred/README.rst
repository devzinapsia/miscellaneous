========================
Edenred - Fuel Invoice Import
========================

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

The original Excel and PDF files are attached to the created vendor bill.

**Table of contents**

.. contents::
   :local:

Configuration
=============

This module requires a few things to be set up beyond its own
dependencies:

* ``fleet.vehicle`` records with their ``license_plate`` set, matching the
  plates used in the Edenred spreadsheet.
* Exactly 6 catalog products, named:
  "Diesel (autos)", "Nafta (autos)", "Otros gastos no combustible (autos)",
  "Diesel (maquinarias)", "Nafta (maquinarias)" and
  "Otros gastos no combustible (maquinarias)".
* An "Edenred" property (a "Tags" type property added via the product
  form's "Editar propiedades", stored in the standard
  ``product.product_properties`` field, defined per product category)
  on each of those 6 products, with tags matching the exact
  ``Producto / Servicio`` values used in the Edenred spreadsheet (e.g.
  "DIESEL SUPER", "NAFTA PREMIUM") selected as appropriate.
* An ``account.account`` to use as the fallback account for lines whose
  vehicle did not match. The wizard defaults this to the account with
  code ``5.3.1.01.148`` in the current company, when it exists; otherwise
  it must be set manually.
* An ``account.account`` to use as the target for the subtotal difference
  adjustment line. Also defaults to code ``5.3.1.01.148`` when it exists.
* ``hr.employee`` records whose ``name`` matches the driver names used in
  the ``Conductor`` column (word order does not matter), so that the
  vehicle's current driver and the odometer log's driver can be set
  automatically.

Usage
=====

Go to *Accounting > Vendors > New Edenred bill*, upload the Edenred Excel
spreadsheet and the accompanying PDF invoice, fill in the vendor,
journal, dates, the subtotal shown on the PDF invoice, the fallback
account and the subtotal-difference account, and click *Confirm*.

Expected Excel columns (exact names, case-sensitive)::

    Placa, Producto / Servicio, Neto, Fecha, hora, Conductor,
    Código de conductor, Estación de servicio, Dirección Estación,
    No. Transacción, Último odómetro, Litros

Rows where "Producto / Servicio" is empty (spreadsheet totals or blank
rows), or where "Neto" is zero (or empty), are ignored - they don't
generate an invoice line, and don't count towards vehicle driver/odometer
matching either.

Odometer idempotency
---------------------

``fleet.vehicle.odometer`` only stores a date, not a time of day. The
wizard therefore keys the odometer log on **vehicle + day**: re-importing
the same spreadsheet (or an equivalent one) for the same vehicle and day
updates the existing odometer log instead of creating a duplicate. Two
rows for the same vehicle on the same day but at different times are
treated as the same odometer log entry; only the values from whichever
row is most recent that day (driver and odometer value) are kept. A
different day for the same vehicle always creates a new odometer log.

Fleet service log per line
---------------------------

For every line matched to a vehicle, the wizard creates the corresponding
``fleet.vehicle.log.services`` record itself (instead of leaving it to
``account_fleet``'s own auto-creation when the bill is posted), with:

* Description: the product name and the liters from the "Litros" column
  (e.g. "NAFTA SUPER 35.50 L").
* Date: the row's date (from "Fecha").
* Odometer: linked to the odometer log already created for that vehicle
  and day.
* Notes: the full line description (driver, station, transaction number).

Since the wizard links the service to its invoice line up front, posting
the bill later does not create a second, duplicate service log for the
same line.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/devzinapsia/miscellaneous/issues>`_.

Credits
=======

Authors
-------

* Zinapsia
