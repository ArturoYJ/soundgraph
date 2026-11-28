# SoundGraph — Evidencia histórica y documentos de trabajo

Estos materiales documentan decisiones y ejecuciones anteriores. No se necesitan para instalar la aplicación. Para evaluar lo que se verificó al cierre, usa el [índice de entregables](../entregables.md#cómo-leer-las-evidencias). Los registros no se movieron ni se borraron para conservar sus rutas y referencias.

## Desarrollo y verificación inicial

- [Diseño del MVP](../superpowers/specs/2026-11-21-soundgraph-mvp-design.md), [plan de implementación](../superpowers/plans/2026-11-21-soundgraph-mvp-implementation.md) y [diseño del cierre de validación](../superpowers/specs/2026-11-22-soundgraph-cierre-validacion.md).
- [Carga inicial](2026-11-21-h0-data-seed.md), [primer contrato y casos HTTP](2026-11-21-h1-rest-api.md), [recorrido inicial en navegador](2026-11-21-h1-frontend.md) y [gestión de playlists y notas](2026-11-21-h2-frontend.md).
- [Medición HTTP inicial](2026-11-21-rendimiento.md), [verificación posterior](2026-11-22-verificacion-entrega.md), [consistencia y recuperación](2026-11-22-cierre-consistencia.md) y [cambios de perfiles, interfaz y recuperación de Neo4j](2026-11-23-perfiles-recuperacion-ui.md).

## Evaluaciones y publicaciones previas

- [Evaluación ampliada anterior](2026-11-26-evaluacion-ampliada.md) y [registro de verificación de publicación](2026-11-26-verificacion-publicacion.md). No atribuir las cifras de latencia anteriores a la publicación posterior ni sumar sus resultados a las verificaciones de cierre.
- [Evaluación histórica para el cartel](2026-11-26-evaluacion-cartel.md) y [revisión de materiales de presentación](2026-11-27-material-adicional-poster.md), anterior a la entrega separada del cartel. El [ejecutor HTTP del cartel](../../tests/http/run_cartel_isolated.py) y el [medidor del cartel](../../scripts/measure_cartel.py) mantienen sus parámetros del entorno original. Para verificar la aplicación, sigue la [guía de la suite HTTP](../api/README.md#prueba-http-aislada) y el [método de la evaluación de cierre](2026-11-27-fb24f-evaluacion-ampliada.md).

## Archivos con resultados idénticos

Los siguientes grupos son idénticos byte a byte en el repositorio. Sus nombres, resúmenes y vínculos se conservan para consultar la procedencia documentada. **No se deben contar como casos adicionales por el número de archivos.**

| Grupo | Registros |
| --- | --- |
| Escenarios de API | [Evaluación inicial](2026-11-26-api-24.jsonl) · [publicación](2026-11-26-publicacion-api.jsonl) · [cierre](2026-11-27-fb24f-api-24.jsonl) |
| Escenarios de grafo | [Evaluación inicial](2026-11-26-grafos-600.jsonl) · [publicación](2026-11-26-publicacion-grafos.jsonl) · [cierre](2026-11-27-fb24f-grafos-600.jsonl) |
