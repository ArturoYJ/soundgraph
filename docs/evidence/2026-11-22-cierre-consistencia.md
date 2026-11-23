# SoundGraph — Pruebas de consistencia y recuperación

**Fecha:** 22 de noviembre de 2026. **Versión:** árbol de trabajo local basado en `71fa543`, con la validación documental y pruebas nuevas aún sin commit. **Entorno:** proyecto Docker aislado `soundgraph-audit-20261122`, con volúmenes creados para este ensayo; PostgreSQL 17.12, MongoDB 8.0.38 y Neo4j 5.26.33 Community. El entorno de desarrollo no participó en las mutaciones.

## Interrupción de la carga

Se detuvo MongoDB en el proyecto aislado. Para provocar el fallo después de escribir en PostgreSQL, se invocó `seed()` directamente con conexiones construidas sin la comprobación previa de `open_stores()`. Esta preparación es importante: la entrada normal del cargador comprueba la conectividad de los motores antes de empezar a escribir.

La escritura SQL se completó y la carga falló al acceder a MongoDB con `ServerSelectionTimeoutError`. En ese momento se observaron **4 perfiles y 1 playlist** en PostgreSQL y **0 nodos** en Neo4j. Se arrancó MongoDB y se ejecutó el cargador normal. La carga finalizó y `python -m scripts.check_references` informó «Referencias entre motores: sin incidencias».

La [prueba de integración existente](../../tests/integration/test_seed.py) comprueba por separado que volver a cargar conserva modificaciones de prueba y no duplica los registros. No se afirma atomicidad entre motores.

## Nota documental con espacios

Antes de la corrección, una actualización directa en MongoDB con `text` y `source` compuestos solo de espacios fue aceptada. La solicitud HTTP de recomendaciones devolvió **500** al leer la ficha incompatible con el modelo de la API. El documento se restauró en el entorno aislado.

Se agregó al validador de MongoDB la exigencia de al menos un carácter que no sea espacio en blanco para cada uno de esos campos. Las nuevas pruebas insertan una nota válida y verifican por separado que se rechacen texto y fuente de solo espacios. La modificación del validador evita nuevas escrituras incompatibles; no corrige documentos históricos automáticamente.

## Regresión posterior

| Comprobación | Resultado |
| --- | --- |
| `pytest -p no:cacheprovider -q tests/unit tests/integration` con `SOUNDGRAPH_ISOLATED_TEST=1` | **75 aprobadas**, incluyendo las tres pruebas nuevas. |
| Suite HTTP | **9 aprobadas**. El ejecutor temporal dirigió `ORIGIN` a `127.0.0.1:18084` y `SQL_COMPOSE` al proyecto aislado; verificó el enlace de puertos antes de iniciar. |
| Auditoría de referencias | Sin incidencias tras volver a cargar. |
| `/openapi.json` | Coincide con `docs/api/openapi.json`. |
| Diagramas Mermaid | Los cinco diagramas de arquitectura y modelado se renderizaron con Mermaid CLI 12.2.0 y se revisaron visualmente en imágenes PNG; no se publicaron las imágenes temporales. |

La suite HTTP se ejecutó con el runner adaptado al entorno aislado; no se afirma que esos 9 casos se hayan ejecutado desde el clon público de `71fa543`. La prueba de fallo no equivale a demostrar que toda interrupción posible es recuperable.
