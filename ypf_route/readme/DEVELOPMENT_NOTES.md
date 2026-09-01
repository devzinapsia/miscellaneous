# ypf_route — Development notes (exploration, 2026-09-01)

Notas de exploración del módulo tal como está hoy, para no tener que
re-leer todo el código en cada sesión nueva. El módulo ya está en
producción/uso — mantenimiento y fixes puntuales solamente, no reescritura.
No sigue las convenciones de `CLAUDE.md` (fue creado antes de adoptarlo):
sin `i18n/`, sin `readme/DESCRIPTION.rst` (hasta ahora), sin tests, labels
en español, licencia `LGPL-3` en vez de `AGPL-3`. No "corregir" nada de eso
salvo pedido explícito.

## Estructura de archivos

```
ypf_route/
├── __manifest__.py
├── __init__.py            (from . import models / wizard)
├── LICENSE
├── models/__init__.py     (VACÍO — no hay modelos permanentes, solo el wizard)
├── security/ir.model.access.csv
├── static/src/js/ypf_list_button.js
├── static/src/xml/ypf_list_button.xml
├── views/account_move_views.xml   (VACÍO, 0 bytes, y NO está listado en
│                                    manifest "data" — archivo muerto/sin uso)
└── wizard/
    ├── __init__.py
    ├── ypf_import_wizard.py       (toda la lógica de negocio vive acá)
    ├── ypf_import_wizard_view.xml
    └── ypf_menu.xml
```

No hay carpeta `tests/` — el módulo no tiene tests automatizados.
No hay carpeta `i18n/` — todos los strings están hardcodeados en español,
ya sea en el código Python (`raise UserError("...")`) o en los `string=`
de las vistas.

## 1. Modelos / wizards

Un solo modelo, transient: **`ypf.import.wizard`** (`wizard/ypf_import_wizard.py`).
No hay modelos persistentes propios — el módulo solo actúa como
"importador" que crea un `account.move` estándar y después desaparece.

Campos del wizard:
- `partner_id` (proveedor, requerido) — **no está fijado por default a
  YPF**, lo elige el usuario cada vez. El nombre del módulo sugiere que
  siempre es YPF, pero el código no lo fuerza ni lo precarga.
