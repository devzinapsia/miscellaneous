Go to *Accounting > Vendors > New Edenred bill*, upload the Edenred Excel
spreadsheet and the accompanying PDF invoice, fill in the vendor,
journal, dates, the subtotal shown on the PDF invoice and the fallback
account, and click *Confirm*.

Expected Excel columns (exact names, case-sensitive)::

    Placa, Producto / Servicio, Neto, Fecha, hora, Conductor,
    Código de conductor, Estación de servicio, Dirección Estación,
    No. Transacción, Último odómetro

Rows where "Producto / Servicio" is empty (spreadsheet totals or blank
rows) are ignored.

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
