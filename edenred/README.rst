========================
Edenred - Fuel Invoice Import
========================

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

**Table of contents**

.. contents::
   :local:

Configuration
=============

No specific configuration is required beyond having the standard
dependencies installed and set up:

* ``fleet.vehicle`` records with their ``license_plate`` set, matching the
  plates used in the Edenred spreadsheet.
* A product per Edenred concept (``Producto / Servicio`` column), named
  exactly as it appears in the spreadsheet.
* A product named exactly "Nafta Super", used to post any difference
  between the sum of the imported lines and the subtotal declared in the
  wizard.
* An ``account.account`` to use as the fallback account for lines whose
  product was not found, or whose product was found but no vehicle
  matched. The wizard defaults this to the account with code
  ``5.3.1.01.148`` in the current company, when it exists; otherwise it
  must be set manually.
* ``hr.employee`` records whose ``name`` matches the driver names used in
  the ``Conductor`` column (word order does not matter), so that the
  vehicle's current driver and the odometer log's driver can be set
  automatically.

Usage
=====

Go to *Accounting > Vendors > New Edenred bill*, upload the Edenred Excel
spreadsheet and the accompanying PDF invoice, fill in the vendor,
journal, dates, the subtotal shown on the PDF invoice and the fallback
account, and click *Confirm*.

Expected Excel columns (exact names, case-sensitive)::

    Placa, Producto / Servicio, Neto, Fecha, hora, Conductor,
    Código de conductor, Estación de servicio, Dirección Estación,
    No. Transacción, Último odómetro

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

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/devzinapsia/miscellaneous/issues>`_.

Credits
=======

Authors
-------

* Zinapsia
