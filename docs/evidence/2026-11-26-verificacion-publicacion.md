# Verificación de publicación de la evaluación

La evaluación se integró sobre `origin/main` en el commit base `2d4af8047dfade31ee91da00d20b289fd612323c`, en el proyecto Docker aislado `soundgraph-publicacion-v2`. Se construyó la imagen con los nuevos scripts y se cargó la semilla; no se emplearon volúmenes de desarrollo.

- Unitarias y de integración: **91/91** (`2026-11-26-publicacion-pytest.log`), incluidos los 12 escenarios manuales de grafo.
- Generador reproducible: **600/600** configuraciones, 717 resultados devueltos y 0 canciones ya escuchadas entre estos resultados (`2026-11-26-publicacion-grafos.jsonl`).
- API, sesión, grafo y catálogo: **24/24** escenarios, de los cuales 6 con ficha ausente (`2026-11-26-publicacion-api.jsonl`).
- Suite HTTP de esta versión: **11/11**, incluida creación y recuperación de perfiles personales (`2026-11-26-publicacion-http.log`).
- La auditoría de referencias entre motores terminó sin incidencias.

Los registros de los 600 y 24 casos incluyen entradas y salidas para revisión. Son pruebas distintas, no una medición de precisión musical. Las cifras de rendimiento de `2026-11-26-evaluacion-ampliada.md` y del cartel pertenecen al commit anterior `b287571`; la latencia no se volvió a medir en la base `2d4af80` y no debe atribuirse a esta revisión. Las pruebas presentes no demuestran satisfacción ni rendimiento en producción.
