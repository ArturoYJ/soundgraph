# SoundGraph — Diseño del MVP de descubrimiento musical

**Fecha:** 21 de noviembre de 2026

**Estado:** alcance aceptado; se avanzó al [plan de implementación](../plans/2026-11-21-soundgraph-mvp-implementation.md). No acredita implementación.

## 1. Problema y alcance

Una persona que quiere descubrir música necesita saber por qué una canción puede interesarle, consultar su contexto y guardarla para después. SoundGraph ofrecerá una recomendación explicable basada en escuchas compartidas. La demo usará perfiles e historiales de prueba precargados; no recopilará datos de oyentes reales.

- **Oyente:** consulta recomendaciones y fichas editoriales; crea, consulta, renombra, reordena y elimina sus playlists; añade y quita pistas.
- **Editor de la demo:** actualiza una sección editorial en una ficha existente. La autorización se comprueba en el backend, no en la interfaz.
- **Fuera del MVP:** reproducción de audio, suscripciones, alta pública de cuentas, edición colaborativa y escritura de historiales de escucha. Las rutas de influencia quedan como extensión posterior a la demo.

## 2. Responsabilidades y fuentes de verdad

| Motor | Dato oficial | Operación y regla que lo justifican |
| --- | --- | --- |
| **PostgreSQL** | Perfil, rol, propiedad de la playlist, pistas guardadas y posición | Gestionar playlists de un perfil; impedir pistas repetidas y ordenar o eliminar sus entradas de forma atómica. Las relaciones dentro de SQL usan claves foráneas. |
| **MongoDB** | Ficha de canción identificada por `songId`: título y secciones editoriales como créditos por rol, versiones o notas con fuentes | Leer y editar la ficha como un documento con secciones anidadas que pueden variar por canción. Validar los campos comunes y las secciones admitidas. |
| **Neo4j** | Historial de escucha: relaciones `ESCUCHÓ` entre nodos que referencian `profileId` y `songId` | Recorrer escuchas compartidas para sugerir canciones no escuchadas. Ni las cuentas ni el contenido editorial tienen su valor oficial aquí. |

Los motores comparten identificadores, no copias editables de títulos, cuentas ni fichas. Las semillas se cargan con los mismos identificadores: primero perfiles y fichas, después las relaciones de escucha. Una comprobación de consistencia debe reportar referencias huérfanas entre motores. El MVP no elimina ni cambia los identificadores de perfiles o canciones. Guardar una canción valida que exista su ficha antes de escribir en SQL; no requiere editar el catálogo ni el grafo.

## 3. Flujo integrado

Una interfaz web mínima consume una API modular. La API valida la sesión local de demo y obtiene el perfil y rol de PostgreSQL. El servicio de descubrimiento pide a Neo4j candidatos por afinidad y solicita a MongoDB sus fichas en bloque. Devuelve una sola lista con canción y motivo. La interfaz nunca accede directamente a los motores.

1. Ana abre **Descubrir**. El backend consulta su perfil en PostgreSQL.
2. Neo4j encuentra perfiles con al menos una escucha en común y canciones que ellos escucharon, pero Ana no. La adaptación de Q-01 cuenta **perfiles distintos por `songId`**; en empates ordena por identificador. La explicación no expone los nombres de otros oyentes.
3. MongoDB aporta la ficha editorial de cada candidata. Con la semilla base, **«C.R.E.A.M.» debe aparecer entre las recomendaciones**, no necesariamente en primer lugar.
4. Ana guarda la canción en una playlist propia. La API confirma que la ficha existe y añade la pista en una única transacción en PostgreSQL. Repetir el guardado no duplica la pista ni cambia su posición. Al recargar la playlist, la pista debe seguir allí.
5. Como prueba del valor documental, el editor modifica una nota de la ficha y se vuelve a consultar la recomendación: cambia el contenido editorial, no la afinidad ni la playlist.

## 4. Consistencia y respuesta ante errores

- **Sin historial o sin candidatos con los motores operativos:** resultado vacío normal con mensaje explicativo.
- **Candidato con ficha inexistente:** no mostrar un resultado incompleto como válido; excluir la entrada, señalar que hay resultados parciales y registrar su identificador para revisar la semilla. Un intento de guardar esa canción se rechaza antes de escribir.
- **Motor no disponible:** la operación que lo necesita muestra un error de servicio y permite reintentar. No se presenta como lista vacía ni como guardado exitoso.
- **Permisos:** el backend obtiene el perfil desde la sesión de demo y verifica propiedad o rol según la operación. Una solicitud de otro perfil no modifica la playlist. El despliegue previsto es local, con cuentas sintéticas y sin credenciales versionadas.
- **Escrituras:** cada operación modifica un solo motor. Si falla una transacción SQL no quedan posiciones ni entradas actualizadas parcialmente. No se incluye sincronización de copias editables, compensación distribuida ni cambios de identificador.

## 5. Criterios de aceptación y evidencia

| Prueba | Resultado esperado |
| --- | --- |
| Arranque limpio | Las tres bases se crean y cargan siguiendo el README; la API verifica conexión con las tres. No se usan credenciales reales. |
| Descubrimiento integrado | Ana ve «C.R.E.A.M.» con un motivo de afinidad y su ficha editorial. Una pista ya escuchada no aparece. Dos coincidencias del mismo perfil cuentan una sola vez. |
| Persistencia relacional | Guardar dos veces deja una sola entrada. El reordenamiento válido persiste; el inválido no deja cambios parciales. Otro perfil no puede editar la playlist. |
| Validación documental | Una edición válida es visible en la siguiente consulta y no cambia la puntuación de afinidad. Un documento inválido se rechaza. |
| Consistencia y fallos | Un perfil sin historial devuelve vacío normal. Una ficha ausente produce un resultado parcial controlado y no permite guardar esa pista. Un motor caído devuelve un error distinguible y recupera el flujo al restablecerse. |
| Rendimiento básico | Registrar duración de solicitudes de descubrimiento tras el arranque, tamaño de la semilla, número de solicitudes y entorno. No inferir ventajas generales sobre SQL a partir de esa medición. |

Antes de reutilizar Q-01, validar la semilla y el DDL del integrador en la edición concreta de Neo4j. El script histórico incluye restricciones de existencia que requieren Enterprise en Neo4j 5; si se elige Community, el esquema se adaptará en **archivos nuevos** y se comprobarán las reglas requeridas mediante validación y pruebas. No se modifica la práctica histórica.

## 6. Orden de entrega

1. **Primero:** cargar las tres bases con identificadores coherentes y comprobar el flujo de abrir una recomendación y guardarla. La ficha de una candidata faltante y la caída de una dependencia son los primeros casos negativos.
2. **Después:** completar edición documental, operaciones de playlist, catálogo de operaciones, scripts e instrucciones reproducibles. Fijar versiones compatibles, framework y comandos en el plan de implementación.
3. **Cartel:** seleccionar evidencia que exista al cierre del **25 de noviembre, 23:59**: resultado comprobado del flujo, limitaciones y QR al repositorio cuando esté confirmado. No trasladar gráficos de muestra. Completar los entregables técnicos del integrador para el **27 de noviembre**.

Los criterios académicos y sus fuentes son los de la documentación académica local. El mapa de arquitectura de contexto sigue siendo conceptual; este diseño no acredita servicios en ejecución ni resultados de pruebas.