- `journal_id` — default: el primer diario `type=purchase` encontrado
  (`search(..., limit=1)`, sin orden explícito → depende del orden de
  inserción/ID en la DB, no necesariamente "el diario de compras
  correcto").
- `invoice_date`, `date` — default hoy.
- `invoice_date_due` — declarado pero **nunca usado** en `action_confirm`
  (no se pasa al `create` del move).
- `l10n_latam_document_type_id` — default: doc type código `'1'`
  (Factura A) para Argentina.
- `document_number` — número de documento, mapea a
  `l10n_latam_document_number`.
- `excel_file` (Binary, requerido) + `file_name`.
- `group_type`: `'line'` (una línea de factura por cada fila del Excel) o
  `'product'` (default; agrupa todas las filas por PRODUCTO y genera una
  sola línea de factura por producto, con distribución analítica
  ponderada entre los distintos vehículos que consumieron ese producto).
- `use_analytic_domain` (bool, default True): si está apagado, NO se
  arma `analytic_distribution` en ninguna línea — factura sin apropiar
  a vehículos.

### Punto de entrada UI
Hay dos formas de abrir el wizard:
1. Menú `Contabilidad > Proveedores > Nueva factura de YPF`
   (`wizard/ypf_menu.xml`, bajo `account.menu_finance_payables`).
2. Botón "Nueva factura de YPF" inyectado en el list view de
   `account.move` vía JS (`ypf_list_button.js` + `.xml`), agregado con un
   `t-inherit` de `web.ListView` que muestra el botón solo cuando
   `model.resModel === 'account.move'`.
   - **Nota**: la acción de servidor `action_server_ypf_import_wizard`
     en `wizard/ypf_menu.xml` (con `binding_model_id`/`binding_view_types`)
     parece un mecanismo alternativo/legacy para lograr lo mismo (bindear
     la acción al modelo `account.move`), pero el botón real que se usa es
     el JS. Puede ser redundante — no tocar sin confirmar cuál de los dos
     mecanismos está realmente en uso en producción.
   - El historial de git tiene ~19 commits seguidos con el mismo mensaje
     "feat: add YPF button to invoice list view" — sugiere que este botón
     fue iterado/parcheado muchas veces (probablemente costó hacerlo andar
     bien). Tenerlo en cuenta si aparece un bug ahí: zona históricamente
     inestable.

## 2. Relación patente (dominio) ↔ cuenta analítica

- Columna Excel: `IDENTIFICACION TARJETA` (variable `col_dominio`).
  **Ojo con el nombre**: pese a llamarse "tarjeta", en el negocio esto es
  la patente del vehículo (asumido por el módulo, no hay traducción
  explícita en el código — confirmar si esto sigue siendo así o si YPF
  cambió el nombre de columna en algún momento).
- El código NO usa un campo custom en `account.analytic.account` para
  guardar la patente. En cambio, busca por **nombre** de la cuenta
  analítica con `ilike`:
  ```python
  clean_pat = str(dominio).replace(" ", "").upper()
  ana_acc = env['account.analytic.account'].search(
      [('name', 'ilike', clean_pat + '%')], limit=1
  )
  ```
  Es decir: la patente limpia (sin espacios, mayúsculas) debe ser
  **prefijo** del campo `name` de la cuenta analítica correspondiente al
  vehículo (ej. patente `AB123CD` matchea una cuenta cuyo `name` empiece
  con `AB123CD`, tipo `"AB123CD - Ford Ranger"`).
  - Esto es frágil: si dos vehículos tienen patentes donde una es prefijo
    de otra (poco probable en formato patente argentina, pero no
    imposible con formatos mixtos viejo/nuevo), puede matchear la cuenta
    incorrecta. También si la cuenta analítica no sigue estrictamente la
    convención "patente al principio del nombre", el match falla
    silenciosamente (`if ana_acc:` — si no hay match, esa fila
    simplemente no aporta distribución analítica, sin warning ni error).
  - Búsqueda sin filtrar por `plan_id` o `company_id` — si hay otras
    cuentas analíticas en el sistema (de otro plan analítico, no
    vehículos) cuyo nombre por casualidad empiece igual, podrían matchear
    por error.

## 3. Lectura del Excel

- Librería: **pandas** + **openpyxl** como engine (`external_dependencies`
  en el manifest, correctamente declarado).
- `pd.read_excel(io.BytesIO(decoded_data), engine='openpyxl')` — toma la
  primera hoja del archivo por default (no especifica `sheet_name`).
- Columnas esperadas, **por nombre exacto** (no por posición — esto es
  bueno, es lo recomendado), tras `df.columns.str.strip()`:
  - `PRODUCTO` — nombre del producto/combustible.
  - `IMP TOT YER` — importe total de la fila/grupo (con impuestos
    incluidos).
  - `IDENTIFICACION TARJETA` — patente/dominio del vehículo.
  - `IVA`, `IMP CO2`, `TASA VIAL`, `IMP COMB LIQ` — columnas de impuestos
    que se restan del total para obtener el precio neto de la línea.
  - Si falta cualquiera de estas columnas exactas, el código no falla
    explícitamente en la lectura — `col not in df.columns` se chequea en
    algunos lugares (`_apply_fixed_tax_amounts`, agrupado) pero **no** en
    el acceso a `col_product`/`col_total`/`col_dominio` en modo `'line'`
    (usa `row.get(col, 0)`, que devuelve `0`/`False` silenciosamente si
    la columna no existe) — un cambio de nombre de columna en la planilla
    de YPF rompería el cálculo sin ningún error visible, solo importes en
    cero.
- `_filter_valid_rows`: descarta filas donde `PRODUCTO` es nulo, vacío,
  `0` o `'0'` — para sacar totales/filas en blanco del Excel.
- No hay ningún parseo de fechas del Excel — las fechas de la factura
  (`invoice_date`, `date`) las pone el usuario a mano en el wizard, no
  vienen de la planilla. Sin riesgo de parsing de fechas acá.
- `TAX_COLUMN_MAP` mapea 3 columnas de impuesto del Excel a nombres
  exactos de impuesto en Odoo (`ICO2`, `Tasa vial`, `ITC`) — depende de
  que existan `account.tax` con esos nombres exactos y
  `type_tax_use=purchase`. Si no existen, esos montos simplemente no se
  ajustan (`if not tax: continue`), sin avisar.

## 4. Armado de la factura de compra

Flujo en `action_confirm`:
1. Decodifica y lee el Excel a un DataFrame, limpia columnas/filas vacías.
2. Filtra filas válidas por `PRODUCTO`.
3. Según `group_type`:
   - **`'line'`** (por renglón): una línea de factura por fila del Excel.
     `price = IMP TOT YER - suma(IVA, IMP CO2, TASA VIAL, IMP COMB LIQ)`.
     Si `price <= 0`, se descarta la fila silenciosamente. Cada línea
     lleva `analytic_distribution` 100% a la cuenta que matchea la
     patente de esa fila (si `use_analytic_domain`).
   - **`'product'`** (agrupado, default): agrupa por `PRODUCTO`, suma
     `IMP TOT YER` y las columnas de impuesto. Una línea de factura por
     producto, con `price` neto = total del grupo menos impuestos. La
     distribución analítica de esa línea es un **prorrateo ponderado**:
     para cada vehículo que consumió ese producto, el peso es
     `(total de esa fila / total del grupo) * 100`, sumado por patente si
     un mismo vehículo aparece en más de una fila del mismo producto.
     Los pesos se redondean a 2 decimales al armar
     `analytic_distribution` — si hay muchos vehículos podría no sumar
     exactamente 100% por errores de redondeo acumulados (riesgo menor,
     Odoo suele tolerar esto).
4. `product_id` en cada línea: busca `product.product` por **nombre
   exacto** (`('name', '=', product_name)`) igual al valor de `PRODUCTO`
   en el Excel. Si no hay match exacto, la línea se crea igual pero sin
   producto (`product_id: False`) — solo con el `name` como descripción
   de texto libre. Frágil ante cualquier variación de mayúsculas/espacios
   en el nombre del producto entre el Excel y el catálogo Odoo (no hay
   `.strip()`/normalización en esta búsqueda, a diferencia de la de
   cuenta analítica).
5. `tax_ids` de cada línea = **todos** los `supplier_taxes_id` del
   producto encontrado (si no hay producto, lista vacía → línea sin
   impuestos).
6. Crea el `account.move` (`move_type='in_invoice'`) con esas líneas.
7. **Post-procesamiento clave — `_apply_fixed_tax_amounts`**: como cada
   línea de producto ya trae todos sus impuestos, Odoo genera una línea
   de impuesto en el pie de la factura *por cada línea de producto que
   comparte ese impuesto* (duplicados). Esta función:
   - Para cada impuesto de `TAX_COLUMN_MAP` (ICO2, Tasa vial, ITC),
     calcula el total real de esa columna en el Excel completo.
   - Busca todas las líneas del pie (`account.move.line`) con
     `tax_line_id` igual a ese impuesto.
   - **(Desde 18.0.1.0.3)** Distribuye el total exacto de la columna del
     Excel entre *todas* esas líneas, en proporción al peso actual de
     cada una (con signo negativo por ser factura de compra /
     `is_inbound()`), sin borrar ninguna. Antes de este fix se borraban
     todas menos la primera y se forzaba el total ahí — ver
     "Bug corregido" más abajo.
   - **IVA no está en `TAX_COLUMN_MAP`** — el IVA sí se resta del
     `price_unit` al calcular el neto de cada línea (está en
     `tax_columns`), pero no pasa por este ajuste de consolidación de
     pie. Se asume que el IVA queda calculado normalmente por Odoo vía
     los `tax_ids` del producto (impuesto porcentual estándar, no un
     monto fijo del Excel) — consistente con que CO2/Tasa vial/ITC son
     impuestos de monto fijo por litro que YPF ya calculó, mientras que
     el IVA es proporcional y Odoo lo puede recalcular él solo. Confirmar
     que este supuesto siga siendo válido si cambia algo del esquema
     impositivo.
8. Adjunta el Excel original como `ir.attachment` en la factura creada.
9. Abre la factura recién creada en modo form.

**Proveedor no está hardcodeado a YPF** en ningún lado del código — pese
al nombre del módulo, `partner_id` es un campo libre que elige el
usuario. Si el negocio espera que *siempre* sea YPF, hoy no hay ningún
default ni validación que lo garantice.

## 5. Tests

No existen. No hay carpeta `tests/`. Ningún test automatizado cubre:
parsing del Excel, agrupamiento, matching de cuenta analítica por
patente, ni la consolidación de impuestos del pie.

## 6. Puntos frágiles detectados (solo señalados, sin tocar)

1. **Matching de cuenta analítica por prefijo de nombre** (`ilike
   'PATENTE%'`) en vez de un campo dedicado — silenciosamente no apropia
   nada si no hay match, sin error visible al usuario.
2. **Matching de producto por nombre exacto** (`==`, sin `.strip()` ni
   normalización) — más frágil todavía que el de cuenta analítica.
3. **Nombres de columna e impuesto hardcodeados** (`PRODUCTO`,
   `IMP TOT YER`, `IDENTIFICACION TARJETA`, `ICO2`, `Tasa vial`, `ITC`) —
   cualquier cambio de formato en la planilla de YPF o renombre de un
   `account.tax` rompe el cálculo sin excepción visible (fallback
   silencioso a 0 o a "no ajustar").
4. **`journal_id` default** sin orden determinístico
   (`search(domain, limit=1)` sin `order=`) — podría traer un diario de
   compras distinto al esperado si hay más de uno.
5. **`invoice_date_due` no se usa** — campo del wizard que no impacta en
   la factura creada (posible bug o resto de una versión anterior).
6. **`views/account_move_views.xml` está vacío y no listado en el
   manifest** — archivo muerto, candidato a limpieza si alguna vez se
   pide explícitamente.
7. **Redundancia potencial entre el botón JS y la `ir.actions.act_window`
   con `binding_model_id`** en `ypf_menu.xml` — no queda claro con solo
   leer el código si ambos coexisten a propósito o si uno es vestigial;
   confirmar con el usuario antes de tocar cualquiera de los dos.
8. **Manejo de errores del Excel es genérico**: cualquier excepción al
   leer el archivo se envuelve en un solo `UserError` con el mensaje
   crudo de la excepción de pandas/openpyxl — no hay validación previa
   de que las columnas esperadas existan, así que un Excel con formato
   distinto puede "funcionar" pero generar una factura con importes en
   cero o mal apropiada, en vez de fallar con un mensaje claro.
9. **Sin tests** — cualquier fix a la lógica de agrupamiento/cálculo de
   impuestos no tiene red de seguridad automatizada; validar manualmente
   con un Excel de ejemplo real antes de dar por bueno un cambio.
10. **No filtra la cuenta analítica por plan/compañía** al buscar por
    patente — riesgo bajo pero real en una DB con múltiples planes
    analíticos o multi-compañía.

## 7. Bug corregido — "Error de validación" al editar una factura ya importada (18.0.1.0.3)

**Síntoma reportado**: tras importar el Excel, el usuario edita el importe
de una línea de producto (para ajustar una pequeña diferencia del Excel) y
al guardar aparece: *"El importe expresado en la divisa secundaria debe
ser positivo cuando se carga la cuenta y negativo cuando se acredita la
cuenta. Si la divisa es la misma que la de la empresa, este monto debe ser
estrictamente igual al balance."*

**Causa raíz** (confirmada reproduciendo con la factura real del cliente,
`account.move` id 6001, S-Train): la versión anterior de
`_apply_fixed_tax_amounts` borraba todas las líneas duplicadas de un
impuesto fijo menos una, y forzaba el total del Excel en la sobreviviente
vía `amount_currency = ...` con `check_move_validity=False`. Eso deja el
`account.move.line` bien sincronizado en el momento de la importación,
pero con una cantidad de líneas de impuesto distinta a la que el motor de
impuestos de Odoo espera encontrar la próxima vez que recalcula (por
ejemplo, al editar el precio de *cualquier otra* línea de la factura). En
ese recómputo posterior, Odoo termina escribiendo un `amount_currency`
nuevo (y erróneo, ej. `-35616.36`) en esa línea sin actualizar `balance`
en el mismo paso, y el `CHECK` de PostgreSQL
`account_move_line_check_amount_currency_balance_sign` (que exige que
`balance` y `amount_currency` tengan el mismo signo) rechaza el `UPDATE`.

**Fix**: no se borra ninguna línea. El total del Excel se reparte entre
*todas* las líneas de ese impuesto en proporción al peso actual de cada
una (la última absorbe el redondeo). Así la cantidad de líneas nunca
cambia, y un recómputo posterior de Odoo no encuentra una estructura
distinta a la que él mismo generó.

**Limitación que sigue existiendo (aceptada, no es bug)**: como antes,
cualquier edición posterior de la factura hace que Odoo recalcule los
impuestos fijos (ICO2/Tasa vial/ITC) con su monto "crudo" configurado en
el `account.tax` (típicamente 1.0), no con el total del Excel — el ajuste
del wizard solo aplica en el momento de la importación. Si hace falta
corregir un importe después, se edita directo en el pie de la factura.

**Hallazgo secundario, no corregido**: en la base de S-Train hay impuestos
duplicados con distinto nombre para el mismo concepto —
`ICO2` (id interno, `TAX_COLUMN_MAP` lo reconoce) e `IDC` (no lo
reconoce), y `ITC` vs `ICL` — ambos parecen estar asignados a los mismos
productos simultáneamente. Confirmar con el cliente/contador cuál es el
impuesto vigente antes de tocar esto; puede ser configuración duplicada
sin limpiar, no necesariamente un bug del módulo.

## 8. Impuestos fijos duplicados "por artículo" en la factura — no era un bug de código

Después de subir el fix de la sección 7, el usuario reportó en producción
que, al editar una factura ya importada y abrir "TAX: Add/update" en el
pie, `ICO2` y `Tasa vial` seguían apareciendo **una vez por cada artículo**
(ej. 6 líneas de "$1,00" en vez de un solo total), a diferencia de `IDC`,
`ICL`, `ITC`, `Perc IVA` y `P. IIBB BA`, que siempre se ven como una sola
línea consolidada.

**Causa real**: es configuración del `account.tax`, no código. Cada
impuesto tiene una línea de reparto (`account.tax.repartition.line`) de
tipo `tax` con un flag **"Usar en cierre de impuestos"**
(`use_in_tax_closing`). Cuando ese flag está **desactivado**, Odoo copia
la distribución analítica de cada línea de producto a su línea de
impuesto correspondiente, generando una línea de impuesto distinta por
cada distribución analítica distinta (es decir, por vehículo/artículo).
Cuando está **activado**, la línea de impuesto no lleva distribución
analítica propia y todas las contribuciones se consolidan en una sola
línea — sin importar cuántos vehículos/artículos haya detrás.

`ICO2` y `Tasa vial` tenían ese flag desactivado; `IDC`, `ICL`, `ITC`,
`Perc IVA` y `P. IIBB BA` lo tenían activado — de ahí la diferencia de
comportamiento, pese a que en la pestaña "Opciones avanzadas" del
impuesto se ven idénticos.

**Dónde está el campo en la UI** (no es obvio): pestaña **Definición**
del impuesto → grilla de líneas de distribución (donde se ve el % y la
cuenta contable) → ícono de columnas (⚙) para mostrar la columna oculta
**"Usar en cierre de impuestos"** → tildarla en la fila con Tipo =
"Impuesto" (no en la fila "Base").

**⚠️ Corrección — NO activar este flag, se revirtió.** En un primer
momento se le indicó al cliente activar "Usar en cierre de impuestos" en
`ICO2`/`Tasa vial` (2026-09-01) para eliminar la duplicación visual, y
funcionó para eso. Pero investigando más a fondo apareció un efecto
secundario real: ese mismo flag determina si el monto del impuesto se
incluye en el **cierre periódico de impuestos** (Libro IVA / percepciones,
`account_reports` de Enterprise — `enterprise/account_reports/models/
account_generic_tax_report.py`, usa `repartition.use_in_tax_closing`
para decidir qué se liquida contra AFIP).

`ICO2` imputa a una cuenta de **gasto** ("Impuestos y tasas",
`account_type=expense`) y `Tasa vial` a "Tasa vialidad"
(`account_type=expense_direct_cost`) — son **costos reales, no créditos
fiscales recuperables**. `ITC`/`IDC`/`ICL` en cambio imputan a "Pago a Cta
Ley 23966" (`account_type=asset_current`, un pago a cuenta recuperable
por ley) — por eso a esos SÍ les corresponde tener el flag activado, y a
`ICO2`/`Tasa vial` **no**. El default que traía Odoo (flag apagado en
ICO2/Tasa vial) era contablemente correcto. Se **revirtió** el cambio
(el cliente lo hizo directo en la UI) — `ICO2`/`Tasa vial` volvieron a
`use_in_tax_closing = False`.

