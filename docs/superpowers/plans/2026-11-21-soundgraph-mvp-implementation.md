# SoundGraph — Plan de implementación del MVP

**Estado:** H0 y API REST validados. Pendiente conectar y probar la interfaz. [Evidencia de H0](../../evidence/2026-11-21-h0-data-seed.md) · [Evidencia de API](../../evidence/2026-11-21-h1-rest-api.md).

**Diseño de referencia:** [MVP de descubrimiento musical](../specs/2026-11-21-soundgraph-mvp-design.md) · criterios académicos AC-01 a AC-08 de la documentación local.

**Primer hito demostrable:** abrir el perfil de Ana, ver «C.R.E.A.M.» con un motivo y su ficha, guardar la pista y verificar que permanece tras recargar. El cartel vence el **25 de noviembre, 23:59**; la entrega técnica, el **27 de noviembre**.

## 1. Stack y prerrequisitos

Backend **Python 3.12 + FastAPI** y contrato REST/OpenAPI. La interfaz se maquetará en Stitch y se integrará desde el mismo origen. Psycopg 3, PyMongo, el controlador oficial de Neo4j y FastAPI están fijados en `requirements.lock.txt`. No se instalaron paquetes en el Python del sistema.

| Componente | Imagen base verificada en el registro | Digest del índice multiplataforma |
| --- | --- | --- |
| Backend | `python:3.12-slim-bookworm` | `sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df` |
| Relacional | `postgres:17-bookworm` | `sha256:837bed18782820fe967067cb5328b02b0d9992c1be9a37ee0c9c492cfc03af3b` |
| Documental | `mongo:8.0` | `sha256:479e85ced54ffb8a40dade1dcde2da2a9ae858515b9415e9cc54bfb8f0575d01` |
| Grafo | `neo4j:5.26.33-community` | `sha256:51d0314ef86074f519003da8dd4daaa9fff72b8479672b742d7cab7f3064e3ed` |

Las imágenes incluyen Linux amd64 y arm64; la ejecución solo se comprobó en el Mac arm64 mediante Docker Desktop. Usar proyectos Compose separados (`soundgraph-dev` y `soundgraph-test`), volúmenes propios y ningún puerto de base publicado. Al implementar la interfaz, comprobar que el puerto esté libre y enlazar el HTTP de la demo solo a `127.0.0.1`. No reutilizar, limpiar ni reiniciar volúmenes ajenos.

## 2. Orden de trabajo y pruebas

Las casillas distinguen lo ejecutado del trabajo pendiente.

### H0 — Entorno, esquemas y una semilla común

- [x] Añadir `compose.yaml`, `Dockerfile`, `.env.example` y dependencias fijadas. Compose inicia los tres motores con comprobaciones de salud. Las credenciales de los motores se generan localmente y no se versionan.
- [x] Crear `database/postgres/001_schema.sql`, `database/mongo/song_validator.json`, `database/neo4j/001_schema.cypher` y `database/fixtures/demo.json`. El esquema de Neo4j Community usa unicidad y valida presencia de identificadores en la carga; no copia DDL Enterprise de la práctica. Se conservaron intactos `soundgraph_schema.cypher` y `actividad_soundgraph_completa.md`.
- [x] Implementar `scripts/seed.py` y `scripts/check_references.py`. Cargar perfiles y fichas primero y escuchas después. Sembrar a Ana, un oyente con dos escuchas en común, otro perfil sin historial y un editor. La semilla repetida no duplica datos ni sobrescribe playlists o fichas editadas.
- [x] Probar en una instancia aislada: arranque desde volúmenes vacíos, segunda carga sin duplicados, rechazo de un documento inválido, detección de una referencia huérfana y ausencia de identificadores sin valor en el grafo. Versiones registradas en la evidencia.

### H1 — Recomendación y guardado de extremo a extremo, antes del cartel

