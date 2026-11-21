# SoundGraph — Índice de entregables

Los enlaces corresponden al integrador, no a la práctica histórica de grafos. El estado de cada evidencia se distingue entre código, ejecución y presentación.

| Entregable de la guía | Dónde revisarlo |
| --- | --- |
| 1. Propuesta | [Problema, objetivo, usuarios, alcance y casos de uso](propuesta.md). |
| 2. Modelado | [Diagrama conceptual, modelos implementados, diccionario y reglas](models/modelado-integrado.md). |
| 3. Arquitectura y selección tecnológica | [Diagrama, matriz tecnológica, decisión REST y consistencia](arquitectura.md). |
| 4. Implementación de las tres bases | [Esquemas y semilla](../database/), [cargador](../scripts/seed.py), [evidencia de carga e integridad](evidence/2026-11-21-h0-data-seed.md) y [consultas observadas por motor](catalogo-operaciones.md#consultas-representativas-por-motor). |
| 5. Catálogo de operaciones y consultas | [Operaciones, resultados esperados y pruebas observadas](catalogo-operaciones.md). |
| 6. Backend y API | [Rutas](../backend/main.py), [servicios](../backend/services/), [repositorios](../backend/repositories/) y [contrato](api/openapi.json). |
| 7. Aplicación e integración | [Frontend](../frontend/) y [evidencia de recomendación, ficha, guardado y recarga](evidence/2026-11-21-h1-frontend.md). La gestión avanzada existe en la API; no se acredita como interfaz funcional. |
| 8. Pruebas, documentación y despliegue | [Instrucciones de ejecución](../README.md#arranque-local), [configuración de ejemplo](../.env.example), [pruebas](../tests/), [medición de rendimiento](evidence/2026-11-21-rendimiento.md). Arranque local comprobado. Código y documentación en [ArturoYJ/soundgraph](https://github.com/ArturoYJ/soundgraph). |

El **cartel final y el QR** se entregan por separado. El QR debe apuntar al repositorio y probarse antes de entregar el cartel. La evidencia del integrador está en texto, código y datos de prueba; las capturas se conservan fuera de la selección pública.

## Última verificación local: 21 de noviembre de 2026

- En `soundgraph-bench`: consultas representativas de los tres motores, 6 pruebas de persistencia e integración aprobadas y auditoría sin referencias huérfanas.
- En `soundgraph-test`: 8 pruebas HTTP aprobadas y auditoría sin referencias huérfanas tras probar consistencia y recuperación. No se volvió a ejecutar el recorrido JS en un navegador en esta verificación; su evidencia previa está en el punto 7.
- La medición HTTP es una ejecución distinta de las suites; los tiempos de prueba no son latencia de la aplicación.
