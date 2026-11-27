# SoundGraph — evaluación para corregir el cartel

Fecha: 26 de noviembre de 2026 (hora de Ciudad de México). Código base local `b287571fcea82496d7c4b1676071aa0b8694b820`, con la nueva prueba `tests/integration/test_recommendation_scenarios.py` montada en el contenedor. Esta revisión local estaba cinco commits detrás de `origin/main`; las cifras no deben atribuirse sin nueva verificación a otra revisión.

## Corrección de reglas

Se ejecutaron 12 escenarios sintéticos independientes con salidas esperadas escritas de antemano: perfil inexistente, sin historial, sin vecino, sin candidatas, una candidata, dos escuchas compartidas con un solo vecino, dos vecinos, exclusión de pista escuchada, orden y desempate, límite, vecino sin coincidencia y múltiples candidatas. La consulta Cypher real se ejecutó en Neo4j con datos creados dentro de transacciones revertidas. Resultado **12/12**. Evalúa esos escenarios de la consulta de grafo, no la calidad musical ni el flujo completo de API en esos doce escenarios.

La ejecución conjunta de pruebas unitarias, de integración existentes y los 12 escenarios dio **87/87** (los 12 están incluidos, no se suman otra vez). Una ejecución separada dio **9/9** casos HTTP: en total **96/96 ejecuciones de prueba**. Incluyen unidades con dobles de prueba y casos integrados; no representan cobertura de código ni todas las situaciones posibles. Los registros completos están en `2026-11-26-cartel-pruebas.log` y `2026-11-26-cartel-pruebas-http.log`. El ejecutor HTTP adaptado al nombre y puerto del proyecto aislado está en `tests/http/run_cartel_isolated.py`.

## Medición HTTP

Mac Apple M1, 8 GiB RAM, macOS 26.7.4; Docker Engine 29.1.3, Compose 2.40.3, PostgreSQL 17.12, MongoDB 8.0.38, Neo4j 5.26.33. Entorno Compose `soundgraph-cartel-20261126`, puerto 127.0.0.1:18136, volúmenes propios, semilla mínima de 4 perfiles, 3 canciones y 5 relaciones. Un cliente autenticado local, una solicitud a la vez, 10 calentamientos descartados y 100 muestras por ruta. Cronómetro desde envío hasta lectura completa del cuerpo HTTP, excluye renderizado del navegador. p95 = valor en posición ceil(0,95 × n). No se controló la carga de fondo.

| Ruta | n | Mediana (ms) | p95 (ms) | Máximo (ms) | Respuestas esperadas |
|---|---:|---:|---:|---:|---:|
| Recomendaciones | 100 | 15,181 | 23,808 | 35,389 | 100/100 |
| Playlists | 100 | 8,040 | 15,979 | 39,528 | 100/100 |

Las muestras crudas están en `2026-11-26-cartel-rendimiento-muestras.csv`. La primera medición coincidió temporalmente con las pruebas y se descartó; la tabla corresponde a una segunda medición tras finalizar las pruebas. Son dos rutas con trabajos distintos y solicitudes repetidas sobre los mismos datos: no son 200 escenarios, prueba de carga, capacidad de producción ni comparación de motores. No se midió satisfacción, precisión musical ni experiencia de navegador.

## Repetición

Crear y cargar solo el proyecto aislado mediante Compose; ejecutar `SOUNDGRAPH_API_PORT=18136 docker compose -p soundgraph-cartel-20261126 run --rm --no-deps -e SOUNDGRAPH_ISOLATED_TEST=1 tools python -m pytest -p no:cacheprovider -v tests/unit tests/integration` tras reconstruir la imagen que incluye el nuevo test. Con la API aislada activa, ejecutar `SOUNDGRAPH_API_PORT=18136 python3 tests/http/run_cartel_isolated.py` para la suite HTTP; después, `python3 -m scripts.measure_cartel --csv /tmp/soundgraph-cartel-nuevo.csv` (archivo nuevo). Los resultados pueden variar. Nunca apuntar estas pruebas a datos de desarrollo.
