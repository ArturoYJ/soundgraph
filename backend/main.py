import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path as FilePath
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Path, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import APIKeyCookie
from starlette.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.errors import ApiError, missing_song
from backend.repositories.music import CatalogRepository, GraphRepository
from backend.repositories.sql import SqlRepository
from backend.schemas import (
    ID_PATTERN, ErrorBody, Health, Login, NoteUpdate, Playlist, PlaylistDetail,
    PlaylistInput, Playlists, Profile, Recommendations, SavedTrack, Song, SongPage, TrackOrder,
)
from backend.services import discovery, sessions
from scripts.storage import DATABASE_ERRORS, connect_postgres, create_graph_driver, create_mongo_client

log = logging.getLogger("soundgraph.api")
ResourceId = Annotated[str, Path(pattern=ID_PATTERN)]
SessionCookie = Annotated[str | None, Depends(APIKeyCookie(name=sessions.COOKIE, auto_error=False))]


@asynccontextmanager
async def lifespan(app):
    app.state.demo_codes = sessions.configure_codes()
    with create_mongo_client() as mongo, create_graph_driver() as graph:
        app.state.catalog = CatalogRepository(mongo)
        app.state.graph = GraphRepository(graph)
        yield


app = FastAPI(
    title="SoundGraph API", version="1.0.0", lifespan=lifespan,
    description="API REST local de descubrimiento musical con datos sintéticos.",
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])


def error_response(status, code, message, fields=None):
    body = ErrorBody(code=code, message=message, fields=fields)
    return JSONResponse(status_code=status, content=body.model_dump(exclude_none=True))


