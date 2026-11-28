# Seguimiento del cierre del proyecto integrador

Candidata de código: `fb24f0009da5718074d0675a3748d7db21488693`. Los documentos de cierre son cambios locales posteriores al commit. Estados: **aprobado**, **pendiente** o **histórico**; ningún caso histórico se presenta como una ejecución nueva.

| Actividad | Estado | Evidencia o siguiente acción | Responsable sugerido |
| --- | --- | --- | --- |
| Preservar archivos locales y comparar ejecutor HTTP | Aprobado | Respaldo fuera de la copia; el ejecutor remoto añade H09 y H10. | Equipo |
| Elegir candidata remota | Aprobado técnicamente | Base `fb24f00` verificada y publicada en el `main` remoto; confirmar con el equipo que sea la versión acordada para presentar. | Equipo |
| Construir y cargar las tres bases desde cero | Aprobado | [Registro de cierre](evidence/2026-11-27-cierre-candidata.md); volúmenes aislados. | Equipo técnico |
| Verificar validador documental | Aprobado | Configuración activa más pruebas de documentos válidos e inválidos. | Equipo técnico |
| Unitarias, integración, HTTP y contrato | Aprobado | 91, 11 y OpenAPI en el registro de cierre; suites separadas. | Equipo técnico |
| Auditoría de las 18 operaciones del catálogo | Aprobado con límites | Cada ruta tiene resultado/evidencia y sus límites explícitos; H11 agregó observación de casos borde. UI-03 cubre gestión visual de playlists. No se afirma exhaustividad de todas las entradas, límites y carreras. | Equipo técnico |
| Fallo y reconciliación de perfil | Aprobado | H10 con caída de Neo4j en entorno aislado. | Equipo técnico |
| Interrupción y recuperación de carga inicial | Aprobado con límites | Repetida en MongoDB caído; recuperada por reintento normal y auditoría limpia. | Equipo técnico |
| Recorrido web de Ana, Editorial y gestión de playlists | Aprobado con límites | Ensayos de escritorio: ficha/recomendación/guardar, perfil con código, nota editorial y creación/renombre/reordenamiento/retiro/recarga; [flujo principal](evidence/2026-11-27-demo-web.log), [gestión](evidence/2026-11-27-demo-management-web.log). No se confirmó la eliminación visual de playlist ni se cubren todos los errores/controles. | Equipo |
| Recuperar perfil personal por código desde la interfaz | Aprobado | Perfil de prueba creado, sesión cerrada y reingreso visual por «Mi código»; identidad confirmada en pantalla. Perfil desechable retirado de la base aislada. | Equipo |
| Revisión móvil y teléfono físico | Fuera del alcance actual | El usuario pidió enfocar el cierre en la aplicación web y omitir móvil. | Equipo |
| Medición de las rutas principales | Aprobado con límites | Medición aislada sobre la base `fb24f00`, con carga de fondo no controlada. | Equipo técnico |
| Actualizar índice, arquitectura y trazabilidad | En curso | Índice, catálogo, arquitectura, OpenAPI y evidencia referencian la base `fb24f00`; comprobar que cada operación marcada «no verificada» siga explícita y confirmar el paquete de entrega. | Equipo |
| Versión y publicación definitivas | En curso | `main` remoto verificado en `a52da16` con cambios de documentación/evidencia posteriores al código `fb24f00`; falta confirmación del equipo sobre versión de presentación y validar repo/QR final. | Equipo |
| Reproducibilidad desde README | Aprobado | Entorno Compose nuevo, volúmenes vacíos, carga y auditoría limpias, readiness ok y 91/91 unitarias/integración y 11/11 HTTP; registros de reproducibilidad. | Equipo técnico |
| Ensayo final de presentación | Aprobado con límites | En entorno limpio `soundgraph-repro-20261127` se recorrió en navegador Ana → recomendación → ficha → guardar «C.R.E.A.M.» → playlist con 1 pista; ver [registro](evidence/2026-11-27-demo-web.log). La edición editorial y el acceso por código constan en los ensayos del registro de cierre. Aún falta el ensayo con el equipo/docente en el entorno físico de presentación. | Equipo |
| Verificar otros materiales de curso | Parcial | La búsqueda local encontró guía y cartel PDF, no rúbrica/slides; confirmar si la plataforma del curso tiene requisitos adicionales y si el cartel integra la entrega. | Equipo |
