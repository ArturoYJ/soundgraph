# SoundGraph — Brief para el agente de UI/UX

## Objetivo y entregable

Diseña y maqueta en Stitch un frontend web responsive en español. SoundGraph ayuda a descubrir música mediante escuchas compartidas: el usuario lee **por qué** aparece una canción, consulta su ficha y la guarda en una playlist. El prototipo puede usar los datos de ejemplo de este archivo; **no conectes Stitch a las bases ni incluyas credenciales**. La implementación final consumirá una API REST de FastAPI desde el mismo origen.

Entrega pantallas de escritorio (1440 px) y móvil (390 px), componentes reutilizables con sus variantes y el flujo enlazado. La demo prioritaria (**H1**) es: **Acceso como Ana → Descubrir → Ficha de C.R.E.A.M. → Guardar → Para escuchar → recargar y confirmar que sigue ahí**. El mantenimiento de playlists y la edición editorial (**H2**) deben diseñarse aparte para que la demo principal pueda entregarse primero.

**Fuera de alcance:** reproducción, barra de control de audio, suscripciones, búsquedas globales, tendencias, filtros de género, registro público, edición colaborativa y explorador de influencias. No agregar controles sin acción definida.

## Lenguaje visual

- Una **libreta de descubrimiento musical**, no un clon de Spotify. El elemento distintivo es la tira **«¿Por qué esta recomendación?»**: corta en la tarjeta, ampliada en la ficha.
- Dirección sugerida: papel marfil, tinta oscura y ciruela como acento; gris para metadatos y colores semánticos para advertencia y error. Espaciado en múltiplos de 8; superficies diferenciadas por fondo, sin sombras pesadas. Verificar contraste antes de entregar.
- Encabezado tras iniciar sesión: marca, **Descubrir**, **Mis playlists**, etiqueta discreta **Modo demo** y menú del perfil con **Cerrar sesión**. Marcar la navegación activa; no agregar un sidebar para dos destinos.
- Escritorio: contenido central y panel lateral de ficha de unos 440 px. Móvil: una columna y ficha en panel inferior o a pantalla completa para contenido largo. Si no hay imágenes autorizadas, usar carátulas tipográficas o geométricas; no incluir icono de reproducción.
- Componentes: botón primario/secundario/destructivo, entrada de formulario, tarjeta de canción, tira de afinidad, fila de playlist, esqueleto, aviso en línea, panel de ficha, selector de playlist y confirmación de guardado.

## Pantallas H1

### 1. Acceso de demostración

Marca, título **«Entra a la demo»**, ayuda **«Los perfiles y las escuchas son datos de prueba»**, selector de perfil, campo protegido **Código de acceso** y botón **Entrar**. Para la maqueta: Ana, Sofía, Perfil nuevo y Editor son ejemplos sintéticos; la primera demo usa Ana y Perfil nuevo. La asignación de roles corresponde al backend, nunca al selector.

- Clic en **Entrar** o Enter: valida datos; cambia a **Entrando…**, bloquea envíos duplicados y navega a Descubrir solo si la API confirma.
- Credenciales erróneas: **«El perfil o el código no son válidos»** en el formulario. Sin indicar cuál falló.
- Sesión caducada: volver al acceso con **«Tu sesión terminó. Vuelve a entrar»**. No repetir escrituras automáticamente.
- **Cerrar sesión:** borrar la sesión por API y volver al acceso. No requiere modal. Al recargar, consultar la sesión actual, no guardar el código en el navegador.

### 2. Descubrir

Título **«Descubre música»**, subtítulo **«Recomendaciones basadas en escuchas compartidas»**, zona de avisos y lista de tarjetas. Diseñar el caso real de **una sola recomendación**, sin rellenar con resultados inventados.

Tarjeta: título, crédito principal si existe, tira con motivo, **Ver ficha** y **Guardar en playlist**. Texto exacto de referencia: **«1 perfil con escuchas en común también escuchó esta canción»**. Ajustar singular/plural. La afinidad cuenta perfiles distintos, no canciones compartidas ni porcentajes; no muestra nombres de otros oyentes.