**No hay forma de resolver la duplicación visual únicamente por
configuración** sin ese efecto secundario: en el código fuente de Odoo
(`account_tax.py`), la condición que decide si se copia la distribución
analítica a la línea de impuesto es exactamente
`tax.analytic OR NOT use_in_tax_closing` — no hay una tercera opción.
Se probó también limpiar `analytic_distribution` en los renglones ya
creados (sin borrarlos): no alcanza, porque cada renglón ya es un
registro separado en la base — limpiar un campo no fusiona filas, hace
falta borrarlas, que es la operación insegura que causó el bug de la
sección 7.

El fix de código de la sección 7 (no borrar líneas duplicadas) sigue
siendo válido y necesario — sin él, cualquier factura con varios
vehículos/artículos para un mismo impuesto de monto fijo puede volver a
generar el error de validación al editar. La duplicación visual en el
pie, en cambio, es esperable con `use_in_tax_closing=False` + distintas
distribuciones analíticas por línea — no es un bug, es cómo Odoo
prorratea el costo de ese impuesto por vehículo (igual que ya hace con el
combustible). Ver sección 9 para la causa real de lo que parecía "el pie
no suma bien".

## 9. El "pie no suma bien" (ej. $83 en vez de $664.167) — bug de otro módulo (`account_invoice_tax`, ingadhoc), no de `ypf_route`

