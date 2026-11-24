# Perfiles personales, preparación de Neo4j e interfaz

Fecha local: 23 de noviembre de 2026. Cambios locales sobre `b287571`, sin commit. Windows y Docker Desktop; los reinicios y las altas temporales se ejecutaron exclusivamente en `soundgraph-test`, puerto 18080, con sus volúmenes existentes. No se ejecutaron benchmarks ni suites completas por rutina.

## Causa y corrección de H07

La primera reproducción sin límite de CPU aprobó, consistente con un fallo intermitente. Para reproducir el arranque lento de forma controlada, se limitó temporalmente Neo4j de pruebas a una CPU. H07 falló tras salud `200`; el registro de la primera recomendación capturó `Neo.ClientError.Transaction.TransactionTimedOutClientConfiguration`. La consulta conserva el timeout de cuatro segundos. `RETURN 1` no había comprobado la preparación de la consulta real.

La salud ejecuta ahora esa misma consulta con Ana y límite 1. Mientras no puede completarla responde `503`; no fabrica recomendaciones vacías. H07 conserva exactamente su cuerpo anterior, comprobado mediante comparación AST contra HEAD. Tras el cambio aprobó bajo la misma condición de una CPU y en la selección final con la configuración original. La configuración de CPU se restauró recreando únicamente el contenedor de pruebas con su mismo volumen; `NanoCpus=0` se verificó al final.

## Perfiles y fallos parciales

La migración `003_personal_profiles.sql` añade `personal_access`. El servidor genera identidad y código aleatorios; la transacción SQL confirma perfil oyente, hash del código y sesión. El nombre no autentica y no es único. El nodo de Neo4j se crea después con `MERGE`; `graph_pending` solo se limpia tras completar esa escritura.

Se probaron dos perfiles con el mismo nombre, IDs diferentes, sesiones persistentes, cierre y acceso posterior por código, playlists independientes y denegación de operaciones sobre listas ajenas. Un alta con `role` explícito o nombre vacío devuelve `422`; el oyente no obtiene acceso editorial.

La prueba de caída del grafo detectó inicialmente un timeout HTTP durante la sincronización gestionada con reintentos del driver. Se cambió únicamente esa escritura a un intento auto-commit consumido; la marca SQL mantiene el reintento idempotente desde la aplicación. La prueba final confirmó alta `201` con `graphPending: true`, identidad y acceso disponibles durante la caída, recomendaciones `503` y reconciliación posterior del mismo perfil, con exactamente un nodo y la marca pendiente limpia.

## Resultados actuales

| Comprobación | Resultado |
| --- | --- |
| Unitarias afectadas: perfiles, sesiones, modelos y repositorio SQL | 60 aprobadas |
| Formularios, sin dependencia DOM: `node --test tests/unit/frontend_access.test.cjs` | 2 aprobadas; envío POST, prevención de navegación, nombre del servidor y presentación del código |
| Selección HTTP final: H00, H01, H02, H03, H07, H08, H09 y H10 | 8 aprobadas en 160,910 s |
| H07 con una CPU tras corregir la preparación | Aprobada sin modificar la prueba |
| Auditorías tras pruebas y actualización de uso | Sin incidencias |
| Contrato OpenAPI activo | Coincide con el JSON versionado actualizado, 18 operaciones |
| Sintaxis JavaScript/Python y `git diff --check` | Correctas |

Los intentos fallidos de diagnóstico se distinguen arriba; no se consideran aprobados por una ejecución posterior. Las pruebas de integración anteriores no se repitieron ni se presentan como resultados de esta actualización.

## Interfaz y límite de la verificación visual

Se sustituyó la identidad clara por fondo oscuro, acentos violeta, tarjetas musicales, tipografía sans, navegación y formularios agrupados. Se conservan los modales nativos, los avisos, el teclado, el foco visible y el movimiento reducido. Se añadieron Crear perfil y Mi código, manteniendo Demo / Editor. El código personal se muestra oculto inicialmente, permite copiarlo y pide guardarlo antes de continuar.

Se observó la pantalla de acceso en navegador de escritorio con viewport interno de 1024 px. El cambio de tamaño del navegador integrado solo recortó la captura, por lo que no se considera una verificación móvil. El control nativo de Chrome terminó por no poder determinar la URL con confianza. Quedan pendientes la revisión visual real en móvil y el recorrido completo del nuevo flujo en navegador; las pruebas de formularios sin DOM no los sustituyen.

## Conservación y estado local

En `soundgraph-dev` se aplicó solamente la migración aditiva y se recreó la API; no se repitió la semilla ni se reiniciaron las bases. Las huellas SHA-256 del contenido de perfiles, playlists, pistas, fichas, nodos y relaciones coincidieron antes y después: cuatro perfiles, tres playlists, dos pistas guardadas y tres fichas. Las sesiones no forman parte de esa huella.

La interfaz, Swagger, salud y OpenAPI respondieron `200` en el puerto 8000. Se comprobó el acceso de Ana y la recomendación C.R.E.A.M. con afinidad 1 sin modificar contenido. Las credenciales y volúmenes se conservaron.
