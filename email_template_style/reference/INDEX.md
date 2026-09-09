# Templates extraídos del Word

7 templates x 2 estilos = 14 combinaciones, cada una con su `__subject.txt` y `__body.html`.

| Archivo (slug) | Título original en el doc |
|---|---|
| factura | FACTURA |
| notas_credito | NOTAS DE CREDITO |
| pagos | PAGOS (RECIBOS y O/P) |
| cotizacion_orden_venta | COTIZACION y ORDEN DE VENTA |
| orden_venta_confirmada | ORDEN DE VENTA CONFIRMADA |
| orden_venta_cancelada | ORDEN DE VENTA CANCELADA |
| orden_venta_confirmacion_pago | ORDEN DE VENTA - CONFIRMACION DE PAGO |

Carpetas: `formal/` e `informal/`.

## Cambios pendientes de aplicar en TODOS los bodies (no vienen resueltos del Word)

1. Reemplazar el bloque de firma completo (el `<div>` con "El equipo de Zinapsia" /
   "El equipo de Umbrella Software") por el bloque de firma individual dinámica
   definido en `email_template_style` (nombre/apellido del usuario responsable del
   registro, y su firma de perfil si tiene).
2. El logo tiene un ancho en píxeles fijo, calculado a mano por cliente (176px en
   Informal, 133.328px en Formal, cada uno ajustado al logo de un cliente de
   ejemplo distinto). Reemplazar por `max-width`/`max-height` con `width:auto` /
   `height:auto` para que sea responsivo y sirva para cualquier logo, sin volver a
   calcular medidas a mano por cliente.
