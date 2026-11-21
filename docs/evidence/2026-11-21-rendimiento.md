# SoundGraph — Evaluación básica de rendimiento HTTP

**Fecha:** 21 de noviembre de 2026. Medición local de dos lecturas del flujo principal; no es una prueba de carga.

| Operación | Muestras | Mínimo (ms) | Mediana (ms) | p95 (ms) | Máximo (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Recomendaciones · PostgreSQL, Neo4j y MongoDB | 100 | 11.241 | 12.403 | 17.029 | 24.332 |
| Listado de playlists · PostgreSQL | 100 | 6.814 | 8.223 | 12.951 | 19.529 |

Las **200 solicitudes medidas** devolvieron `200` y el resultado esperado: la recomendación `c-cream` con afinidad 1 y sin resultado parcial, y la lista `Para escuchar` con 0 pistas. Los [datos crudos](2026-11-21-rendimiento-muestras.csv) tienen una fila por solicitud, sin códigos de acceso ni cookies.

## Método y condiciones

- **Equipo:** Apple M1, 8 GiB de RAM, macOS 26.7.4. Máquina virtual de Docker con 6 CPU lógicas reportadas y aproximadamente 5.30 GiB de RAM. Docker Engine 29.1.3, Compose 2.40.3-desktop.1; cliente Python 3.9.6.
- **Backend y datos:** API contenida en Docker en `127.0.0.1:18081`; proyectos y volúmenes de medición separados de desarrollo. Versiones observadas: PostgreSQL 17.12, MongoDB 8.0.38, Neo4j 5.26.33 Community. Antes de medir se consultaron 4 perfiles, 1 playlist, 0 pistas, 0 sesiones, 3 fichas y 5 relaciones de escucha. La API de desarrollo se dejó activa en el mismo equipo, sin ser objetivo del cliente. No se controló la carga de fondo.
- **Cliente:** una sesión de Ana, un cliente HTTP/1.1 y una solicitud a la vez. Primero `GET /api/v1/recommendations?limit=10`, luego `GET /api/v1/playlists`. Por cada ruta, 10 solicitudes de calentamiento descartadas y 100 registradas. Se validaron también las respuestas de calentamiento.
- **Latencia:** tiempo desde inmediatamente antes de enviar la solicitud hasta terminar de leer el cuerpo, con `perf_counter_ns`. Incluye el viaje HTTP local y el trabajo del servidor; excluye el inicio y cierre de sesión, la decodificación JSON del cliente y todo el renderizado del navegador. El p95 usa el rango `ceil(0.95 × n)` en las muestras ordenadas.
- **Interpretación:** las cifras describen una ejecución local con una semilla mínima. No permiten inferir capacidad en producción, rendimiento bajo concurrencia, latencia percibida en navegador, ni ventajas de un motor sobre otro. Las rutas ejecutan trabajos distintos. No se midió escritura ni arranque en frío.

## Reproducir

Desde la raíz; usar la semilla del benchmark sin pistas guardadas. `scripts.init_env` preserva los archivos existentes. El script comprueba que el puerto pertenezca al proyecto aislado, valida cada respuesta y no imprime credenciales.

```sh
python3 -m scripts.init_env
export SOUNDGRAPH_API_PORT=18081
docker compose -p soundgraph-bench up -d --wait postgres mongo neo4j
docker compose -p soundgraph-bench build tools api
docker compose -p soundgraph-bench run --rm --no-deps tools
docker compose -p soundgraph-bench up -d --no-deps --wait api
python3 -m scripts.measure_demo --csv /tmp/soundgraph-rendimiento-nuevo.csv
docker compose -p soundgraph-bench down
unset SOUNDGRAPH_API_PORT
```

La API debe arrancar **después de la carga inicial** para que su comprobación de salud encuentre las tablas. Usa un nombre de salida nuevo para no sobrescribir mediciones anteriores. Conserva los volúmenes de desarrollo.
