# SoundGraph — Catálogo de operaciones y consultas

**Alcance:** operaciones de la versión actual. Los cuerpos completos y tipos se encuentran en [OpenAPI](api/openapi.json). Las rutas de negocio llevan el prefijo `/api/v1`; las protegidas requieren una sesión de demo. **PG** = PostgreSQL, **MG** = MongoDB, **NG** = Neo4j. Las respuestas de error tienen código y mensaje; un estado que aparece en «límites y errores» no se considera probado salvo que la columna de evidencia lo indique.

## Operaciones de la aplicación

| ID · propósito | Ruta · motores | Entrada y validación | Salida esperada | Límites, errores y evidencia observada |
| --- | --- | --- | --- | --- |
| S-00 · comprobar dependencias | `GET /health/ready` (sin prefijo) · PG + MG + NG | Sin entrada | `200`, `{"status":"ok"}` | H01: disponibilidad normal; H07: Neo4j detenido devolvió `503` y se recuperó. |
| S-01 · iniciar sesión | `POST /demo/sessions` · PG | `profileId` válido y `code` de 1–128 caracteres; credenciales correctas | `201`, perfil y cookie HttpOnly/SameSite Strict | H02: código incorrecto → `401`; sesiones válidas emitidas en la suite. Códigos solo locales. |
| S-02 · recuperar sesión | `GET /demo/sessions/current` · PG | Cookie y sesión vigente | `200`, `{profileId, displayName, role}` | H02: perfil válido; la revocación del token se comprobó en una ruta protegida distinta. |
| S-03 · cerrar sesión | `DELETE /demo/sessions/current` · PG si hay token reconocible | Cookie si está presente; origen permitido | `204`, sin cuerpo; revoca sesión y elimina cookie | H02: revocación comprobada; escribir desde un origen no permitido se rechaza con `403` (probado con creación de playlist). |
| R-01 · recomendar con explicación | `GET /recommendations` · PG + NG + MG | Sesión; `limit` 1–25, por defecto 10 | `200`, `{items: [{song, affinity}], partial}` | H03: Ana recibe `c-cream`, afinidad 1; perfil nuevo recibe vacío. H06: ficha ausente → `partial: true`. H07: motor caído → `503`. |
| P-01 · listar playlists propias | `GET /playlists` · PG | Sesión | `200`, `{items: [{playlistId, name, trackCount}]}` | Sin listas devuelve arreglo vacío; sin sesión `401`. La medición verificó 100 respuestas con la lista de Ana y 0 pistas. |
| P-02 · abrir playlist | `GET /playlists/{playlistId}` · PG + MG cuando hay pistas | Sesión, identificador válido y propiedad | `200`, detalle con pistas ordenadas y fichas | H03: playlist ajena → `404`; H04: orden correcto; H06: pista con ficha ausente → `song: null`, se conserva la posición. |
| P-03 · crear playlist | `POST /playlists` · PG | Sesión; `name` de 1–100 caracteres tras recorte; nombres no necesariamente únicos | `201`, resumen con 0 pistas | H04: alta válida; H02: origen de escritura rechazado con `403`. Entrada de formato incorrecto: `422` previsto por el esquema. |
| P-04 · renombrar playlist | `PATCH /playlists/{playlistId}` · PG | Sesión, propiedad e igual regla de nombre | `200`, resumen actualizado | H04: conserva el nombre sin espacios de extremos. Ajena o ausente: `404` previsto. |
| P-05 · eliminar playlist | `DELETE /playlists/{playlistId}` · PG | Sesión y propiedad | `204`, elimina playlist y sus entradas, no las fichas | H04: después de eliminar, consultar la playlist dio `404`. |
| P-06 · guardar pista | `PUT /playlists/{playlistId}/tracks/{songId}` · PG + MG | Sesión, propiedad y ficha existente; sin cuerpo | `201` al insertar; `200` si ya existe; `{playlistId, songId, position, created}` | H04: dos solicitudes en paralelo devolvieron `201` y `200` con una sola posición. H03/H06: ajena o ficha ausente → `404`. En navegador quedó guardada tras recargar. |
| P-07 · reordenar pistas | `PUT /playlists/{playlistId}/track-order` · PG | Sesión, propiedad y `songIds` con la permutación exacta de todas las pistas, máximo 1000 | `204`, actualización transaccional | H04: nuevo orden persistió; orden incompleto devolvió `422` sin cambiar el anterior. |
| P-08 · quitar pista | `DELETE /playlists/{playlistId}/tracks/{songId}` · PG | Sesión, propiedad e identificadores válidos | `204`; compacta las posiciones superiores si quitó una pista | H04: se eliminó la pista y la restante pasó a la posición 1. Si falta la pista en playlist propia, `204` está implementado; no se verificó como caso separado. |
| E-01 · editar notas | `PATCH /songs/{songId}/editorial` · PG + MG | Sesión de editor; 1–20 notas, `text` de 1–1000, `source` de 1–200 tras recorte | `200`, ficha con las notas reemplazadas | H05: editor actualiza notas sin cambiar créditos ni afinidad; oyente → `403`; nota inválida → `422`. Disponible por API, no como edición en navegador. |

**Trazabilidad.** H01–H07 identifican `test_01` a `test_07` de la [suite HTTP](../tests/http/test_api.py). Resultados registrados en la [evidencia REST](evidence/2026-11-21-h1-rest-api.md) y la [evidencia en navegador](evidence/2026-11-21-h1-frontend.md). H00 verifica la entrega de los recursos frontend y no representa una operación de dominio. La [medición HTTP](evidence/2026-11-21-rendimiento.md) es una ejecución separada.

## Consultas representativas por motor

Se ejecutaron en el entorno aislado `soundgraph-bench` con la semilla sin pistas guardadas. Las dos primeras son lecturas representativas; la tercera usa literalmente el archivo Cypher del integrador.

| ID · consulta | Parámetros y resultado esperado | Resultado observado y caso negativo |
| --- | --- | --- |
| Q-SQL · listar playlists y contar pistas con `LEFT JOIN` | En el [repositorio SQL](../backend/repositories/sql.py), `list_playlists(owner)`, propietario `p-ana-main`; una fila `(playlist_id, name, count)`. | `(pl-ana-demo, Para escuchar, 0)`. Como prueba de integridad distinta de esta lectura, PostgreSQL rechazó un propietario inexistente al insertar una playlist. |
| Q-DOC · proyectar ficha y notas con `find` y filtro por `_id` | `{"_id":{"$in":["c-cream"]}}`, proyección `{"title":1, "editorial.notes":1}`; una ficha coincidente. Véase [by_ids en el repositorio](../backend/repositories/music.py). | Una ficha con ID `c-cream`, título «C.R.E.A.M.» y una nota. La prueba de integridad separada registró código 121 al insertar una ficha sin sección editorial. |
| Q-GRAFO · contar perfiles afines, no caminos | [Cypher parametrizado](../database/neo4j/queries/recommendations.cypher): `profile_id=p-ana-main`, `limit=10`; filas `(song_id, affinity)`. | `(c-cream, 1)`. La prueba de la consulta con el perfil nuevo devuelve vacío. La auditoría verificó detección de referencias huérfanas con datos de prueba. |

Las pruebas de los motores y de consistencia están en la [suite de integración](../tests/integration/) y la [evidencia de carga](evidence/2026-11-21-h0-data-seed.md). Las referencias y las reglas se explican en el [modelo integrado](models/modelado-integrado.md).
