# SoundGraph — evaluación ampliada de recomendaciones

Fecha: 26 de noviembre de 2026, hora de Ciudad de México. Código base local `b287571fcea82496d7c4b1676071aa0b8694b820` con los scripts nuevos sin commit. La rama local estaba cinco commits detrás de `origin/main`. Proyecto Docker aislado `soundgraph-cartel-20261126`, puerto 18136. No se modificaron los volúmenes de desarrollo.

## 600 configuraciones sintéticas de grafo

`scripts/evaluate_graph_volume.py` generó 600 casos reproducibles, semilla 20261126, distribuidos en seis categorías con 100 cada una: sin historial, sin vecino, sin candidatas, vecino único, varios vecinos y mixto. Los identificadores, límites y relaciones varían; esto no significa que los 600 grafos sean topológicamente distintos. El oráculo Python agrupa escuchas por perfil con conjuntos y cuenta candidatos por vecino; es independiente del Cypher de producción. Cada caso ejecutó la consulta Neo4j real en una transacción revertida y comparó canción, afinidad y orden con el resultado completo esperado. Resultado **600/600** casos correctos; entre las **717 candidatas mostradas** no hubo canciones ya escuchadas (0/717). Los casos contienen también resultados vacíos; son escenarios diseñados, no una muestra de usuarios reales.

Los 600 registros, datos, resultado esperado y observado están en `2026-11-26-grafos-600.jsonl`. Una segunda ejecución generó exactamente el mismo archivo SHA-256 `b585adfae7218ccf952d4368255ce138b957216b8ebe5d4d71450d92b95b3de1`. El oráculo coincidió con las respuestas escritas manualmente en 11/11 de los escenarios previos aplicables al perfil `me`; el de perfil inexistente se evalúa directamente en la suite manual. La repetición comprueba reproducibilidad en este entorno, no corrección universal.

## Escenarios integrados

`scripts/evaluate_api_scenarios.py` ejecutó **24/24** casos esperados mediante sesión y API real: grafo Neo4j, catálogo MongoDB y perfil de sesión en PostgreSQL. Incluye **6 casos con ficha ausente** y respuesta parcial. Los casos y respuestas están en `2026-11-26-api-24.jsonl`. La consulta de grafo de estos casos se comparó con el mismo oráculo independiente. En la copia aislada, se retiraron temporalmente las relaciones de Ana y se restauraron; los nodos y documentos sintéticos fueron eliminados. Los 24 no son pruebas completas de interfaz ni representan todas las fallas posibles.

## Comparación de escala HTTP

Se midió solo `GET /api/v1/recommendations?limit=10`, en tres conjuntos sintéticos con una distribución uniforme de relaciones seleccionadas sin repetición. Por escala: 10 calentamientos y tres rondas secuenciales de 100 solicitudes, sin concurrencia intencional; cada respuesta se comparó con el oráculo. **900/900** respuestas coincidieron. El generador fija una semilla diferente por tamaño. La semilla demo conserva tres perfiles adicionales, tres canciones y tres relaciones ajenas al perfil consultado durante el ensayo; las cifras de la tabla describen el conjunto sintético, que incluye a Ana. Una sola configuración por tamaño no permite generalizar el efecto del tamaño aislado de la forma del grafo.

| Perfiles | Canciones | Escuchas | p95 rondas (ms) | Mediana de los tres p95 (ms) |
|---:|---:|---:|---|---:|
| 10 | 50 | 200 | 23,215; 21,984; 18,707 | 21,984 |
| 100 | 500 | 5.000 | 111,163; 125,682; 176,153 | 125,682 |
| 500 | 2.000 | 25.000 | 104,928; 93,881; 183,145 | 104,928 |

El p95 de cada ronda es el valor ordenado número 95 de 100. La última columna es **la mediana de tres p95**, no el p95 de las 300 muestras combinadas. Los resultados no crecen de forma monótona; la variación entre rondas y las distintas estructuras de grafos impiden concluir una tendencia estable o atribuir una causa al tamaño. Las muestras y resúmenes están en `2026-11-26-escala-http.jsonl`.

La medición se realizó en Apple M1, 8 GiB, macOS 26.7.4, Docker Engine 29.1.3, Compose 2.40.3, PostgreSQL 17.12, MongoDB 8.0.38, Neo4j 5.26.33. El cliente Python corrió en un contenedor del mismo proyecto; el cronómetro incluye solicitud HTTP, lectura y decodificación JSON de respuesta y no mide renderizado en navegador. No se controló la carga de fondo. Estos tiempos no son directamente comparables con los de `2026-11-26-evaluacion-cartel.md`, que usaban otro cliente y método de cronometraje. No miden concurrencia, capacidad de producción, calidad musical ni satisfacción.

## Repetición

Con los servicios y semilla del proyecto aislado activos y los scripts incorporados a la imagen, ejecutar `SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-cartel-20261126 run --rm --no-deps -e SOUNDGRAPH_ISOLATED_TEST=1 tools python -m scripts.evaluate_graph_volume`. Los scripts de API y escala requieren montar `.env.demo` como `/tmp/soundgraph-codes` de solo lectura y deben ejecutarse únicamente en este proyecto aislado. No imprimen códigos. Las mediciones variarán entre ejecuciones.
9372fcbf2fc7adb4f1a245e3560e3b45b392ff45aec85aee9b21e53b790687d0  scripts/evaluate_graph_volume.py
4dbc97dc31df99cebcfa8f56e6a844ce6165a455b952e0a666eb23b01dbb4652  scripts/evaluate_api_scenarios.py
11996e8d7c12b639750ab8a2a94dc23f8501f5af91f24f9f114de65102cc8e00  scripts/evaluate_scale_http.py

Comprobación posterior: `pytest -p no:cacheprovider -q tests/unit tests/integration` en el mismo proyecto aislado dio **87/87**; la auditoría `scripts.check_references` terminó sin incidencias. Son suites separadas de los 600 y 24 escenarios; no se suman las lecturas de rendimiento como casos funcionales independientes.

Los siguientes comandos son exclusivos del proyecto aislado ya preparado y reconstruido (`SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-cartel-20261126 build tools api`). Los scripts de API y escala modifican temporalmente el grafo y catálogo y deben ejecutarse solo allí, nunca en desarrollo:

```sh
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-cartel-20261126 run --rm --no-deps -e SOUNDGRAPH_ISOLATED_TEST=1 -v "$PWD/.env.demo:/tmp/soundgraph-codes:ro" tools python -m scripts.evaluate_api_scenarios
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-cartel-20261126 run --rm --no-deps -e SOUNDGRAPH_ISOLATED_TEST=1 -v "$PWD/.env.demo:/tmp/soundgraph-codes:ro" tools python -m scripts.evaluate_scale_http
```
