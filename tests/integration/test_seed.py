import os

import psycopg
import pytest
from pymongo.errors import WriteError

from scripts.check_references import collect_issues
from scripts.seed import load_fixture, seed
from scripts.storage import open_stores

pytestmark = pytest.mark.skipif(
    os.getenv("SOUNDGRAPH_ISOLATED_TEST") != "1",
    reason="Requiere el proyecto Compose soundgraph-test con volúmenes propios",
)


@pytest.fixture
def stores():
    with open_stores() as clients:
        yield clients


def counts(stores):
    profiles = stores.postgres.execute("SELECT count(*) FROM profiles").fetchone()[0]
    playlists = stores.postgres.execute("SELECT count(*) FROM playlists").fetchone()[0]
    songs = stores.mongo.songs.count_documents({})
    result, _, _ = stores.graph.execute_query(
        "MATCH (:Perfil)-[r:`ESCUCHÓ`]->(:Cancion) RETURN count(r) AS listens",
        database_="neo4j",
    )
    return profiles, playlists, songs, result[0]["listens"]


def test_seed_is_idempotent_and_keeps_changes(stores):
    seed(stores, load_fixture())
    assert counts(stores) == (4, 1, 3, 5)
    fixture_song = stores.mongo.songs.find_one({"_id": "c-cream"})
    fixture_playlist = stores.postgres.execute(
        "SELECT name FROM playlists WHERE playlist_id=%s", ("pl-ana-demo",)
    ).fetchone()[0]
    try:
        stores.mongo.songs.update_one({"_id": "c-cream"}, {"$set": {"title": "Edición de prueba"}})
        stores.postgres.execute(
            "UPDATE playlists SET name=%s WHERE playlist_id=%s", ("Playlist editada", "pl-ana-demo")
        )
        seed(stores, load_fixture())
        assert counts(stores) == (4, 1, 3, 5)
        assert not collect_issues(stores)
        assert stores.mongo.songs.find_one({"_id": "c-cream"})["title"] == "Edición de prueba"
        assert stores.postgres.execute(
            "SELECT name FROM playlists WHERE playlist_id=%s", ("pl-ana-demo",)
        ).fetchone()[0] == "Playlist editada"
    finally:
        stores.mongo.songs.replace_one({"_id": "c-cream"}, fixture_song)
        stores.postgres.execute(
            "UPDATE playlists SET name=%s WHERE playlist_id=%s", (fixture_playlist, "pl-ana-demo")
        )


def test_mongo_rejects_invalid_document(stores):
    with pytest.raises(WriteError) as error:
        stores.mongo.songs.insert_one({"_id": "c-invalid-test", "title": "sin sección editorial"})
    assert error.value.code == 121


@pytest.mark.parametrize("field", ["text", "source"])
def test_mongo_rejects_whitespace_only_note(stores, field):
    note = {"text": "Nota válida", "source": "Fuente válida"}
    note[field] = "   "
    doc = {"_id": "c-invalid-spaces", "title": "Canción", "editorial": {"notes": [note]}}
    with pytest.raises(WriteError) as error:
        stores.mongo.songs.insert_one(doc)
    assert error.value.code == 121


def test_mongo_accepts_valid_note(stores):
    doc = {"_id": "c-valid-note-test", "title": "Canción",
           "editorial": {"notes": [{"text": "Nota válida", "source": "Fuente válida"}]}}
    try:
        stores.mongo.songs.insert_one(doc)
        assert stores.mongo.songs.find_one({"_id": doc["_id"]}) == doc
    finally:
        stores.mongo.songs.delete_one({"_id": doc["_id"]})


def test_postgres_rejects_inexistent_owner(stores):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        stores.postgres.execute(
            "INSERT INTO playlists VALUES (%s, %s, %s)",
            ("pl-invalid-test", "p-missing-test", "Inválida"),
        )


def test_reference_audit_detects_missing_and_orphan_ids(stores):
    try:
        stores.graph.execute_query(
            "CREATE (:Perfil:SeedProbe {profileId: 'p-orphan-probe'}), (:Cancion:SeedProbe)",
            database_="neo4j",
        )
        assert collect_issues(stores) == [
            "graph_missing_id:Cancion", "graph_orphan:Perfil:p-orphan-probe"
        ]
    finally:
        stores.graph.execute_query("MATCH (n:SeedProbe) DETACH DELETE n", database_="neo4j")
    assert not collect_issues(stores)
