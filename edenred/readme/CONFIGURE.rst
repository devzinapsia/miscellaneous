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
