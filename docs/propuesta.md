# SoundGraph — Propuesta de aplicación

## Problema y objetivo

Al descubrir una canción, una persona puede querer saber por qué le fue sugerida, consultar su contexto y conservarla para volver a encontrarla. SoundGraph propone reunir esas tres acciones: **explicar la recomendación a partir de escuchas compartidas, presentar la ficha y guardar la pista en una playlist propia**.

El objetivo es demostrar un flujo funcional que coordine datos transaccionales, fichas documentales y relaciones de escucha, sin que la interfaz se conecte directamente a ninguno de los motores.

## Usuarios y operaciones prioritarias

| Usuario de la demo | Necesidad | Operaciones |
| --- | --- | --- |
| Oyente | Entender la recomendación y conservar una canción | Entrar, descubrir, ver la ficha, guardar y volver a abrir la playlist. Desde Mis playlists puede crear, renombrar, eliminar, reordenar y quitar pistas. |
| Editor | Corregir o actualizar el contexto de una canción | Reemplazar las notas editoriales y sus fuentes desde Editorial, sin cambiar las escuchas ni las playlists. |

El prototipo no reproduce audio, no recopila escuchas de usuarios reales ni ofrece registro público. Los perfiles e historiales se precargan para una demostración académica reproducible.

## Por qué tres modelos

- **PostgreSQL** conserva sesiones y playlists. Al añadir una pista a una playlist propia, la transacción controla la posición y evita entradas duplicadas.
- **MongoDB** conserva la ficha, con créditos y notas que pueden variar según la canción. Al consultar una recomendación, la ficha se obtiene por identificador; editar sus notas no modifica la afinidad.
- **Neo4j** representa escuchas como relaciones entre perfiles y canciones. La consulta encuentra perfiles que comparten escuchas y recomienda canciones nuevas para el perfil consultado.

Con los datos sintéticos de la demo, Ana comparte dos escuchas con otro perfil. Ese perfil también escuchó «C.R.E.A.M.»; por ello, la afinidad para esa recomendación es **1 perfil**, no dos caminos. Este resultado se verificó en la [suite de persistencia](evidence/2026-11-21-h0-data-seed.md) y el [flujo integrado en navegador](evidence/2026-11-21-h1-frontend.md). No representa una evaluación con oyentes reales.

[Modelado](models/modelado-integrado.md) · [Arquitectura](arquitectura.md) · [Catálogo](catalogo-operaciones.md).
