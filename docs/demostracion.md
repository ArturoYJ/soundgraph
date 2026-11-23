# SoundGraph — Recorrido de evaluación

Sigue el [arranque local](../README.md#arranque-local), abre [SoundGraph](http://127.0.0.1:8000/) y comprueba que [el estado de la API](http://127.0.0.1:8000/health/ready) devuelva `{"status":"ok"}`. Los perfiles y las escuchas son datos sintéticos de la semilla. Los códigos de los perfiles se generan de forma local en `.env.demo`; no deben aparecer en el cartel ni en capturas.

## Recorrido principal

| Paso | Resultado que debe observarse | Qué lo explica |
| --- | --- | --- |
| 1. Entra como **Ana** con `DEMO_CODE_ANA` y abre **Descubrir**. | «C.R.E.A.M.» aparece como recomendación con afinidad de **un perfil**, aunque ese perfil comparte dos escuchas con Ana. | PostgreSQL identifica la sesión; Neo4j consulta las escuchas y cuenta perfiles distintos. MongoDB devuelve las fichas de las canciones encontradas. |
| 2. Pulsa **Ver ficha**. | Se muestran el título, el crédito y la nota disponible para la canción de la semilla. | La ficha y las notas provienen de MongoDB. |
| 3. Guarda la canción en **Para escuchar**, abre la playlist y recarga. | La pista sigue visible. Repite el guardado: el mensaje indica que ya estaba en la playlist y no aparece otra entrada. | La API verifica que exista la ficha. PostgreSQL registra la pista y controla la unicidad dentro de la playlist. |

La primera vez solo se mostrará **Guardada** si la pista aún no estaba en la lista. Si el entorno ya se usó para ensayar, emplea una playlist temporal para demostrar el alta sin alterar una lista existente.

## Preparación previa de gestión

Antes de presentar, entra como Ana y crea una playlist temporal en **Mis playlists**. Desde **Descubrir**, guarda «C.R.E.A.M.» en ella. Para añadir la segunda canción de la semilla:

1. Abre [Swagger](http://127.0.0.1:8000/docs) en el mismo navegador y origen, con la sesión de Ana activa.
2. Ejecuta `GET /api/v1/playlists` e identifica el `playlistId` de la lista temporal.
3. Ejecuta `PUT /api/v1/playlists/{playlistId}/tracks/{songId}` con ese identificador y `songId: c-soWhat`.
4. Vuelve a la lista y comprueba que aparecen ambas pistas. Conserva otra lista vacía para mostrar un primer guardado.

La preparación usa datos de prueba y deja las pistas disponibles antes de la exposición; no es necesario usar Swagger durante el recorrido en vivo.

## Recorrido de gestión y edición

- **Playlists, como Ana:** abre la playlist preparada, renómbrala y selecciona **Reordenar pistas**. Mueve una pista con **Subir/Bajar**, guarda y recarga. Quita una pista y, al terminar, elimina solo la playlist de ensayo; las canciones del catálogo no se borran.
- **Notas, como Editor:** cierra la sesión de Ana, entra como **Editor** con `DEMO_CODE_EDITOR`, abre **Editorial** y elige una ficha. Guarda un cambio en el texto o la fuente de una nota, recarga y vuelve a abrirla para verificar el resultado. Para una demostración con escritura editorial, usa datos de prueba o restaura la nota inicial al terminar. Los créditos y el título no se editan desde este formulario.

[Índice de entregables](entregables.md) · [Evidencia del recorrido principal](evidence/2026-11-21-h1-frontend.md) · [Evidencia de gestión y edición](evidence/2026-11-21-h2-frontend.md)
