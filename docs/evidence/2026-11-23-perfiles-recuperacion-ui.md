# Perfiles personales, preparación de Neo4j e interfaz

Fecha local: 23 de noviembre de 2026. Cambios locales sobre `b287571`, sin commit. Windows y Docker Desktop; los reinicios y las altas temporales se ejecutaron exclusivamente en `soundgraph-test`, puerto 18080, con sus volúmenes existentes. No se ejecutaron benchmarks ni suites completas por rutina.

## Causa y corrección de H07

La primera reproducción sin límite de CPU aprobó, consistente con un fallo intermitente. Para reproducir el arranque lento de forma controlada, se limitó temporalmente Neo4j de pruebas a una CPU. H07 falló tras salud `200`; el registro de la primera recomendación capturó `Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration`. La consulta conserva el timeout de cuatro segundos. `RETURN 1` no había comprobado la preparación de la consulta real.

La salud ejecuta ahora esa misma consulta con Ana y límite 1. Mientras no puede completarla responde `503`; no fabrica recomendaciones vacías. H07 conserva exactamente su cuerpo anterior, comprobado mediante comparación AST contra HEAD. Tras el cambio aprobó bajo la misma condición de una CPU y en la selección final con la configuración original. La configuración de CPU se restauró recreando únicamente el contenedor de pruebas con su mismo volumen; `NanoCpus=0` se verificó al final.