@app.exception_handler(ApiError)
def app_error(_request, exc):
    return error_response(exc.status, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
def invalid_request(_request, exc):
    fields = sorted({".".join(map(str, item["loc"])).removeprefix("body.") for item in exc.errors()})
    return error_response(422, "invalid_input", "Revisa los campos indicados.", fields)


def dependency_error(_request, exc):
    log.warning("database_request_failed type=%s", type(exc).__name__)
    return error_response(503, "service_unavailable", "Servicio temporalmente no disponible.")


for error_type in DATABASE_ERRORS:
    app.add_exception_handler(error_type, dependency_error)


@app.middleware("http")
async def disable_api_cache(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/v1"):
        response.headers["Cache-Control"] = "no-store"
    return response


def require_local_origin(request: Request):
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    origin = request.headers.get("origin")
    port = os.environ.get("SOUNDGRAPH_API_PORT", "8000")
    allowed_hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
    host = request.headers.get("host", "")
    if request.headers.get("sec-fetch-site") == "cross-site" or (
        origin is not None and (host not in allowed_hosts or origin != f"http://{host}")
    ):
        raise ApiError(403, "invalid_origin", "La solicitud no procede de SoundGraph.")


def sql_repository():
    with connect_postgres() as connection:
        yield SqlRepository(connection)


def catalog_repository(request: Request):
    return request.app.state.catalog


def graph_repository(request: Request):
    return request.app.state.graph


SQL = Annotated[SqlRepository, Depends(sql_repository)]
Catalog = Annotated[CatalogRepository, Depends(catalog_repository)]
Graph = Annotated[GraphRepository, Depends(graph_repository)]


def authenticated(cookie: SessionCookie, sql: SQL):
    return sessions.current_profile(sql, cookie)


User = Annotated[Profile, Depends(authenticated)]


def require_editor(profile: User):
    if profile.role != "editor":
        raise ApiError(403, "editor_required", "No tienes permiso para acceder a la edición de fichas.")


EditorAccess = Annotated[None, Depends(require_editor)]
error_codes = {
    401: {"model": ErrorBody, "description": "Sesión o credenciales no válidas"},
    403: {"model": ErrorBody, "description": "Permiso u origen no permitido"},
    404: {"model": ErrorBody, "description": "Recurso no disponible para el perfil"},
    422: {"model": ErrorBody, "description": "Entrada u orden no válido"},
    503: {"model": ErrorBody, "description": "Una dependencia no está disponible"},
}
api = APIRouter(prefix="/api/v1", dependencies=[Depends(require_local_origin)])


def documented(*statuses):
    return {status: error_codes[status] for status in statuses}


@app.get("/health/ready", response_model=Health, tags=["Servicio"], responses=documented(503))
def ready(sql: SQL, catalog: Catalog, graph: Graph):
    sql.ready()
    catalog.ready()
    graph.ready()
    return Health(status="ok")


@api.post("/demo/sessions", status_code=201, response_model=Profile, tags=["Sesión"],
          responses=documented(401, 403, 422, 503))
def login(credentials: Login, request: Request, response: Response, sql: SQL):
    profile, token = sessions.sign_in(
        sql, request.app.state.demo_codes, credentials, request.cookies.get(sessions.COOKIE)
    )
    response.set_cookie(sessions.COOKIE, token, max_age=sessions.TTL,
                        httponly=True, samesite="strict", path="/api/v1")
    return profile


@api.get("/demo/sessions/current", response_model=Profile, tags=["Sesión"], responses=documented(401, 503))
def me(profile: User):
    return profile


@api.delete("/demo/sessions/current", status_code=204, tags=["Sesión"], responses=documented(403, 503))
def logout(request: Request, response: Response, sql: SQL):
    token_hash = sessions.hash_cookie(request.cookies.get(sessions.COOKIE))
    if token_hash:
        sql.delete_session(token_hash)
    response.delete_cookie(sessions.COOKIE, path="/api/v1", httponly=True, samesite="strict")
    response.status_code = 204
    return response


@api.get("/recommendations", response_model=Recommendations, tags=["Descubrimiento"],
         responses=documented(401, 422, 503))
def recommendations(profile: User, graph: Graph, catalog: Catalog, limit: Annotated[int, Query(ge=1, le=25)] = 10):
    return discovery.discover(profile, graph, catalog, limit)


@api.get("/playlists", response_model=Playlists, tags=["Playlists"], responses=documented(401, 503))
def playlists(profile: User, sql: SQL):
    return Playlists(items=sql.list_playlists(profile.profileId))


@api.post("/playlists", status_code=201, response_model=Playlist, tags=["Playlists"],
          responses=documented(401, 403, 422, 503))
def create_playlist(payload: PlaylistInput, profile: User, sql: SQL):
    return sql.create_playlist(profile.profileId, payload.name)


@api.get("/playlists/{playlistId}", response_model=PlaylistDetail, tags=["Playlists"],
         responses=documented(401, 404, 422, 503))
def playlist(playlistId: ResourceId, profile: User, sql: SQL, catalog: Catalog):
    return discovery.playlist_detail(profile, sql, catalog, playlistId)


@api.patch("/playlists/{playlistId}", response_model=Playlist, tags=["Playlists"],
           responses=documented(401, 403, 404, 422, 503))
def rename_playlist(playlistId: ResourceId, payload: PlaylistInput, profile: User, sql: SQL):
    return sql.rename_playlist(profile.profileId, playlistId, payload.name)


@api.delete("/playlists/{playlistId}", status_code=204, tags=["Playlists"],
            responses=documented(401, 403, 404, 422, 503))
def delete_playlist(playlistId: ResourceId, profile: User, sql: SQL):
    sql.delete_playlist(profile.profileId, playlistId)
    return Response(status_code=204)


@api.put("/playlists/{playlistId}/tracks/{songId}", status_code=201, response_model=SavedTrack, tags=["Playlists"],
         responses={200: {"model": SavedTrack, "description": "La pista ya estaba guardada"},
                    **documented(401, 403, 404, 422, 503)})
def save_track(playlistId: ResourceId, songId: ResourceId, response: Response, profile: User, sql: SQL, catalog: Catalog):
    saved = discovery.save_track(profile, sql, catalog, playlistId, songId)
    if not saved.created:
        response.status_code = 200
    return saved


@api.put("/playlists/{playlistId}/track-order", status_code=204, tags=["Playlists"],
         responses=documented(401, 403, 404, 422, 503))
def track_order(playlistId: ResourceId, payload: TrackOrder, profile: User, sql: SQL):
    sql.reorder_tracks(profile.profileId, playlistId, payload.songIds)
    return Response(status_code=204)


@api.delete("/playlists/{playlistId}/tracks/{songId}", status_code=204, tags=["Playlists"],
            responses=documented(401, 403, 404, 422, 503))
def remove_track(playlistId: ResourceId, songId: ResourceId, profile: User, sql: SQL):
    sql.remove_track(profile.profileId, playlistId, songId)
    return Response(status_code=204)


@api.get("/songs", response_model=SongPage, tags=["Editorial"], responses=documented(401, 403, 422, 503))
def editorial_catalog(
    _editor: EditorAccess, catalog: Catalog,
    after: Annotated[str | None, Query(pattern=ID_PATTERN)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    return catalog.list_songs(after, limit)


@api.get("/songs/{songId}/editorial", response_model=Song, tags=["Editorial"],
         responses=documented(401, 403, 404, 422, 503))
def editorial_detail(songId: ResourceId, _editor: EditorAccess, catalog: Catalog):
    song = catalog.find_song(songId)
    if not song:
        raise missing_song()
    return song


@api.patch("/songs/{songId}/editorial", response_model=Song, tags=["Editorial"],
           responses=documented(401, 403, 404, 422, 503))
def edit_editorial(songId: ResourceId, payload: NoteUpdate, _editor: EditorAccess, catalog: Catalog):
    song = catalog.replace_notes(songId, payload.notes)
    if not song:
        raise missing_song()
    return song


app.include_router(api)

web_root = FilePath(__file__).resolve().parent.parent / "frontend"
app.mount("/assets", StaticFiles(directory=web_root / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(web_root / "index.html", headers={
        "Cache-Control": "no-cache",
        "Content-Security-Policy": (
            "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
            "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        ),
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
    })
