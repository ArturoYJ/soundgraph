# Seguimiento del cierre del proyecto integrador

Candidata de código: `fb24f0009da5718074d0675a3748d7db21488693`. Los documentos de cierre son cambios locales posteriores al commit. Estados: **aprobado**, **pendiente** o **histórico**; ningún caso histórico se presenta como una ejecución nueva.

| Actividad | Estado | Evidencia o siguiente acción | Responsable sugerido |
| --- | --- | --- | --- |
| Preservar archivos locales y comparar ejecutor HTTP | Aprobado | Respaldo fuera de la copia; el ejecutor remoto añade H09 y H10. | Equipo |
| Elegir candidata remota | Aprobado técnicamente | `origin/main` actualizado y base `fb24f00` aislada; confirmar con el equipo antes de publicar. | Equipo |
| Construir y cargar las tres bases desde cero | Aprobado | [Registro de cierre](evidence/2026-11-27-cierre-candidata.md); volúmenes aislados. | Equipo técnico |
| Verificar validador documental | Aprobado | Configuración activa más pruebas de documentos válidos e inválidos. | Equipo técnico |
| Unitarias, integración, HTTP y contrato | Aprobado | 91, 11 y OpenAPI en el registro de cierre; suites separadas. | Equipo técnico |
| Fallo y reconciliación de perfil | Aprobado | H10 con caída de Neo4j en entorno aislado. | Equipo técnico |
| Interrupción y recuperación de carga inicial | Aprobado con límites | Repetida en MongoDB caído; recuperada por reintento normal y auditoría limpia. | Equipo técnico |
| Recorrido de Ana y edición editorial | Aprobado con límites | Ensayo de navegador de escritorio, incluyendo recarga; detalle y exclusiones en registro. | Equipo |
| Recuperar perfil personal por código desde la interfaz | Aprobado | Perfil de prueba creado, sesión cerrada y reingreso visual por «Mi código»; identidad confirmada en pantalla. Perfil desechable retirado de la base aislada. | Equipo |
| Revisión móvil y teléfono físico | Fuera del alcance actual | El usuario pidió enfocar el cierre en la aplicación web y omitir móvil. | Equipo |
| Medición de las rutas principales | Aprobado con límites | Medición aislada sobre la base `fb24f00`, con carga de fondo no controlada. | Equipo técnico |
| Actualizar índice, arquitectura y trazabilidad | En curso | Revisar casos del catálogo marcados previstos y confirmar el paquete tras el commit definitivo. | Equipo |
| Versión y publicación definitivas | En curso | Evidencia/documentación publicada hasta `c4c2500`; falta confirmar la versión de presentación y validar repo/QR final. | Equipo |
| Reproducibilidad desde README | Aprobado | Entorno Compose nuevo, volúmenes vacíos, carga y auditoría limpias, readiness ok y 91/91 unitarias/integración y 11/11 HTTP; registros de reproducibilidad. | Equipo técnico |
| Ensayo final de presentación | Pendiente | Ensayar con datos preparados, permisos, disponibilidad y documentación de la versión definitiva. | Equipo |
| Verificar otros materiales de curso | Parcial | La búsqueda local encontró guía y cartel PDF, no rúbrica/slides; confirmar si la plataforma del curso tiene requisitos adicionales y si el cartel integra la entrega. | Equipo |
