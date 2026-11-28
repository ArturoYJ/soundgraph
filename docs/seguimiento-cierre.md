# SoundGraph — Estado de cierre

El [índice de entregables](entregables.md) reúne los artefactos que acompañan a la aplicación en `main`. Esta página distingue lo que se verificó técnicamente, sus límites y lo que corresponde a la entrega académica. Un resultado verificado no implica una calificación ni certifica aceptación docente.

## Verificación técnica

| Aspecto | Resultado | Evidencia |
| --- | --- | --- |
| Carga limpia, auditoría y contrato | Se iniciaron las tres bases con volúmenes nuevos, se cargó la semilla y la auditoría no detectó referencias huérfanas. La API respondió 200 en disponibilidad y el OpenAPI servido coincidió con el versionado. | [Arranque desde una copia limpia](evidence/2026-11-28-repro-main-clean.log) |
| Suites y contrato de operaciones | 70 pruebas unitarias, 21 de integración y 11 HTTP aprobadas. Las 18 operaciones en 12 rutas tienen evidencia o límites declarados; no se afirma cobertura exhaustiva. | [Registro de pruebas](evidence/2026-11-28-repro-main-clean.log) · [Catálogo y auditoría](catalogo-operaciones.md) |
| Validador y recuperación | Validador MongoDB activo y coincidente con el archivo. Se verificaron la reconciliación de un perfil tras caída de Neo4j y el reintento de una carga interrumpida con MongoDB detenido. | [Validación aislada](evidence/2026-11-27-cierre-candidata.md) · [Registro del validador](evidence/2026-11-27-cierre-validador.log) · [Reintento de carga](evidence/2026-11-27-carga-interrumpida.log) |
| Recorridos web | En escritorio se observaron recomendación, ficha, guardado, edición editorial, acceso personal válido e inválido y gestión de playlists, incluida su eliminación. | [Registros de navegación y alcance](entregables.md#cómo-leer-las-evidencias) |
| Evaluación y mediciones | La evaluación ampliada comprobó 600 escenarios de grafo y 24 de API, y midió 900 solicitudes secuenciales. Una ejecución aparte midió 100 solicitudes por ruta en recomendaciones y playlists. | [Evaluación ampliada](evidence/2026-11-27-fb24f-evaluacion-ampliada.md) · [Medición corta](evidence/2026-11-27-cierre-candidata.md#medición-http) |

No se cubrió la revisión móvil. La recuperación descrita no equivale a atomicidad entre motores; las mediciones no evalúan concurrencia, satisfacción musical ni capacidad de producción. Si cambia el código o la configuración, se deben repetir las comprobaciones afectadas. Los [antecedentes](evidence/anteriores.md) conservan los resultados de sus propias ejecuciones.

## Entrega académica

- **Repositorio técnico:** se mantiene en `main`, con los artefactos y enlaces del [índice de entregables](entregables.md).
- **Informe integral:** preparado con el enlace a GitHub. Se comparte por separado; este repositorio no contiene el PDF ni acredita su envío o recepción.
- **Cartel:** entregado por separado según confirmó el equipo. No forma parte del informe ni de esta entrega técnica.
- **Demostración:** hay [guion y preparación de datos](demostracion.md) y constan ensayos locales. Antes de exponer, conviene repetir el recorrido principal en el equipo que se usará. Los registros no acreditan una presentación ante el docente.
