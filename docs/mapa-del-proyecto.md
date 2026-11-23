# SoundGraph — Qué se usa y cuándo

## Cada base hace un trabajo distinto

| Motor | Fuente oficial | Ejemplo concreto |
| --- | --- | --- |
| **PostgreSQL** | Perfiles, rol, sesiones, playlists y posición de sus pistas. | Al entrar, verifica el perfil. Al guardar o reordenar, aplica propiedad, unicidad y transacciones para no dejar pistas repetidas ni posiciones parciales. |
| **MongoDB** | Ficha de canción: título, créditos y notas. | En «Ver ficha» se muestran datos del documento. En «Editorial» el editor lee y actualiza sus notas; no cambia títulos, créditos ni afinidad. También se comprueba que la ficha exista antes de guardar la pista. |
| **Neo4j** | Relaciones de escucha entre perfiles y canciones. | Recorre escuchas compartidas para hallar candidatas que Ana no escuchó y cuenta **perfiles distintos**, no caminos. No guarda playlists ni interviene al editar notas. |

Al recomendar, **PostgreSQL** valida la sesión → **Neo4j** obtiene candidatas y afinidad → **MongoDB** aporta las fichas. La API combina todo en una respuesta. Al gestionar una playlist la escritura va a PostgreSQL; al cambiar notas, a MongoDB. No se sincronizan copias de fichas entre motores.

## Qué archivos y funciones se usan

No todo se ejecuta al iniciar la app. La revisión separa las referencias del código, las pruebas efectivamente ejecutadas y el material que no se ejecuta.

| Grupo | Cuándo participa |
| --- | --- |
| [`frontend/index.html`](../frontend/index.html), [`app.js`](../frontend/assets/app.js), [`app.css`](../frontend/assets/app.css), [`mark.svg`](../frontend/assets/mark.svg) | Son la página, lógica, estilos e icono que usa el navegador. JavaScript llama a los endpoints de la misma aplicación; no conecta a las bases. |
| [`backend/main.py`](../backend/main.py), [modelos](../backend/schemas.py), [errores](../backend/errors.py), [servicios](../backend/services/), [repositorios](../backend/repositories/) | Son código de ejecución: despacho de rutas, validación/autorización y acceso a datos. Muchas funciones son callbacks o dependencias que invoca FastAPI. Las rutas editoriales solo se activan para el rol Editor; las rutas de falla se usan cuando corresponde, no en cada solicitud. |
| [`scripts/storage.py`](../scripts/storage.py) y [consulta Cypher de recomendación](../database/neo4j/queries/recommendations.cypher) | Se importan en la API: conexiones y consulta ejecutada al descubrir música. |
| [`Dockerfile`](../Dockerfile), [`compose.yaml`](../compose.yaml), [dependencias](../requirements.lock.txt) | Construyen y levantan el entorno. `requirements.in` declara dependencias de entrada; la imagen instala las versiones de `requirements.lock.txt`. `.dockerignore` y `.gitignore` son filtros de herramientas, no código de la app. |
| [`init_env.py`](../scripts/init_env.py), [`seed.py`](../scripts/seed.py), [esquemas, validadores y datos base](../database/), [`.env.example`](../.env.example) | Preparación. El cargador ejecuta los scripts SQL y Cypher, aplica el validador y carga la semilla. Los motores aplican esas restricciones después de prepararse; no releen los archivos en cada petición. La plantilla no contiene credenciales reales. |
| [`check_references.py`](../scripts/check_references.py), [`measure_demo.py`](../scripts/measure_demo.py), [`tests/`](../tests/) | Verificación bajo demanda. El cargador reutiliza la comprobación de referencias; los tests y el benchmark no forman parte de las pantallas ni se ejecutan con cada solicitud. |
| [`README.md`](../README.md) y [`docs/`](./) | Guías, diseño y evidencias. El JSON de OpenAPI versionado es una copia para consulta; FastAPI genera el contrato que sirve en ejecución a partir de sus rutas y modelos. Las maquetas y el CSV del benchmark no alimentan la aplicación. |
| Práctica histórica, capturas, carpetas internas y notas de Stitch | Material de trabajo local, excluido del repositorio público y sin dependencia de la app. |

**Dependencias:** como el HTML se sirve con `FileResponse` y el proyecto no usa plantillas Jinja, se retiraron Jinja2 y su dependencia MarkupSafe. `pytest` se conserva para las pruebas. No haber visto ejecutar una función en una prueba no demuestra que sea código muerto.
