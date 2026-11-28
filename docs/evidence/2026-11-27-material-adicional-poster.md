# Requisitos adicionales de ETEIA para el cartel — 27 de noviembre de 2026

## Material consultado

Se revisó visualmente el PDF de dos páginas **Guía instructiva para la elaboración del póster**, del Encuentro de Tecnologías Emergentes e Innovación Aplicada (ETEIA), junto con el cartel PDF de SoundGraph disponible en Descargas. La guía del proyecto final sigue siendo el contrato para la aplicación y sus ocho entregables; el cartel es un producto de comunicación derivado, no sustituye código, modelos, scripts, pruebas ni documentación.

## Criterios extraídos de la guía del cartel

- El cartel comunica problema, decisiones de diseño/implementación, resultados demostrables y conclusiones respaldadas; no debe inventar resultados ni crear una versión alternativa del proyecto para el cartel.
- La estructura enumera: título específico; autores completos; afiliaciones; resumen; introducción; planteamiento del problema; justificación; metodología; resultados; conclusiones con límites/mejoras; referencias IEEE.
- Los resultados deben distinguir lo diseñado, implementado y validado. Mostrar responsabilidades y operaciones de las tres bases; dar contexto/procedimiento a pruebas y mediciones; declarar lo incompleto.
- Formato recomendado: A1 vertical, 60 × 90 cm, salvo instrucción distinta de la organización. El PDF final debe usar las dimensiones indicadas por la organización.
- Exposición oral de 5–7 minutos seguida de preguntas; añadir demostración breve cuando esté disponible.
- El QR puede apuntar al repositorio, demo o ficha digital; se debe comprobar que abre antes de entregar el cartel.

## Revisión del cartel disponible

- PDF de una página, 1700 × 2551 pt (≈ 59,97 × 89,99 cm), compatible con 60 × 90 cm vertical.
- Incluye título, autores, afiliación, resumen, contexto, justificación, metodología, resultados, conclusiones y referencias; muestra un QR de repositorio.
- El planteamiento está integrado en la introducción, pero no formula en un bloque explícito el usuario afectado, su necesidad concreta y las consecuencias del problema; reforzarlo si el cartel se revisa para entrega.
- El QR se decodificó como `https://github.com/ArturoYJ/soundgraph`; la URL respondió HTTP 200 el 27/11/2026. Repetir la comprobación si cambia la URL/QR y antes de imprimir o entregar.
- La guía pide referencias IEEE; en el cartel actual [4] y [5] aparecen pegadas en una misma línea y la referencia [9] «Evaluacion ampliada… Registros locales y muestras» no ofrece una ubicación bibliográfica reproducible. Corregir y revisar acentos/formato al preparar la siguiente versión.
- El cartel no identifica el hash del código que respalda sus resultados. Las 600/600 y 24/24 ahora se reprodujeron en el candidato `fb24f00` y sus registros están en `2026-11-27-fb24f-evaluacion-ampliada.md` y JSONL. Los p95 del cartel (21,98; 125,68; 104,93 ms) proceden de la evaluación anterior sobre `b287571`, no de la nueva corrida en `fb24f00`; no presentarlos como medición de la candidata final. Actualizar las cifras y la referencia [9] con los valores actuales o etiquetar expresamente la revisión histórica. No afirmar carga concurrente: ambas mediciones son secuenciales.
- No se editó el PDF del cartel ni se fijó la exposición. Antes de entrega, acordar con el equipo el cartel que se imprimirá y ensayar exposición, preguntas y demo breve.

## Documento consolidado local

También existe `Documentacion_Final_SoundGraph.pdf` en Descargas (44 páginas), que declara la revisión `fb24f00` y distingue explícitamente que las métricas del cartel se tomaron de `b287571` y no se habían repetido en la candidata. Esa nota es honesta, pero el PDF no incluye el cierre y la nueva evaluación documentados el 27/11, no está versionado en el repositorio y no se localizó un fuente editable con el mismo nombre. Si el profesor recibirá ese PDF como manual/informe, regenerarlo desde los documentos vigentes o añadir un anexo con las nuevas pruebas; no sustituirlo automáticamente sin conservar el original.

## Addendum — cartel editable encontrado en Drive (28 de noviembre de 2026)

Se revisó en modo lectura la presentación nativa de Google Slides **SoundGraph_Cartel_ETEIA_2026_revision_docente_final**, modificada el 27/11/2026, identificador `1zQ-ADW7ekM-kZ5X_vt-VBdHm_9kzEzIsDbVL_uMI8TI`. Su tamaño es 60 × 90 cm vertical (21599525 × 32399275 EMU). Es una versión posterior/importante a cotejar, pero el título «revision_docente_final» y su fecha no prueban por sí solos aprobación del profesor.

El deck conserva **84/84 (100 %)**, atribuido a 75 unitarias/integración y 9 HTTP de revisiones anteriores. La fuente enlazada es `2d4af80`, y una nota del cartel precisa que el recuento corresponde a `46ff5d7`; por tanto no es la métrica de la candidata `fb24f00`. En esta candidata la evidencia posterior registra 91/91 unitarias e integración y 11/11 HTTP, en suites separadas (102 aprobaciones sumadas, sin contar los 600 escenarios de grafo, 24 escenarios API adicionales o las 900 lecturas secuenciales como pruebas unitarias). Antes de entregar, actualizar resumen, resultado y referencias del cartel con la evidencia vigente o identificar con claridad la ronda histórica.

Se consultaron los comentarios de la presentación (no hay hilos) y su historial de revisiones disponible (solo una revisión; modificada el 27/11/2026 por la cuenta propietaria). Por ello, «revision_docente_final» es solo parte del nombre del archivo: no hay comentario, autoría de tercero ni revisión previa que pruebe una aprobación del profesor. El usuario decidió dejar este archivo intacto hasta confirmar con el equipo que se entregará.

La referencia [9] del deck es «Pruebas de consistencia y recuperación» y apunta al registro de 22/11 bajo `2d4af80`, pero el texto del cartel atribuye el total 84 a `46ff5d7`; esa trazabilidad debe unificarse. Las referencias internas [7] y [8] también enlazan a evidencias antiguas. Los valores de p95 de la versión PDF revisada anteriormente siguen siendo históricos, no los de `fb24f00`. No se editaron el archivo de Drive ni el PDF. La vista de Drive no establece si esta presentación es la versión que el equipo entregará ni si fue aprobada; confirmar con el equipo/docente.

## Límite de la búsqueda externa

La búsqueda local encontró la guía del proyecto final, esta guía del cartel, el cartel y un PDF de documentación final de SoundGraph. La búsqueda de Drive encontró el deck editable descrito arriba, pero no una rúbrica adicional ni las instrucciones de plataforma. No se pudo verificar el contenido de la plataforma del curso ni una instrucción directa del profesor; confirmar allí fecha, mecanismo de entrega, dimensiones de impresión y si el cartel/demostración son obligatorios para este grupo.