Después de la sección 8, el cliente reportó que el **resumen del pie** de
la factura mostraba un total chico y sin sentido (ej. "$83,00") para
`ICO2`/`Tasa vial`, mientras que los **Apuntes contables** (Journal
Items) mostraban los renglones individuales correctos (uno por vehículo,
sumando bien al total real del Excel). Un F5 no lo arreglaba.

**Causa raíz** (nada que ver con `ypf_route`): el botón **"TAX:
Add/update"** / popup "Editar líneas de impuesto" no es de Odoo core —
lo agrega el módulo `account_invoice_tax` de
`ingadhoc/account-invoicing` (ya instalado en S-Train, se usa para
ajustar impuestos de monto fijo en facturas de cualquier proveedor, no
solo YPF). Ese módulo agrega un campo `tax_override_data` (JSON) en
`account.move`, pensado para que un ajuste manual de impuesto
"sobreviva" a futuras ediciones — recalculado automáticamente cada vez
que la factura se resincroniza dinámicamente
(`_sync_tax_lines`/`_apply_tax_overrides`).

El popup lista **una fila por cada `account.move.line`** de ese impuesto
(por eso se ve "duplicado por vehículo" ahí — es solo cómo arma la
lista, no indica nada malo por sí solo). El bug está en
`wizards/account_invoice_tax.py`, método `_save_overrides()`, que se
ejecuta al apretar el botón **"Update"** del popup:

