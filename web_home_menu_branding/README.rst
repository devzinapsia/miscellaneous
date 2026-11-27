=============================================
Branding Zinapsia en el menú de aplicaciones
=============================================

Agrega el branding de Zinapsia y de la empresa activa al menú de aplicaciones
(pantalla de inicio de Odoo Enterprise), sin ninguna configuración por cliente:

* **Panel izquierdo**: logo de Zinapsia.
* **Panel derecho**: logo de la empresa activa (sin el nombre, porque los
  logos suelen incluirlo). Cambia al cambiar de empresa en bases
  multiempresa. Si la empresa no tiene logo, muestra su nombre en su lugar.

Los paneles quedan fijos, centrados verticalmente en la pantalla y
centrados horizontalmente entre el borde de la pantalla y la grilla de
aplicaciones.
* **Pie**, debajo de la grilla de aplicaciones: "Ante alguna duda o problema
  enviá un correo a consultas@zinapsia.com", con el correo como enlace.

Los paneles no tapan ni bloquean los clics sobre las aplicaciones. Toman los
colores del tema, así que se ven bien en modo claro y oscuro; los logos van
sobre un recuadro blanco para que los logos oscuros se vean en modo oscuro.

Tamaños según el ancho de pantalla:

* 1600 px o más: logos de hasta 180 px de alto.
* De 1200 a 1599 px: logos de hasta 128 px de alto (los logos apaisados se
  achican si no entran en el espacio lateral).
* Menos de 1200 px (tablet y celular): sin paneles; solo se ve el pie.

Configuración
=============

No requiere configuración. El módulo **no** se instala solo: hay que
activarlo desde **Aplicaciones** en cada base donde se quiera mostrar el
branding (requiere ``web_enterprise``).

El logo de la empresa es el que figura en **Ajustes ‣ Usuarios y empresas ‣
Empresas**, en cada empresa.

**Cambiar el logo de Zinapsia**: reemplazar el archivo
``static/src/img/zinapsia_logo.png`` manteniendo el mismo nombre (se
recomienda una imagen cuadrada de unos 360 x 360 px), subir la versión del
módulo en ``__manifest__.py`` y actualizar el módulo. Si el navegador sigue
mostrando el logo anterior, forzar la recarga (Ctrl + F5).

Uso
===

Abrir el menú de aplicaciones (ícono de cuadrícula arriba a la izquierda, o
el logo de Odoo). Los paneles y el pie aparecen automáticamente.

Al cambiar de empresa con el selector de empresas, la página se recarga y el
panel derecho muestra la nueva empresa activa.

Bug Tracker
===========

Los errores se registran en
`GitHub Issues <https://github.com/devzinapsia/miscellaneous/issues>`_.
Antes de reportar uno, revisar si ya fue informado.

Credits
=======

Authors
-------

* Zinapsia
