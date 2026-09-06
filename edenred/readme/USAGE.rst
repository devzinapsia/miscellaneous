Go to *Accounting > Vendors > New Edenred bill*, upload the Edenred Excel
spreadsheet and the accompanying PDF invoice, fill in the vendor,
journal, dates, the subtotal shown on the PDF invoice and the fallback
account, and click *Confirm*.

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
