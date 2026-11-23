# SoundGraph — Índice de entregables

Este es el índice vigente del integrador. Cada entregable enlaza su artefacto y, cuando corresponde, la evidencia de ejecución. El plan y el diseño del MVP se conservan como antecedentes de trabajo.

| Entregable de la guía | Dónde revisarlo |
| --- | --- |
| 1. Propuesta | [Problema, objetivo, usuarios, alcance y casos de uso](propuesta.md). |
| 2. Modelado | [Diagrama conceptual, modelos implementados, diccionario y reglas](models/modelado-integrado.md). |
| 3. Arquitectura y selección tecnológica | [Diagrama, matriz tecnológica, decisión REST y consistencia](arquitectura.md). |
| 4. Implementación de las tres bases | [Esquemas y semilla](../database/), [scripts SQL de carga](../database/postgres/seed/), [scripts Cypher de carga](../database/neo4j/seed/), [cargador](../scripts/seed.py), [evidencia de carga e integridad](evidence/2026-11-21-h0-data-seed.md), [consultas observadas por motor](catalogo-operaciones.md#consultas-representativas-por-motor) y [prueba de cardinalidad del grafo](evidence/2026-11-22-verificacion-entrega.md#cardinalidad-y-dirección-en-neo4j). |
| 5. Catálogo de operaciones y consultas | [16 operaciones de la API, entradas, resultados esperados y pruebas observadas](catalogo-operaciones.md). |
| 6. Backend y API | [Rutas](../backend/main.py), [servicios](../backend/services/), [repositorios](../backend/repositories/) y [contrato](api/openapi.json). |
| 7. Aplicación e integración | [Frontend](../frontend/), [recorrido de evaluación](demostracion.md), [evidencia de recomendación, ficha, guardado y recarga](evidence/2026-11-21-h1-frontend.md) y [evidencia de gestión de playlists y editor de notas](evidence/2026-11-21-h2-frontend.md). |
| 8. Pruebas, documentación y despliegue | [Instrucciones de ejecución](../README.md#arranque-local), [configuración de ejemplo](../.env.example), [pruebas unitarias](../tests/unit/), [integración](../tests/integration/), [pruebas HTTP](../tests/http/) y [validación de entrega y medición HTTP](evidence/2026-11-22-verificacion-entrega.md). Repositorio: [ArturoYJ/soundgraph](https://github.com/ArturoYJ/soundgraph). |

El **cartel final y el QR** se entregan por separado. El QR debe apuntar al repositorio y probarse antes de entregar el cartel. La evidencia del integrador está en texto, código y datos de prueba; las capturas se conservan fuera de la selección pública.

## Cómo leer las evidencias

- El [registro del 22 de noviembre](evidence/2026-11-22-verificacion-entrega.md) reúne resultados de la versión candidata local: 66 pruebas unitarias, 9 HTTP y 6 de integración, la comprobación de relaciones de escucha y la medición HTTP.
- **Reverificación de los scripts separados:** en una copia de la revisión `917a122` con este ajuste, Docker creó volúmenes nuevos y el cargador ejecutó el SQL y el Cypher desde sus archivos. Pasaron 66 pruebas unitarias y 6 de integración, incluida la recarga sin duplicados ni pérdida de cambios. La auditoría no encontró referencias huérfanas; el OpenAPI activo coincidió con el contrato versionado de 16 operaciones. De 9 pruebas HTTP, pasaron 8 en ambos intentos: H07 confirmó `503` durante la caída de Neo4j, pero la comprobación inmediata tras el reinicio aún recibió `503` en la repetición observada. Una comprobación posterior devolvió `200` tanto en disponibilidad como en recomendaciones, sin recargar la semilla ni reiniciar la API.
- **Ajuste de recuperación H07:** en una ejecución posterior con volúmenes nuevos, la prueba esperó la disponibilidad de la API con un plazo de 60 segundos. Se aprobaron 72 pruebas unitarias y de integración, las 9 HTTP y una segunda ejecución individual de H07; la auditoría de referencias no encontró incidencias. Para aislar los datos se cambió el proyecto Compose de la suite al proyecto temporal de prueba, conservando sus mismas aserciones.
- **Conflicto de orden y pantalla estrecha:** en Chrome y un entorno aislado, una segunda pestaña quitó una pista mientras la primera conservaba abierto el orden anterior. La API rechazó el orden obsoleto; tras la corrección, «Recargar playlist» mostró la lista actualizada. A 390 × 844 CSS px se comprobaron el modal de eliminación y el editor de notas sin desbordamiento horizontal; Escape cerró ambos y devolvió el foco al botón correspondiente. No es una prueba en teléfono físico.
- Las evidencias del navegador documentan los recorridos ejecutados el 21 de noviembre. La [medición inicial](evidence/2026-11-21-rendimiento.md) se conserva como registro histórico; sus cifras no deben mezclarse con las del 22.
- Para evaluar una versión descargada de GitHub, comprueba que el commit y la evidencia que vas a citar correspondan a esa versión. El cartel debe referirse a las mismas funcionalidades y resultados que la demo.
