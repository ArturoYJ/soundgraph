# SoundGraph — Verificación para entrega

**Fecha:** 22 de noviembre de 2026. La comprobación de cardinalidad, las pruebas unitarias y de integración y la medición se ejecutaron sobre el árbol de código reproducido sin cambios en la revisión `46ff5d7`, en el proyecto aislado `soundgraph-bench`. No se escribieron datos en el entorno de desarrollo.

## Evidencia por tipo de prueba

| Comprobación | Resultado registrado | Evidencia |
| --- | --- | --- |
| Pruebas unitarias | 66 aprobadas: sesiones, descubrimiento, validación de entradas y repositorio SQL. | [Suite unitaria](../../tests/unit/). |
| Integración de persistencia | 6 aprobadas: semilla, integridad SQL, validación documental y resultados de grafo; auditoría sin referencias huérfanas. | [Suite de integración](../../tests/integration/) y [evidencia de semilla](2026-11-21-h0-data-seed.md). La ejecución conjunta del 22 informó **72 aprobadas**. |
| HTTP | 9 aprobadas en la auditoría local del 22: salud, acceso, recomendaciones, playlists, edición, permisos y recuperación. | [Suite HTTP](../../tests/http/test_api.py) y [casos por operación](../catalogo-operaciones.md). |
| Interfaz | El registro del 21 demuestra guardado y recarga, gestionar playlists, reordenar y editar notas. | [Descubrimiento y guardado](2026-11-21-h1-frontend.md) y [gestión y edición](2026-11-21-h2-frontend.md). |

## Cardinalidad y dirección en Neo4j

**Regla:** cada relación `ESCUCHÓ` va de un nodo `Perfil` a un nodo `Cancion`, con una relación por par. La validación agrupa por par de nodos y detecta duplicados o extremos incorrectos. Se ejecutó contra la semilla y contra dos relaciones introducidas en una transacción de prueba (una repetida y otra inversa). Se revirtió esa transacción.

| Estado observado | Relaciones | Pares duplicados | Pares con extremos o dirección incorrectos |
| --- | ---: | ---: | ---: |
| Semilla antes de la prueba | 5 | 0 | 0 |
| Dentro de la transacción con datos inválidos | 7 | 1 | 1 |
| Después de revertir | 5 | 0 | 0 |

Para repetir, con las bases y la semilla de `soundgraph-bench` listas, ejecutar lo siguiente **solo en el proyecto aislado**:

```sh
SOUNDGRAPH_API_PORT=18081 docker compose -p soundgraph-bench run --rm --no-deps -T tools python - <<'PY'
from scripts.storage import create_graph_driver

query = """
MATCH (a)-[r:`ESCUCHÓ`]->(b)
WITH a, b, count(r) AS cantidad
RETURN coalesce(sum(cantidad), 0) AS relaciones,
       sum(CASE WHEN cantidad > 1 THEN 1 ELSE 0 END) AS pares_duplicados,
       sum(CASE WHEN a:Perfil AND b:Cancion THEN 0 ELSE 1 END) AS pares_invalidos
"""

with create_graph_driver() as driver, driver.session(database="neo4j") as session:
    original = session.run(query).single().data()
    assert original == {"relaciones": 5, "pares_duplicados": 0, "pares_invalidos": 0}, original
    with session.begin_transaction() as tx:
        tx.run("""
            MATCH (p:Perfil {profileId: $perfil})-[:`ESCUCHÓ`]->(c:Cancion {songId: $cancion})
            CREATE (p)-[:`ESCUCHÓ`]->(c), (c)-[:`ESCUCHÓ`]->(p)
        """, perfil="p-ana-main", cancion="c-soWhat").consume()
        artificial = tx.run(query).single().data()
        assert artificial == {"relaciones": 7, "pares_duplicados": 1, "pares_invalidos": 1}, artificial
        tx.rollback()
    restored = session.run(query).single().data()
    assert restored == original, restored

for step, result in (("Semilla", original), ("Transacción de prueba", artificial), ("Tras rollback", restored)):
    print(step, result)
PY
```

Esta prueba demuestra detección y restauración; la unicidad de los identificadores de nodo es una regla distinta, definida en el [esquema](../../database/neo4j/001_schema.cypher).

## Medición HTTP de la versión candidata

| Lectura | Muestras | Mínimo (ms) | Mediana (ms) | p95 (ms) | Máximo (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Recomendaciones | 100 | 11,823 | 14,981 | 37,346 | 52,833 |
| Listado de playlists | 100 | 6,858 | 8,920 | 19,765 | 35,661 |

**Resultado:** las 200 solicitudes medidas devolvieron HTTP `200` y el contenido esperado. [Muestras crudas](2026-11-22-rendimiento-muestras.csv).

**Condiciones:** Apple M1, 8 GiB de RAM, macOS 26.7.4; Docker Engine 29.1.3 y Compose 2.40.3-desktop.1; VM de Docker con 6 CPU y aproximadamente 5,30 GiB de RAM. Cliente Python 3.9.6. PostgreSQL 17.12, MongoDB 8.0.38 y Neo4j 5.26.33 Community. Semilla de 4 perfiles, 1 playlist sin pistas, 3 fichas y 5 relaciones. Se usó un cliente local autenticado y una solicitud a la vez, con 10 calentamientos descartados por ruta. El tiempo termina al leer el cuerpo HTTP; el p95 se obtiene con el rango `ceil(0.95 × n)`. Se midieron lecturas, no una prueba de carga.

Para repetir, usa el [procedimiento de arranque del entorno de medición](2026-11-21-rendimiento.md#reproducir) y [el script de medición](../../scripts/measure_demo.py). Usa un nombre de CSV nuevo. Las cifras del 21 de noviembre pertenecen a otra ejecución.