```python
for wizard_line in self.tax_line_ids.filtered(lambda l: l.tax_id.amount_type == "fixed"):
    new_overrides[str(wizard_line.tax_id.id)] = {
        "amount": wizard_line.amount,
        ...
    }
```

Como hay varias filas de wizard para el mismo `tax_id` (una por
vehículo), este loop **pisa** la entrada del diccionario en cada
iteración — se queda solo con el importe de la **última** fila
procesada, no con la suma. Ese valor queda grabado en
`tax_override_data` y, desde ese momento, **cada recómputo futuro de la
factura fuerza ese único valor** (el de la última línea, no el total)
como si fuera el total del impuesto — permanentemente, hasta que se
limpie el campo. Por eso el F5 no soluciona nada: el servidor devuelve
intencionalmente ese valor "congelado" vía
`_compute_tax_totals()` (que, si `tax_override_data` no está vacío,
ignora el cálculo normal de Odoo y usa el override).

Confirmado en la base: `account.move` id 6001 (la primera factura que
investigamos, sección 7) tiene grabado
`tax_override_data = {"161": {"amount": 8904.09}, "174": {"amount":
664168.17}, "176": {"amount": 5900656.58}, ...}` — quedó así porque en
algún momento de las pruebas se apretó "Update" en ese popup.

