# SoundGraph — Catálogo de operaciones y consultas

**Alcance:** operaciones de la versión actual. Los cuerpos completos y tipos se encuentran en [OpenAPI](api/openapi.json). Las rutas de negocio llevan el prefijo `/api/v1`; las protegidas requieren una sesión de demo. **PG** = PostgreSQL, **MG** = MongoDB, **NG** = Neo4j. Las respuestas de error tienen código y mensaje; un estado que aparece en «límites y errores» no se considera probado salvo que la columna de evidencia lo indique.

**Cómo leer la evidencia:** H01–H10 identifican pruebas de la suite HTTP ejecutada en la candidata; H11 es un sondeo HTTP adicional. UI-01/UI-02/UI-03 identifican recorridos visuales de escritorio. Las pruebas no implican cobertura exhaustiva de toda combinación de datos. Las expresiones «previsto», «implementado» o «no se verificó» describen el contrato o el código, no una prueba aprobada de ese caso. Los resultados por ejecución y revisión se separan en el [índice de entregables](entregables.md#cómo-leer-las-evidencias).

La [validación aislada del 27 de noviembre](evidence/2026-11-27-cierre-candidata.md) ejecutó H00–H10 sobre el código base `fb24f00`; UI-01 cubre los recorridos principales de Ana/Editor, UI-02 el reingreso con código y UI-03 la gestión visual de playlists. Esta auditoría relaciona cada endpoint con evidencia, pero no convierte en probados los casos que cada fila marque como previstos o no verificados.

## Operaciones de la aplicación

| ID · propósito | Ruta · motores | Entrada y validación | Salida esperada | Límites, errores y evidencia observada |
| --- | --- | --- | --- | --- |
| S-04 · crear perfil personal | `POST /profiles` · PG + NG | `displayName` de 1–100 caracteres; no admite rol ni ID | `201`, perfil oyente, código personal y cookie | H09 HTTP: creación, identidad aleatoria, rol listener y nodo creado. H10: alta durante fallo de Neo4j, `graphPending: true` y reconciliación. UI-02: creación visual. |
| S-05 · entrar con código personal | `POST /sessions` · PG + NG si pendiente | `code` completo generado al crear | `201`, perfil y cookie | H09 HTTP: reingreso, misma identidad y playlist propia; código inválido → `401`. H10: reintento de perfil pendiente. UI-02: cierre y reingreso visual con el código, misma identidad en pantalla. |
| S-00 · comprobar dependencias | `GET /health/ready` (sin prefijo) · PG + MG + NG | Sin entrada | `200`, `{"status":"ok"}` | Comprueba también la consulta real de recomendación. H01: `200` con los motores disponibles. H07: durante una caída `503`; tras reinicio, vuelve a `200` y recomienda C.R.E.A.M. |
| S-01 · iniciar sesión | `POST /demo/sessions` · PG | `profileId` válido y `code` de 1–128 caracteres; credenciales correctas | `201`, perfil y cookie HttpOnly/SameSite Strict | H02: código incorrecto → `401`; sesiones válidas emitidas en la suite. Códigos solo locales. |
| S-02 · recuperar sesión | `GET /demo/sessions/current` · PG | Cookie y sesión vigente | `200`, `{profileId, displayName, role}` | H02: perfil válido; la revocación del token se comprobó en una ruta protegida distinta. |
| S-03 · cerrar sesión | `DELETE /demo/sessions/current` · PG si hay token reconocible | Cookie si está presente; origen permitido | `204`, sin cuerpo; revoca sesión y elimina cookie | H02: revocación comprobada; escribir desde un origen no permitido se rechaza con `403` (probado con creación de playlist). |
| R-01 · recomendar con explicación | `GET /recommendations` · PG + NG + MG | Sesión; `limit` 1–25, por defecto 10 | `200`, `{items: [{song, affinity}], partial}` | H03: Ana recibe `c-cream`, afinidad 1; perfil nuevo recibe vacío. H06: ficha ausente → `partial: true`. H07: motor caído → `503`. |
| P-01 · listar playlists propias | `GET /playlists` · PG | Sesión | `200`, `{items: [{playlistId, name, trackCount}]}` | Sin listas devuelve arreglo vacío; sin sesión `401`. La medición verificó 100 respuestas con la lista de Ana y 0 pistas. |
| P-02 · abrir playlist | `GET /playlists/{playlistId}` · PG + MG cuando hay pistas | Sesión, identificador válido y propiedad | `200`, detalle con pistas ordenadas y fichas | H03: playlist ajena → `404`; H04: orden correcto; H06: pista con ficha ausente → `song: null`, se conserva la posición. |
| P-03 · crear playlist | `POST /playlists` · PG | Sesión; `name` de 1–100 caracteres tras recorte; nombres no necesariamente únicos | `201`, resumen con 0 pistas | H04: alta válida; H02: origen de escritura rechazado con `403`; H11: nombre solo espacios → `422`; UI-03: alta visual. |
| P-04 · renombrar playlist | `PATCH /playlists/{playlistId}` · PG | Sesión, propiedad e igual regla de nombre | `200`, resumen actualizado | H04: conserva el nombre sin espacios de extremos; H11: vacío → `422` sin mutación; UI-03: renombre y persistencia visual. Ajena o ausente: `404` previsto. |
| P-05 · eliminar playlist | `DELETE /playlists/{playlistId}` · PG | Sesión y propiedad | `204`, elimina playlist y sus entradas, no las fichas | H04: después de eliminar, consultar la playlist dio `404`; UI-03 abrió la confirmación y canceló (no ejecutó la eliminación). |
| P-06 · guardar pista | `PUT /playlists/{playlistId}/tracks/{songId}` · PG + MG | Sesión, propiedad y ficha existente; sin cuerpo | `201` al insertar; `200` si ya existe; `{playlistId, songId, position, created}` | H04: dos solicitudes en paralelo devolvieron `201` y `200` con una sola posición. H03/H06: ajena o ficha ausente → `404`. En navegador quedó guardada tras recargar. |
| P-07 · reordenar pistas | `PUT /playlists/{playlistId}/track-order` · PG | Sesión, propiedad y `songIds` con la permutación exacta de todas las pistas, máximo 1000 | `204`, actualización transaccional | H04: nuevo orden persistió; orden incompleto devolvió `422` sin cambiar el anterior; UI-03: orden visual persistió al recargar. |
| P-08 · quitar pista | `DELETE /playlists/{playlistId}/tracks/{songId}` · PG | Sesión, propiedad e identificadores válidos | `204`; compacta las posiciones superiores si quitó una pista | H04: se eliminó la pista y la restante pasó a la posición 1; H11: pista ausente → `204`; UI-03 retirada visual. |
| E-02 · listar catálogo editorial | `GET /songs` · PG + MG | Sesión de editor; `limit` de 1–50 y cursor `after` opcional | `200`, títulos, IDs y cursor siguiente | H08: paginación sin duplicar filas, límite inválido → `422`, sin sesión → `401`, oyente → `403`. |
| E-03 · abrir ficha para editar | `GET /songs/{songId}/editorial` · PG + MG | Sesión de editor e identificador válido | `200`, ficha con título, créditos y notas | H08: fixture existente y ficticio ausente → `404`; invitado → `401`, oyente → `403`. H05: las notas actualizadas son visibles en una lectura posterior. |
| E-01 · editar notas | `PATCH /songs/{songId}/editorial` · PG + MG | Sesión de editor; 1–20 notas, `text` de 1–1000, `source` de 1–200 tras recorte | `200`, ficha con las notas reemplazadas | H05: editor actualiza notas sin cambiar créditos ni afinidad; oyente → `403`; nota inválida → `422`. También disponible desde Editorial; no edita el título ni los créditos. |

**Trazabilidad.** H01–H10 identifican `test_01` a `test_10` de la [suite HTTP](../tests/http/test_api.py); H00 es la prueba de entrega de frontend y H11 el sondeo complementario de [casos borde](evidence/2026-11-27-catalog-edge-probes.log). El [registro del 27 de noviembre](evidence/2026-11-27-cierre-http.log) conserva los 11 resultados automatizados, incluidos H09–H10; H11 no se suma. La evidencia antigua del 22 de noviembre corresponde a otra versión y se mantiene solo como antecedente. UI-01/UI-02 están descritos en el [registro de cierre](evidence/2026-11-27-cierre-candidata.md); UI-03 está descrito en el [recorrido visual de gestión](evidence/2026-11-27-demo-management-web.log). H00 verifica la entrega de recursos frontend y no representa una operación de dominio. La [medición HTTP de la candidata](evidence/2026-11-27-cierre-candidata.md#medición-http) es una ejecución separada, no una prueba funcional adicional.

## Auditoría endpoint por endpoint — candidata `fb24f00`

La comprobación cotejó las 18 rutas de `docs/api/openapi.json` con las aserciones de H01–H10, la evidencia de navegador y el registro de medición. «Cubierto» significa que hay al menos un resultado observable de la operación, no que todas las entradas y fallas estén probadas.

| Operación | Evidencia de resultado | Límite que permanece explícito |
| --- | --- | --- |
| `GET /health/ready` | H01 disponible; H07 indisponibilidad y recuperación. | Ninguno para los escenarios reportados; no prueba todas las combinaciones de fallos. |
| `POST /demo/sessions` | H02 acceso correcto e inválido. | No evalúa fuerza contra ataques; demo local. |
| `GET /demo/sessions/current` | H02 perfil autenticado; H09 identidad personal. | La autenticación de producción está fuera del alcance. |
| `DELETE /demo/sessions/current` | H02 cierre y revocación; H09 reingreso personal posterior; H11 logout sin cookie reconocible → `204`. | No se prueba revocación de todos los estados de almacenamiento externos. |
| `POST /profiles` | H09 creación/validación; H10 fallo de Neo4j y reconciliación; UI-02 alta web. | Sin transacción distribuida; resultado pendiente se comunica mediante `graphPending`. |
| `POST /sessions` | H09 código válido/inválido; UI-02 reingreso web. | Se probó el flujo de código de demo generado, no políticas de rotación/recuperación de credenciales. |
| `GET /recommendations` | H03 escenario base/vacío; H06 ficha ausente; H07 caída; escenarios Neo4j y API adicionales. | No evalúa relevancia musical ni usuarios reales. |
| `GET /playlists` | Medición 100/100 con lista de Ana; H09 lista propia tras reingreso. | El caso HTTP de lista vacía está probado indirectamente para perfil nuevo al verificar aislamiento; rendimiento no es cobertura adicional. |
| `POST /playlists` | H04 alta y limpieza; UI-01/UI-03 creación visual; H11 nombre en blanco → `422 invalid_input`. | No prueba todos los límites de longitud ni unicidad de nombres (no exigida). |
| `GET /playlists/{playlistId}` | H03 acceso ajeno; H04 orden/detalle; H06 ficha ausente. | Combinaciones arbitrarias de IDs no se enumeraron exhaustivamente. |
| `PATCH /playlists/{playlistId}` | H04 renombre y recorte; H09 denegación de playlist ajena; H11 nombre en blanco → `422` y el nombre anterior permanece; UI-03 renombre/recarga. | No prueba todos los límites de longitud. |
| `DELETE /playlists/{playlistId}` | H04 eliminación; H09 denegación de playlist ajena; UI-03 diálogo confirmado visualmente y cancelado. | UI-03 no ejecutó la eliminación; no se afirma borrado en otros motores. |
| `PUT /playlists/{playlistId}/tracks/{songId}` | H04 concurrencia/duplicado; H03 ajena; H06 ficha ausente; UI-01 guardado y recarga. | No se midieron todas las carreras posibles. |
| `DELETE /playlists/{playlistId}/tracks/{songId}` | H04 quitar y compactar posiciones; H09 ajena; H11 idempotencia; UI-03 retirada visual. | No mide todas las carreras concurrentes de altas/bajas. |
| `PUT /playlists/{playlistId}/track-order` | H04 permutación válida y orden incompleto rechazado sin cambios; H09 ajena; UI-03 orden visual persistido tras recarga. | No prueba cada límite de tamaño ni todos los órdenes posibles. |
| `GET /songs` | H08 paginación, límite, invitado y rol oyente. | No prueba límites de cursor vacíos o toda página posible. |
| `GET /songs/{songId}/editorial` | H08 ficha válida/ausente y permisos; UI-01 lectura durante edición. | No enumera todas las fichas. |
| `PATCH /songs/{songId}/editorial` | H05 nota válida/inválida, preservación de créditos y afinidad; UI-01 guardar, recargar y restaurar. | No implementa control de concurrencia entre editores; última escritura prevalece. |

H11 es un sondeo HTTP suplementario realizado en el entorno limpio; no forma parte del conteo 11/11 del runner automatizado. Su método y resultados se conservan en [casos borde](evidence/2026-11-27-catalog-edge-probes.log). La matriz no convierte los límites listados en fallos de cumplimiento automáticamente: distingue cobertura observada de escenarios no probados. La guía no fija un número mínimo de pruebas ni cobertura porcentual. Los límites restantes siguen identificados sin presentarlos como probados.

## Consultas representativas por motor

Las nuevas operaciones de perfiles se verifican en H09 (identidad, acceso posterior y separación de playlists) y H10 (alta durante caída del grafo y reconciliación); UI-02 agrega el recorrido visual de reingreso con código y confirma que vuelve el mismo perfil. La [evidencia del 23 de noviembre](evidence/2026-11-23-perfiles-recuperacion-ui.md) registra también la reproducción y corrección de H07 sin alterar su aserción.

Se ejecutaron en el entorno aislado `soundgraph-bench` con la semilla sin pistas guardadas. Las dos primeras son lecturas representativas; la tercera usa literalmente el archivo Cypher del integrador.

| ID · consulta | Parámetros y resultado esperado | Resultado observado y caso negativo |
| --- | --- | --- |
| Q-SQL · listar playlists y contar pistas con `LEFT JOIN` | En el [repositorio SQL](../backend/repositories/sql.py), `list_playlists(owner)`, propietario `p-ana-main`; una fila `(playlist_id, name, count)`. | `(pl-ana-demo, Para escuchar, 0)`. Como prueba de integridad distinta de esta lectura, PostgreSQL rechazó un propietario inexistente al insertar una playlist. |
| Q-DOC · proyectar ficha y notas con `find` y filtro por `_id` | Consulta representativa de prueba: `{"_id":{"$in":["c-cream"]}}`, proyección `{"title":1, "editorial.notes":1}`; una ficha coincidente. La API usa por separado [by_ids](../backend/repositories/music.py), que consulta por `$in` sin esa proyección. | Una ficha con ID `c-cream`, título «C.R.E.A.M.» y una nota. La prueba de integridad separada registró código 121 al insertar una ficha sin sección editorial. |
| Q-GRAFO · contar perfiles afines, no caminos | [Cypher parametrizado](../database/neo4j/queries/recommendations.cypher): `profile_id=p-ana-main`, `limit=10`; filas `(song_id, affinity)`. | `(c-cream, 1)`. La prueba de la consulta con el perfil nuevo devuelve vacío. La auditoría verificó detección de referencias huérfanas con datos de prueba. |

Las pruebas de los motores y de consistencia están en la [suite de integración](../tests/integration/) y la [evidencia de carga](evidence/2026-11-21-h0-data-seed.md). Las referencias y las reglas se explican en el [modelo integrado](models/modelado-integrado.md).
