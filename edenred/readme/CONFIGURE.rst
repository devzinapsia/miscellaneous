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