**Cómo se dispara**: apretar el botón **"Update"** del popup "Editar
líneas de impuesto" en una factura donde un impuesto fijo tiene más de
un renglón (varios vehículos). Solo mirar y cerrar con "Cancelar" no
dispara nada.

**Alcance de `account_invoice_tax`**: se evaluó desinstalarlo. No se
hizo — es una herramienta de uso general del equipo contable (103
facturas en la base tenían `tax_override_data` grabado al momento de
revisar, de proveedores variados, no solo YPF; 102 posteadas —sin
impacto contable real si se pierde el campo, el asiento ya quedó fijo—,
1 en borrador). El único módulo que depende de él
(`l10n_ar_import_bill`, importador de facturas AFIP/ARCA) ya estaba
desinstalado en S-Train, así que tampoco había riesgo de arrastrar esa
baja. Aun así, se prefirió no tocarlo: es más seguro limpiar
puntualmente el campo en la factura afectada.

**Mitigación acordada** (sin tocar código de terceros):
1. En facturas YPF con varios vehículos, **no usar el botón "Update"**
   del popup de impuestos — solo "Cancelar" si se abre para mirar.
2. Para una factura ya "envenenada" (como la 6001), limpiar
   `tax_override_data` (poner `False`) para que vuelva a calcularse
   normal.

Pendiente, no crítico: si se vuelve un problema recurrente, considerar
parchear `_save_overrides()` en la copia local de `account_invoice_tax`
para que **sume** (o promedie ponderado) las filas del wizard que
comparten `tax_id`, en vez de pisarlas — o reportarlo upstream a
ingadhoc.

## Estado general

El módulo funciona (está en uso en producción) pero tiene varias
dependencias implícitas de convención (nombres de columnas Excel exactos,
nombres de impuestos exactos, nombres de cuentas analíticas empezando con
la patente, nombres de producto exactos) sin validación explícita ni
tests. Los bugs más probables van a aparecer como: "la factura se generó
pero con [importe/apropiación/producto] mal" en vez de un error visible —
conviene, ante cualquier reporte de bug, pedir el Excel real usado y
revisar nombres de columnas/productos/cuentas analíticas primero.
