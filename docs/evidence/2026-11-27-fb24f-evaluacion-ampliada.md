# Evaluación ampliada de la candidata fb24f00 — 27 de noviembre de 2026

## Revisión y entorno

Se volvió a ejecutar en código `fb24f0009da5718074d0675a3748d7db21488693`, sin diferencias de backend, base de datos, scripts de evaluación ni pruebas desde ese commit. Proyecto Compose desechable `soundgraph-eval-20261128`, puertos de motores no publicados y API en `127.0.0.1:18136`; volúmenes PostgreSQL/MongoDB/Neo4j nuevos, separados de `soundgraph-dev`, `soundgraph-test`, `soundgraph-cierre-20261127` y `soundgraph-repro-20261127`. macOS 26.7.4 arm64, Docker Engine 29.1.3, Compose 2.40.3, PostgreSQL 17.12, MongoDB 8.0.38 y Neo4j 5.26.33.

La creación/carga desde cero siguió el [README](../../README.md#arranque-local); la auditoría inicial y final de referencias terminaron sin incidencias. Las credenciales locales se montaron en solo lectura donde los scripts las requerían y nunca se emitieron en salida.

## Resultados ligados a esta revisión

| Evaluación | Resultado observado | Registro crudo |
| --- | --- | --- |
| Consulta de grafo frente a oráculo independiente | 600/600 casos correctos en seis categorías; 717 candidatas y ninguna ya escuchada. Datos sintéticos y transacciones revertidas. | [600 casos JSONL](2026-11-27-fb24f-grafos-600.jsonl), SHA-256 `b585adfae7218ccf952d4368255ce138b957216b8ebe5d4d71450d92b95b3de1`. |
| Escenarios API integrados | 24/24 correctos, incluidas 6 respuestas parciales por ficha ausente. Se restauró el historial semilla y se limpiaron nodos/documentos temporales. | [24 casos JSONL](2026-11-27-fb24f-api-24.jsonl), SHA-256 `d3cd20177c489eaaa51c3158a8da534eea3e0f6674caa569b140b1b60645e880`. |
| Escala HTTP de recomendaciones | 900/900 respuestas secuenciales coincidieron con el oráculo; 10 calentamientos y 3 rondas de 100 por escala. Sin concurrencia intencional. | [900 muestras JSONL](2026-11-27-fb24f-escala-900.jsonl), SHA-256 `062f7e5526d97204f3e5208bdffe14e13042430df1a211ad1a7ab4d7ec91d7a9`. |

| Perfiles | Canciones | Escuchas | p95 de cada ronda (ms) | Mediana de tres p95 (ms) | Rango de tres p95 (ms) |
|---:|---:|---:|---|---:|---:|
| 10 | 50 | 200 | 48,311; 32,952; 28,650 | 32,952 | 28,650–48,311 |
| 100 | 500 | 5.000 | 147,085; 139,903; 86,189 | 139,903 | 86,189–147,085 |
| 500 | 2.000 | 25.000 | 110,053; 121,063; 108,352 | 110,053 | 108,352–121,063 |

Los tamaños cambian perfiles, canciones y enlaces al mismo tiempo; los resultados no aíslan causalmente el volumen y no forman una tendencia monotónica. Son solicitudes secuenciales de un cliente local, no una prueba de concurrencia/capacidad productiva, SLA, pertinencia musical o satisfacción.

## Incidencia del primer intento y recuperación

El primer intento del evaluador API devolvió `403 invalid_origin`: el proyecto se había iniciado con `SOUNDGRAPH_API_PORT=18139`, mientras el script fija `Host` y `Origin` a `127.0.0.1:18136`. El guard de [`require_local_origin`](../../backend/main.py) compara esos encabezados con el puerto configurado. Se confirmó la causa en el código y en los logs del contenedor, se recreó solo el contenedor API con el puerto que espera el evaluador y se repitió: 24/24 correctos. No se modificó el guard ni se relajó la protección de origen. El proyecto siguió aislado y la auditoría final volvió a quedar limpia.

## Reproducción

Con `.env` y `.env.demo` locales ya creados por el README:

```sh
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-eval-20261128 up -d --build --wait postgres mongo neo4j
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-eval-20261128 build tools api
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-eval-20261128 run --rm --no-deps tools
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-eval-20261128 run --rm --no-deps tools python -m scripts.check_references
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-eval-20261128 up -d --no-deps --wait api
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-eval-20261128 run --rm --no-deps -e SOUNDGRAPH_ISOLATED_TEST=1 tools python -m scripts.evaluate_graph_volume > graphs.jsonl
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-eval-20261128 run --rm --no-deps -e SOUNDGRAPH_ISOLATED_TEST=1 -v "$PWD/.env.demo:/tmp/soundgraph-codes:ro" tools python -m scripts.evaluate_api_scenarios > api.jsonl
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-eval-20261128 run --rm --no-deps -e SOUNDGRAPH_ISOLATED_TEST=1 -v "$PWD/.env.demo:/tmp/soundgraph-codes:ro" tools python -m scripts.evaluate_scale_http > scale.jsonl
SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-eval-20261128 run --rm --no-deps tools python -m scripts.check_references
```

Los scripts API y escala crean y eliminan temporalmente datos sintéticos. Ejecutarlos únicamente en un proyecto Compose nuevo y aislado. Esta evaluación se añadió como evidencia posterior; no cambia el conteo unitario/integración ni las 11 pruebas HTTP de cierre.
