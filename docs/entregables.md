# SoundGraph — Índice de entregables

Esta página reúne los ocho entregables del proyecto y prioriza las evidencias de cierre. Para repetir la instalación o probar el flujo, empieza por el [arranque local](../README.md#arranque-local) y el [guion de demostración](demostracion.md).

| Entregable de la guía | Artefactos y comprobaciones |
| --- | --- |
| 1. Propuesta | [Problema, usuarios, casos de uso y alcance](propuesta.md). |
| 2. Modelado | [Modelo conceptual, diccionario y reglas entre motores](models/modelado-integrado.md). |
| 3. Arquitectura y selección tecnológica | [Diagrama, flujo, justificación del stack y manejo de fallos parciales](arquitectura.md). |
| 4. Implementación de las tres bases | [Esquemas, validadores y semilla](../database/), [cargador](../scripts/seed.py), [consultas representativas](catalogo-operaciones.md#consultas-representativas-por-motor), [carga limpia](evidence/2026-11-28-repro-main-clean.log) y [reintento tras una interrupción](evidence/2026-11-27-carga-interrumpida.log). |
| 5. Catálogo de operaciones y consultas | [18 operaciones en 12 rutas, resultados y casos no verificados](catalogo-operaciones.md). |
| 6. Backend y API | [Rutas](../backend/main.py), [servicios](../backend/services/), [repositorios](../backend/repositories/), [guía de API](api/README.md) y [contrato OpenAPI](api/openapi.json). |
| 7. Aplicación e integración | [Interfaz](../frontend/), [guion](demostracion.md), [recorrido principal y acceso personal](evidence/2026-11-27-cierre-candidata.md), [gestión de playlists](evidence/2026-11-27-demo-management-web.log), [eliminación web](evidence/2026-11-28-demo-delete-web.log) y [rechazo de código personal inválido](evidence/2026-11-28-web-invalid-personal-code.log). |
| 8. Pruebas, documentación y despliegue | [Instalación](../README.md#arranque-local), [configuración de ejemplo](../.env.example), [unitarias](../tests/unit/), [integración](../tests/integration/), [suite HTTP](../tests/http/test_api.py), [reproducción limpia](evidence/2026-11-28-repro-main-clean.log) y [evaluación ampliada](evidence/2026-11-27-fb24f-evaluacion-ampliada.md). El despliegue documentado es local. |

## Cómo leer las evidencias

| Registro de cierre | Qué respalda | Límite |
| --- | --- | --- |
| [Reproducción desde GitHub](evidence/2026-11-28-repro-main-clean.log) | Carga y arranque con volúmenes nuevos, auditoría, igualdad de OpenAPI y suites de **70 unitarias, 21 de integración y 11 HTTP**. | Se reutilizó caché de imágenes, no volúmenes; el ejecutor HTTP se adaptó temporalmente al nombre y puerto del proyecto aislado. |
| [Validación aislada](evidence/2026-11-27-cierre-candidata.md) y [carga interrumpida](evidence/2026-11-27-carga-interrumpida.log) | Validador, recuperación de perfiles y reintento del cargador ante una caída de MongoDB. | Comprueba los escenarios descritos, no atomicidad entre motores. |
| [Demo web principal](evidence/2026-11-27-demo-web.log), [gestión](evidence/2026-11-27-demo-management-web.log), [eliminación](evidence/2026-11-28-demo-delete-web.log) y [código inválido](evidence/2026-11-28-web-invalid-personal-code.log) | Lo observado en la interfaz de escritorio. | Los recorridos no cubren todos los controles o combinaciones de error; la prueba de acceso personal válido consta en el registro de validación aislada. |
| [Evaluación ampliada](evidence/2026-11-27-fb24f-evaluacion-ampliada.md) | **600 escenarios de grafo**, **24 de API** y **900 solicitudes medidas**; incluye método, muestras y p95. | Casos sintéticos y mediciones secuenciales, no una prueba de uso concurrente ni de calidad musical. |
| [Catálogo](catalogo-operaciones.md) y [sondeo H11](evidence/2026-11-27-catalog-edge-probes.log) | Qué se observó para cada operación y qué casos siguen como previstos. | El sondeo H11 no se cuenta entre las 11 pruebas automatizadas de HTTP. |

Cada registro conserva el código y el entorno con los que se obtuvo. No se suman casos de ejecuciones distintas. Consulta el [estado de cierre](seguimiento-cierre.md) para los límites y la preparación de la entrega, o el [índice de antecedentes](evidence/anteriores.md) para las ejecuciones previas. El informe integral y el cartel son documentos de entrega por separado; no se incluyen en este repositorio.
