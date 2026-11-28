# Cierre de validación de la candidata — 27 de noviembre de 2026

## Versión y límites

Código de la aplicación y pruebas del commit base `fb24f0009da5718074d0675a3748d7db21488693`, copia aislada. Este documento y los cambios de documentación se añadieron después de la ejecución; no se ha creado un commit de entrega ni publicado esta copia. La referencia `origin/main` se actualizó antes de seleccionarlo. El repositorio de desarrollo se conservó sin actualizar y sus archivos no rastreados se respaldaron fuera de esta copia.

Entorno: macOS 26.7.4, Apple M1, 8 GiB RAM; Docker Engine 29.1.3; proyecto Compose aislado `soundgraph-cierre-20261127`, API en `127.0.0.1:18137` y volúmenes propios nuevos. PostgreSQL 17.12, MongoDB 8.0.38 y Neo4j 5.26.33 Community. La semilla tenía 4 perfiles, 1 playlist vacía, 3 fichas y 5 escuchas. No se usaron los volúmenes de desarrollo.

## Resultados

| Comprobación | Resultado y evidencia |
| --- | --- |
| Creación y carga desde cero | Tres servicios saludables; cargador completo y auditoría sin incidencias. Se utilizó el procedimiento del README con nombre de proyecto y puerto aislados. |
| Validador MongoDB | Coincide con `song_validator.json`, nivel `strict`, acción `error`: [registro](2026-11-27-cierre-validador.log). Las pruebas de integración incluyeron inserciones válidas e inválidas. |
| Unitarias e integración | [91 aprobadas](2026-11-27-cierre-pytest.log), incluidos casos de grafo y validación documental. |
| Formularios frontend | [2 aprobadas](2026-11-27-cierre-frontend.log), pruebas Node sin DOM. |
| API HTTP | [11 aprobadas](2026-11-27-cierre-http.log), incluidas concurrencia de playlist, fallo de Neo4j, alta de perfil con grafo caído y reconciliación. Se ejecutó una copia temporal del runner versionado cambiando exclusivamente nombre del proyecto y puerto; conservó la comprobación del enlace 127.0.0.1 y todas las aserciones. |
| OpenAPI | El JSON servido coincidió con `docs/api/openapi.json` mediante comparación estructural. |
| Referencias | [Auditoría sin incidencias](2026-11-27-cierre-auditoria.log), ejecutada tras las pruebas HTTP. |
| Navegador de escritorio | Se creó un perfil de prueba, se observó la ausencia esperada de recomendaciones, se creó una playlist y persistió al recargar. Como Ana se abrió C.R.E.A.M. con afinidad de un perfil, se consultó la ficha y se guardó en la playlist; la canción seguía visible al recargar. Como Editor se cambió una nota, se recargó, se verificó el cambio y se restauró el texto inicial. Esto fue en el entorno aislado; no sustituye toda la suite HTTP. |

La interrupción de carga inicial se repitió el 27 de noviembre en el mismo proyecto aislado. Se detuvo MongoDB y se invocó `seed()` directamente con PostgreSQL, MongoDB y Neo4j abiertos sin el preflight de conectividad. La escritura SQL ocurrió y la carga falló en MongoDB; se observaron 5 perfiles porque ya existía un perfil personal creado durante el ensayo web (no se asumió erróneamente que el total sería 4). Al recuperar MongoDB, el cargador normal finalizó y la auditoría quedó limpia; persistieron los 5 perfiles y no quedó ningún perfil personal con `graph_pending`. Véase [registro de interrupción y recuperación](2026-11-27-carga-interrumpida.log). Esto prueba reintento aditivo en este escenario, no atomicidad distribuida ni recuperación universal.

## Medición HTTP

Se midió la versión `fb24f00` con el cliente HTTP local de `scripts/measure_demo.py`, adaptando en memoria únicamente el nombre y puerto del proyecto. Hubo 10 calentamientos y 100 solicitudes medidas secuencialmente por ruta; el cronómetro incluye la respuesta HTTP completa, pero no el renderizado. La carga de fondo no se controló, por lo que son mediciones orientativas. Las [200 muestras](2026-11-27-cierre-rendimiento.csv) tienen HTTP 200 y respuestas esperadas.

| Ruta | n | Mediana ms | p95 ms | Máximo ms |
| --- | ---: | ---: | ---: | ---: |
| Recomendaciones | 100 | 12,695 | 16,303 | 26,686 |
| Playlists | 100 | 7,228 | 9,615 | 11,426 |

No son pruebas de carga, concurrencia, capacidad de producción, precisión musical ni satisfacción. No deben sumarse las muestras de rendimiento al conteo de pruebas funcionales.

## Pendientes para la entrega

- La verificación móvil se omite por decisión del usuario: el alcance actual está enfocado en el desarrollo web.
- Ensayar en el entorno de presentación y comprobar que la versión publicada es la acordada por el equipo; el push a `main` aún no se ha realizado.
- Si se añaden cambios de código o configuración, repetir las pruebas afectadas y vincular los resultados al commit definitivo.
- El recorrido visual no verificó el reingreso de un perfil personal con su código ni todos los controles de gestión; esos comportamientos se ejercitaron por HTTP, no como recorrido completo de interfaz.