- **Ver ficha:** abre el panel con los datos ya incluidos en la recomendación.
- **Guardar en playlist:** abre el selector; no guarda hasta que se confirma.

### 3. Mis playlists

Título, filas de listas propias, **nombre**, contador real `trackCount` y acción **Abrir**. La semilla de Ana contiene **«Para escuchar»**; el perfil sin listas muestra **«Todavía no tienes playlists»**. No ofrecer crear en la variante H1. El error debe ofrecer **Reintentar**, no simular una lista vacía.

### 4. Detalle de playlist

Enlace **Volver a mis playlists**, nombre, filas con **posición**, **título** y crédito si existe, y **Seguir descubriendo**. Una pista cuya ficha ya no se resuelve sigue visible: mostrar **«Ficha no disponible»**; no inventar título ni borrar la fila. La playlist recién sembrada no tiene pistas: **«Aún no hay canciones guardadas»** y enlace **Ir a Descubrir**. Si no pertenece al perfil o no existe, mostrar **«No encontramos esa playlist»** y volver al listado.

Después de guardar, la pista debe aparecer en el orden del servidor y persistir al recargar. No usar almacenamiento local para simular una escritura en la versión conectada.

## Paneles, modales y estados

| Componente/estado | Contenido y acción |
| --- | --- |
| **Ficha de canción** | Título, créditos por rol, tira de motivo si se abrió desde Descubrir, notas y fuentes si existen. Oculta secciones ausentes. Acciones **Cerrar** y **Guardar en playlist**. No inventes año, álbum, portada o audio. |
| **Guardar en playlist** | Título de la pista, lista seleccionable, **Cancelar** y **Guardar**. Preselecciona si hay una sola playlist. Si no hay destinos, explica el motivo y no permite confirmar. No apiles diálogos: si se abrió desde ficha, al cancelar vuelve a la ficha. |
| **Pendiente** | **Guardando…**; deshabilitar ese envío. No mostrar éxito antes de recibir respuesta. |
| **Guardado nuevo** | `201`: **«Guardada en Para escuchar»**, enlace **Ver playlist**. |
| **Ya guardada** | `200`: **«Ya estaba en Para escuchar»**; una sola fila, misma posición. |
| **Guardado no confirmado** | Conservar selección; **«No pudimos confirmar el guardado»** y **Reintentar** o **Ver playlist**. La respuesta perdida no prueba que no hubo escritura. |
| **Cargando lista** | Esqueletos con la estructura de tarjeta; navegación disponible. |
| **Vacío real** | **«Todavía no hay recomendaciones para este perfil»** cuando `items: []` y `partial: false`. No asumir la causa. |
| **Resultados parciales** | **«Algunas recomendaciones no se muestran porque su ficha no está disponible»** y tarjetas válidas. Aplica incluso si quedaron cero tarjetas. |
| **Servicio caído** | `503`: **«No pudimos cargar las recomendaciones»** y **Reintentar**. No mostrarlo como falta de historial. |
| **Validación/permisos** | `422`: marcar el campo y conservar entrada; `403`: no hay permiso; `404` al guardar: distinguir playlist de ficha mediante el código; `401`: solicitar entrar de nuevo. Nunca mostrar logs ni nombres de motores al oyente. |

**Movimiento:** cambio de color de botón en 100–150 ms, feedback inmediato al pulsar, transición de panel/selector en 180–220 ms con opacidad y desplazamiento corto, sin rebote. Estados normal, hover, pulsado, ocupado, deshabilitado y foco. Con movimiento reducido, suprimir desplazamientos y repeticiones. **Accesibilidad:** áreas táctiles 44 × 44 px; teclas Enter/Escape, foco visible y devuelto al disparador, foco contenido en modal; siempre ofrecer cierre por botón; avisos con texto además de color, confirmaciones en región `aria-live`. No depender de gestos.

## Variantes H2

