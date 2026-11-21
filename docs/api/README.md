# API REST local de SoundGraph

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- Especificación OpenAPI: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) · [exportación para compartir](openapi.json).
- Comprobación de las tres dependencias: `GET /health/ready` → `200 {"status":"ok"}` o `503 service_unavailable`. Swagger UI usa los recursos web por defecto de FastAPI; el contrato JSON y la API no dependen de ellos.

## Probar la demo en Swagger

1. Levanta los motores y aplica la semilla siguiendo el [README](../../README.md).
2. En **Sesión → POST /api/v1/demo/sessions → Try it out**, usa `profileId: p-ana-main` y el valor local de `DEMO_CODE_ANA` que se creó en `.env.demo`. No pegues el código en el repositorio, una captura, el cartel o Stitch.
3. Ejecuta **GET /api/v1/recommendations** en el mismo navegador y origen. El navegador envía automáticamente la cookie que recibió al entrar; no escribas la cookie en **Authorize**.
4. Usa **PUT /api/v1/playlists/{playlistId}/tracks/{songId}** con `pl-ana-demo` y `c-cream`. El primer guardado nuevo devuelve `201`; si ya existía devuelve `200` con la misma posición. Consulta **GET /api/v1/playlists/{playlistId}** para verificar que quedó guardada.
5. Si solo quieres volver al estado inicial sin borrar bases, quita esa pista con **DELETE /api/v1/playlists/{playlistId}/tracks/{songId}**. Cierra sesión mediante **DELETE /api/v1/demo/sessions/current**.

## Contrato para el frontend

Mismo origen; cookie opaca temporal, `HttpOnly`, `SameSite=Strict` y revocada en SQL al cerrar sesión. Se comprueba el origen de las mutaciones de navegador. Es una demo HTTP local, **no** una autenticación para producción; no publiques el puerto ni las credenciales. El usuario/rol y la propiedad se comprueban desde PostgreSQL, no desde los datos de la interfaz.

| Método y ruta bajo `/api/v1` | Entrada y salida |
| --- | --- |
| `POST /demo/sessions` | `{profileId, code}` → `201` con `{profileId, displayName, role}` y cookie |
| `GET /demo/sessions/current`, `DELETE /demo/sessions/current` | Perfil actual `200` o cierre `204` |
| `GET /recommendations?limit=10` | `200 {items:[{song, affinity}], partial}`. Límite 1–25; `song={songId,title,editorial}`. |
| `GET /playlists`, `GET /playlists/{playlistId}` | `200 {items}` o `{playlistId,name,trackCount,tracks:[{songId,position,song}]}`; una ficha faltante se representa con `song:null`. |
| `POST /playlists`, `PATCH /playlists/{playlistId}`, `DELETE /playlists/{playlistId}` | `{name}` para crear `201` o renombrar `200`; eliminar `204`. |
| `PUT /playlists/{playlistId}/tracks/{songId}`, `DELETE /playlists/{playlistId}/tracks/{songId}` | Guardar sin cuerpo → `{playlistId,songId,position,created}`, `201/200`; quitar `204`. |
| `PUT /playlists/{playlistId}/track-order` | `{songIds:[...]}` con la permutación exacta de las pistas presentes → `204`. |
| `PATCH /songs/{songId}/editorial` | `{notes:[{text,source}]}` → ficha actualizada, solo rol editorial. Sustituye la sección de notas, sin modificar créditos o título. |

Los errores gestionados usan `{code,message}` y, para validación de campos, pueden añadir `fields`. Códigos útiles: `invalid_credentials`, `session_required`, `invalid_origin`, `editor_required`, `playlist_not_found`, `song_not_found`, `invalid_input`, `invalid_track_order`, `service_unavailable`.

**Consistencia:** PostgreSQL verifica la sesión y posee las playlists; Neo4j devuelve candidatos; MongoDB hidrata fichas en bloque. Se omiten recomendaciones con ficha ausente y se marca `partial: true`. Guardar valida un identificador existente y escribe en una sola transacción SQL. El bloqueo de la fila de playlist serializa operaciones concurrentes sobre sus pistas; las altas repetidas no cambian la posición. La edición de notas escribe únicamente en MongoDB.

## Prueba HTTP aislada

```sh
export SOUNDGRAPH_API_PORT=18080
docker compose -p soundgraph-test up -d --wait postgres mongo neo4j
docker compose -p soundgraph-test build tools api
docker compose -p soundgraph-test run --rm --no-deps tools
docker compose -p soundgraph-test up -d --no-deps --wait api
python3 tests/http/test_api.py
docker compose -p soundgraph-test down
unset SOUNDGRAPH_API_PORT
```

La prueba requiere el proyecto `soundgraph-test` publicado en loopback en el puerto 18080. Inserta registros temporales, retira/restaura una ficha y detiene/reinicia el Neo4j **de pruebas**, nunca el de desarrollo.
