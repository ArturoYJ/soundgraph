# SoundGraph — Índice de entregables

Este es el índice vigente del integrador. Cada entregable enlaza su artefacto y, cuando corresponde, la evidencia de ejecución. El plan y el diseño del MVP se conservan como antecedentes de trabajo.

| Entregable de la guía | Dónde revisarlo |
| --- | --- |
| 1. Propuesta | [Problema, objetivo, usuarios, alcance y casos de uso](propuesta.md). |
| 2. Modelado | [Diagrama conceptual, modelos implementados, diccionario y reglas](models/modelado-integrado.md). |
| 3. Arquitectura y selección tecnológica | [Diagrama, matriz tecnológica, decisión REST y consistencia](arquitectura.md). |
| 4. Implementación de las tres bases | [Esquemas y semilla](../database/), [cargador](../scripts/seed.py), [evidencia de carga e integridad](evidence/2026-11-21-h0-data-seed.md), [consultas observadas por motor](catalogo-operaciones.md#consultas-representativas-por-motor) y [prueba de cardinalidad del grafo](evidence/2026-11-22-verificacion-entrega.md#cardinalidad-y-dirección-en-neo4j). |
| 5. Catálogo de operaciones y consultas | [16 operaciones de la API, entradas, resultados esperados y pruebas observadas](catalogo-operaciones.md). |
| 6. Backend y API | [Rutas](../backend/main.py), [servicios](../backend/services/), [repositorios](../backend/repositories/) y [contrato](api/openapi.json). |
| 7. Aplicación e integración | [Frontend](../frontend/), [recorrido de evaluación](demostracion.md), [evidencia de recomendación, ficha, guardado y recarga](evidence/2026-11-21-h1-frontend.md) y [evidencia de gestión de playlists y editor de notas](evidence/2026-11-21-h2-frontend.md). |
| 8. Pruebas, documentación y despliegue | [Instrucciones de ejecución](../README.md#arranque-local), [configuración de ejemplo](../.env.example), [pruebas unitarias](../tests/unit/), [integración](../tests/integration/), [pruebas HTTP](../tests/http/) y [validación de entrega y medición HTTP](evidence/2026-11-22-verificacion-entrega.md). Repositorio: [ArturoYJ/soundgraph](https://github.com/ArturoYJ/soundgraph). |

El **cartel final y el QR** se entregan por separado. El QR debe apuntar al repositorio y probarse antes de entregar el cartel. La evidencia del integrador está en texto, código y datos de prueba; las capturas se conservan fuera de la selección pública.

## Cómo leer las evidencias

- El [registro del 22 de noviembre](evidence/2026-11-22-verificacion-entrega.md) reúne resultados de la versión candidata local: 66 pruebas unitarias, 9 HTTP y 6 de integración, la comprobación de relaciones de escucha y la medición HTTP.
- Las evidencias del navegador documentan los recorridos ejecutados el 21 de noviembre. La [medición inicial](evidence/2026-11-21-rendimiento.md) se conserva como registro histórico; sus cifras no deben mezclarse con las del 22.
- Para evaluar una versión descargada de GitHub, comprueba que el commit y la evidencia que vas a citar correspondan a esa versión. El cartel debe referirse a las mismas funcionalidades y resultados que la demo.
