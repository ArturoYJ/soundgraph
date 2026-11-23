# SoundGraph — Diseño de cierre de validación

## Objetivo

Verificar los hallazgos prioritarios de la guía de proyecto y dejar evidencia trazable, sin añadir funcionalidades ni cambiar la arquitectura de SoundGraph.

## Alcance y conservación

- Conservar los cinco documentos de entrega ya modificados y la información de desarrollo.
- Mantener el cartel y el QR para una etapa posterior.
- Ejecutar ensayos de escritura y fallos exclusivamente en un proyecto Docker temporal, con nombre y volúmenes propios. Antes de iniciar, comprobar que no existen recursos con ese nombre. Al concluir, retirar solo los recursos creados por el ensayo.
- Mantener credenciales, capturas y carpetas internas fuera del repositorio público.

## Diagramas y documentación

Renderizar los diagramas Mermaid de arquitectura y modelos; revisar sintaxis, texto, relaciones, cardinalidades y legibilidad frente a los esquemas y al código. Corregir solo inconsistencias comprobadas. Revisar los enlaces y las anclas de la documentación modificada.

## Carga parcial y recuperación

En volúmenes nuevos, provocar una interrupción real después de una escritura en un motor y antes de completar la carga de los restantes. Comprobar la señal de error y documentar qué datos persistieron. Restablecer la dependencia, repetir el cargador y ejecutar la auditoría y las consultas de integridad. Comprobar que la repetición no duplica la semilla ni sobrescribe las ediciones cubiertas por la suite existente. Registrar comandos, resultados, versión y entorno; si falla la recuperación, no presentarla como satisfactoria.

## Validación documental

En una base aislada, verificar si MongoDB acepta una nota con texto o fuente compuestos solo por espacios y cómo responde la API al leerla. Si se confirma una inconsistencia que afecta el flujo, alinear la validación de almacenamiento con las reglas de la API y agregar pruebas negativas y positivas. Preservar el comportamiento de las notas válidas y no modificar los datos de desarrollo. Si el riesgo no se reproduce, registrar el resultado sin afirmar que existe un fallo.

## Evidencia y regresión

Revisar el catálogo por operación y distinguir los casos ejecutados de los previstos por el contrato. Añadir un registro final con la revisión o árbol probado, comandos, entorno y resultados observados, sin inventar ejecuciones anteriores. Repetir las suites unitarias, de integración y HTTP aplicables, la auditoría de referencias y la comprobación del contrato OpenAPI. Si hay fallos, registrar sus resultados y no sustituirlos por resultados históricos.

## Criterios de cierre

Los diagramas se muestran correctamente; las pruebas y su evidencia corresponden a los archivos evaluados; la recuperación de carga y la validación documental tienen resultados verificables; el catálogo diferencia pruebas reales de comportamientos previstos. La publicación y verificación desde un clon público se realizan después de revisar los cambios y únicamente con autorización de publicación; no se incluye el cartel ni el QR.