- [x] Implementar sesión local y rutas en `backend/main.py`, `backend/repositories/` y `backend/services/`. La sesión resuelve perfil en PostgreSQL y el backend verifica origen/permisos. Publicación de desarrollo solo en loopback.
- [x] Añadir y probar `database/neo4j/queries/recommendations.cypher`. Usa parámetros, excluye canciones ya escuchadas, agrupa por `songId`, cuenta perfiles distintos y ordena empates por ID.
- [x] Integrar la consulta con límite y recuperación en bloque de fichas. Validar existencia al guardar y serializar cambios en una sola transacción SQL.
- [x] Probar la API con los tres motores reales mediante `tests/http/test_api.py`: guardado idempotente, ficha ausente, dependencia caída, perfil sin historial y acceso ajeno.
- [ ] Conectar la maqueta del [brief UI/UX](../../frontend/soundgraph-ui-ux-handoff.md) y comprobar desde la interfaz: recomendar, guardar dos veces sin duplicar y recargar.
- [ ] Guardar en `docs/evidence/` los comandos, entradas, resultados obtenidos y limitaciones. Usar únicamente evidencia de este flujo y de pruebas realmente ejecutadas para el cartel. Confirmar y probar el enlace del repositorio antes de generar su QR.

### H2 — Completar operaciones y preparar la entrega técnica

- [x] Completar y probar vía API altas, cambios, borrados, reordenamiento de playlists y edición de notas por un perfil editor. Un orden inválido no deja cambios parciales y una edición no cambia la afinidad.
- [ ] Conectar a la interfaz las acciones de administración y edición.
- [ ] Documentar en `README.md` el arranque limpio y la parada de los servicios propios, y en `docs/api/` y `docs/models/` el contrato, el diccionario y las restricciones. Incorporar el catálogo de operaciones, matriz tecnológica y evidencias a los entregables de la guía.
- [ ] Ejecutar pruebas unitarias/de componentes y repetir la integración con un proyecto nuevo. Medir descubrimiento con calentamiento explícito, tamaño de semilla, número de solicitudes y entorno. Registrar los resultados reales y no extrapolarlos a producción.

## 3. Contrato REST inicial

Base `/api/v1`; la respuesta de error contiene un código estable y un mensaje sin datos internos. El backend usa consultas parametrizadas. `/health/ready` comprueba los tres motores, sin revelar credenciales.

| Hito | Ruta | Resultado en el caso normal |
| --- | --- | --- |
| H1 | `POST /demo/sessions` · `GET /demo/sessions/current` · `DELETE /demo/sessions/current` | Iniciar, consultar o cerrar la sesión local de un perfil sintético. |
| H1 | `GET /recommendations` | `200`: lista ordenada con ficha, afinidad y una señal de resultados parciales si faltan fichas. Vacío normal si no hay coincidencias y las dependencias funcionan. |
| H1 | `GET /playlists` · `GET /playlists/{playlistId}` | `200`: playlists propias y, en la vista de detalle, sus pistas en orden. |
| H1 | `PUT /playlists/{playlistId}/tracks/{songId}` | `201` al agregar, `200` si ya estaba guardada, sin cambiar su posición. |
| H2 | `POST /playlists` · `PATCH /playlists/{playlistId}` · `DELETE /playlists/{playlistId}` | `201` al crear, `200` al renombrar y `204` al eliminar. |
| H2 | `PUT /playlists/{playlistId}/track-order` · `DELETE /playlists/{playlistId}/tracks/{songId}` | Recibe una permutación exacta de las pistas actuales y actualiza el orden en transacción; permite retirar una pista. |
| H2 | `PATCH /songs/{songId}/editorial` | `200`: actualiza únicamente la sección editorial autorizada y validada. |

Errores transversales: `401` sin sesión válida; `403` sin rol editorial; `404` para playlist que no pertenece al perfil o una canción sin ficha; `422` para una entrada inválida; `503` si una dependencia no responde. El servicio no devuelve éxito si la escritura no se completó.

### Referencias técnicas

- [FastAPI en contenedores](https://fastapi.tiangolo.com/deployment/docker/)
- [Neo4j en Docker](https://neo4j.com/docs/operations-manual/current/docker/introduction/), [restricciones de Cypher 5](https://neo4j.com/docs/cypher-manual/5/constraints/) y [compatibilidad del controlador Python](https://neo4j.com/docs/python-manual/current/install/)
- [Compatibilidad de PyMongo](https://www.mongodb.com/docs/drivers/compatibility/?driver-language=python&python-driver-framework=pymongo)
