# SoundGraph — Índice de entregables

Este es el índice de entregables de la candidata de código `fb24f00`; los commits posteriores en `main` agregan documentación y evidencia, no cambian ese código candidato. Cada entregable enlaza su artefacto y, cuando corresponde, evidencia de ejecución. El plan y diseño del MVP se conservan como antecedentes de trabajo.

La [actualización local de perfiles personales, recuperación de Neo4j e interfaz](evidence/2026-11-23-perfiles-recuperacion-ui.md) registra las pruebas afectadas y el pendiente de revisión visual móvil; sus resultados se separan de las ejecuciones históricas siguientes.

| Entregable de la guía | Dónde revisarlo |
| --- | --- |
| 1. Propuesta | [Problema, objetivo, usuarios, alcance y casos de uso](propuesta.md). |
| 2. Modelado | [Conceptual](models/modelado-integrado.md#modelo-conceptual-común), [relacional](models/modelado-integrado.md#relacional--postgresql), [documental](models/modelado-integrado.md#documental--mongodb), [grafo](models/modelado-integrado.md#grafo--neo4j) y [reglas entre motores](models/modelado-integrado.md#reglas-entre-motores). |
| 3. Arquitectura y selección tecnológica | [Diagrama, matriz tecnológica, decisión REST y consistencia](arquitectura.md). |
| 4. Implementación de las tres bases | [Esquemas y semilla](../database/), [scripts SQL de carga](../database/postgres/seed/), [scripts Cypher de carga](../database/neo4j/seed/), [cargador](../scripts/seed.py), [evidencia de carga e integridad](evidence/2026-11-21-h0-data-seed.md), [consultas observadas por motor](catalogo-operaciones.md#consultas-representativas-por-motor) y [prueba de cardinalidad del grafo](evidence/2026-11-22-verificacion-entrega.md#cardinalidad-y-dirección-en-neo4j). |
| 5. Catálogo de operaciones y consultas | [18 operaciones de la API, entradas, resultados esperados y pruebas observadas](catalogo-operaciones.md). |
| 6. Backend y API | [Rutas](../backend/main.py), [servicios](../backend/services/), [repositorios](../backend/repositories/) y [contrato](api/openapi.json). |
| 7. Aplicación e integración | [Frontend](../frontend/), [recorrido de evaluación](demostracion.md), [evidencia de recomendación, ficha, guardado y recarga](evidence/2026-11-21-h1-frontend.md) y [evidencia de gestión de playlists y editor de notas](evidence/2026-11-21-h2-frontend.md). |
| 8. Pruebas, documentación y despliegue | [Instrucciones de ejecución](../README.md#arranque-local), [configuración de ejemplo](../.env.example), [pruebas unitarias](../tests/unit/), [integración](../tests/integration/), [pruebas HTTP](../tests/http/) y [validación de entrega y medición HTTP](evidence/2026-11-22-verificacion-entrega.md). Repositorio: [ArturoYJ/soundgraph](https://github.com/ArturoYJ/soundgraph). |

El **cartel final y el QR** se entregan por separado. El QR debe apuntar al repositorio y probarse antes de entregar el cartel. La evidencia del integrador está en texto, código y datos de prueba; las capturas se conservan fuera de la selección pública.

[Matriz de seguimiento y pendientes del cierre](seguimiento-cierre.md).

La [reproducibilidad desde README](evidence/2026-11-27-reproducibilidad.log), la [suite HTTP en el entorno limpio](evidence/2026-11-27-repro-http.log), el [sondeo HTTP de casos borde](evidence/2026-11-27-catalog-edge-probes.log), el [ensayo principal de demo web](evidence/2026-11-27-demo-web.log), el [recorrido visual de gestión de playlists](evidence/2026-11-27-demo-management-web.log), la [eliminación visual confirmada](evidence/2026-11-28-demo-delete-web.log), la [evaluación ampliada del candidato](evidence/2026-11-27-fb24f-evaluacion-ampliada.md), la [revisión de instrucciones adicionales del cartel](evidence/2026-11-27-material-adicional-poster.md) y la [auditoría endpoint por endpoint](catalogo-operaciones.md#auditoría-endpoint-por-endpoint--candidata-fb24f00) complementan la verificación. La [matriz de seguimiento](seguimiento-cierre.md) identifica lo aún pendiente.

## Validación de la candidata del 27 de noviembre

La [validación aislada de `fb24f00`](evidence/2026-11-27-cierre-candidata.md) documenta carga desde cero, pruebas, auditoría, medición y ensayo parcial de interfaz. Sus límites y pendientes se registran allí; el documento y el índice se añadieron después de ejecutar las pruebas y no constituyen una publicación.

## Cómo leer las evidencias

Cada fila identifica una ejecución distinta. No se suman pruebas de ejecuciones diferentes; los registros históricos se conservan para poder contrastar versión, entorno y resultados.

| Versión o momento | Entorno | Comprobación y resultado | Fuente |
| --- | --- | --- | --- |
| Árbol de código de `46ff5d7` | `soundgraph-bench`, aislado | 66 unitarias y 6 de integración; cardinalidad del grafo y 200 lecturas HTTP medidas. Las 9 HTTP se registraron por separado en la auditoría local de ese día. | [Registro del 22 de noviembre](evidence/2026-11-22-verificacion-entrega.md). |
| `917a122` con scripts separados, antes del ajuste H07 | Copia local con volúmenes nuevos | 72 unitarias/de integración; 8 de 9 HTTP en cada uno de dos intentos. H07 observó recuperación posterior, pero falló la comprobación inmediata. | La espera insuficiente se corrigió después; esta ejecución no se presenta como aprobada. |
| Ajuste H07 y carga separada, previo a publicación | Proyecto Compose temporal, motores reales | 72 unitarias/de integración, 9 HTTP y segunda ejecución individual de H07 aprobadas; auditoría sin incidencias. El proyecto Compose de la suite se dirigió al entorno temporal, conservando sus aserciones. | [Suite HTTP](../tests/http/test_api.py) y [pruebas de integración](../tests/integration/). |
| Interfaz con ajuste de orden, previa a publicación | Chrome y proyecto aislado | Una segunda pestaña cambió las pistas; se rechazó el orden anterior y «Recargar playlist» mostró la lista actual. A 390 × 844 CSS px se comprobaron los modales de eliminación y notas sin desbordamiento horizontal; Escape devolvió el foco. | Registro de ejecución de interfaz; no sustituye una prueba en teléfono físico. |
| `71fa543` publicado | Clon público sin credenciales de GitHub, volúmenes nuevos | 72 unitarias/de integración, auditoría de referencias, disponibilidad y OpenAPI activo idéntico al contrato versionado. Las 9 HTTP no se repitieron dentro de este clon. | [Repositorio](https://github.com/ArturoYJ/soundgraph/tree/71fa543) y [contrato](api/openapi.json). |
| Árbol local posterior a `71fa543` | Proyecto Docker aislado con volúmenes nuevos | Carga interrumpida y reintentada; se reprodujo y corrigió la nota de solo espacios. 75 unitarias/de integración, 9 HTTP y auditoría aprobadas. | [Pruebas de consistencia y recuperación](evidence/2026-11-22-cierre-consistencia.md). |
| Candidato `fb24f00` | Proyecto Docker aislado `soundgraph-eval-20261128`, volúmenes nuevos | 600/600 escenarios de grafo, 24/24 API y 900/900 lecturas secuenciales de escala coincidieron con sus oráculos. Los p95 actuales y su método no son los del cartel anterior. | [Evaluación ampliada actual](evidence/2026-11-27-fb24f-evaluacion-ampliada.md). |

Las [evidencias de H1](evidence/2026-11-21-h1-frontend.md) y [H2](evidence/2026-11-21-h2-frontend.md) registran recorridos de navegador anteriores. La [medición inicial](evidence/2026-11-21-rendimiento.md) pertenece a otra ejecución y sus cifras no deben mezclarse con las del 22. Para evaluar una revisión posterior, comprueba qué código cambió y repite las pruebas correspondientes.