- **Crear / renombrar:** diálogo reutilizable con campo Nombre (1–100 caracteres tras recortar espacios), **Cancelar** y **Crear/Guardar cambios**. Mantener el texto cuando falle.
- **Quitar de playlist:** acción de fila, aclarar que la canción permanece en el catálogo. Actualizar al recibir `204`.
- **Eliminar playlist:** diálogo destructivo con nombre; aclara que se elimina la colección, no las canciones del catálogo. Confirmado, volver al listado.
- **Reordenar:** **Subir/Bajar**, **Cancelar** y **Guardar orden**; arrastre opcional. Enviar la lista completa de IDs; no mostrar cambios como persistidos ante un fallo.
- **Editar nota:** solo para el rol Editor, desde una ficha existente. Campos **Texto** (1–1000) y **Fuente** (1–200). No exponer la edición de títulos, créditos ni afinidad. Enviar la lista de notas de esa sección conservando otras notas; abandonar un formulario modificado requiere confirmar descarte. Los permisos se verifican en el servidor.

## Datos para maquetar

Estos valores corresponden a la semilla académica, no a datos personales ni a una API pública. Respuesta de descubrimiento para Ana:

```json
{
  "items": [
    {
      "song": {
        "songId": "c-cream",
        "title": "C.R.E.A.M.",
        "editorial": {
          "credits": [{"name": "Wu-Tang Clan", "role": "artista"}],
          "notes": [{"text": "Ficha de demostración para probar recomendaciones por escuchas compartidas.", "source": "Semilla académica de SoundGraph"}]
        }
      },
      "affinity": 1
    }
  ],
  "partial": false
}
```

- Ana: `p-ana-main`; perfil sin historial: `p-new`; editor: `p-editor`. Al entrar recibes `{profileId, displayName, role}`.
- Estado inicial de playlist: `{playlistId: "pl-ana-demo", name: "Para escuchar", trackCount: 0, tracks: []}`.
- Después de guardar: `trackCount: 1`; la primera fila tiene `{songId: "c-cream", position: 1, song: …}`. El objeto `song` se hidrata con la ficha y puede valer `null` si falta.
- Variantes de descubrimiento: vacío `{"items":[],"partial":false}`; todas las fichas ausentes `{"items":[],"partial":true}`; caída de motor: HTTP `503` con `{"code":"service_unavailable","message":"Servicio temporalmente no disponible."}`.

## Conexión futura de la maqueta

Base `/api/v1`. Consumir JSON desde el mismo origen mediante cookie de sesión; **no leer ni almacenar el token, no consultar bases directamente**. Swagger UI local: `/docs`; especificación: `/openapi.json`. Nunca subir el archivo de credenciales a Stitch ni exponer Docker en la red para que el prototipo lo consuma.

| Acción | Método y ruta |
| --- | --- |
| Entrar, verificar sesión, salir | `POST /demo/sessions` con `{profileId, code}`; `GET /demo/sessions/current`; `DELETE /demo/sessions/current` |
| Descubrir | `GET /recommendations` |
| Listar y abrir playlists | `GET /playlists` (objeto `{items}`); `GET /playlists/{playlistId}` |
| Guardar | `PUT /playlists/{playlistId}/tracks/{songId}`, sin cuerpo; devuelve `{playlistId, songId, position, created}` |
| Crear, renombrar y eliminar | `POST /playlists` con `{name}`; `PATCH /playlists/{playlistId}` con `{name}`; `DELETE /playlists/{playlistId}` |
| Quitar pista y reordenar | `DELETE /playlists/{playlistId}/tracks/{songId}`; `PUT /playlists/{playlistId}/track-order` con `{songIds:[...]}` |
| Abrir catálogo y ficha editorial (solo Editor) | `GET /songs` y `GET /songs/{songId}/editorial` |
| Editar notas | `PATCH /songs/{songId}/editorial` con `{notes:[{text,source}]}` |

**Orden en Stitch:** enlaza primero el recorrido que cierra con la pista guardada; duplica Descubrir en variantes cargando, vacío, parcial y fallido; diseña móvil; por último agrega los formularios H2. Incluye los nombres de pantallas y estados en la entrega. El prototipo no es evidencia de integración hasta conectarse y probarse contra la API.
