import json
import re
import sys

from scripts.check_references import collect_issues
from scripts.storage import DATABASE_DIR, DATABASE_ERRORS, open_stores

ID_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9-]{0,63}")


def unique_ids(rows, key):
    values = [row[key] for row in rows]
    if any(not isinstance(value, str) or not ID_PATTERN.fullmatch(value) for value in values):
        raise ValueError(f"Identificador inválido en {key}.")
    if len(values) != len(set(values)):
        raise ValueError(f"Identificador duplicado en {key}.")
    return set(values)


def load_fixture():
    data = json.loads((DATABASE_DIR / "fixtures/demo.json").read_text(encoding="utf-8"))
    profiles = unique_ids(data["profiles"], "id")
    songs = unique_ids(data["songs"], "_id")
    unique_ids(data["playlists"], "id")
    if any(row["ownerId"] not in profiles for row in data["playlists"]):
        raise ValueError("Playlist con propietario fuera de la semilla.")
    pairs = set()
    for row in data["listens"]:
        profile, song = row["profileId"], row["songId"]
        if profile not in profiles or song not in songs or (profile, song) in pairs:
            raise ValueError("Relación de escucha duplicada o sin referencia en la semilla.")
        pairs.add((profile, song))
    return data


def seed(stores, data):
    with stores.postgres.transaction():
        for migration in sorted((DATABASE_DIR / "postgres").glob("[0-9]*_*.sql")):
            stores.postgres.execute(migration.read_text(encoding="utf-8"))
        with stores.postgres.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO profiles VALUES (%s, %s, %s) ON CONFLICT (profile_id) DO NOTHING",
                [(row["id"], row["name"], row["role"]) for row in data["profiles"]],
            )
            cursor.executemany(
                "INSERT INTO playlists VALUES (%s, %s, %s) ON CONFLICT (playlist_id) DO NOTHING",
                [(row["id"], row["ownerId"], row["name"]) for row in data["playlists"]],
            )

    validator = json.loads(
        (DATABASE_DIR / "mongo/song_validator.json").read_text(encoding="utf-8")
    )
    validation = {"validator": validator, "validationLevel": "strict", "validationAction": "error"}
    if "songs" not in stores.mongo.list_collection_names():
        stores.mongo.create_collection("songs", **validation)
    else:
        stores.mongo.command("collMod", "songs", **validation)
    for doc in data["songs"]:
        fields = {key: value for key, value in doc.items() if key != "_id"}
        stores.mongo.songs.update_one({"_id": doc["_id"]}, {"$setOnInsert": fields}, upsert=True)

    commands = (DATABASE_DIR / "neo4j/001_schema.cypher").read_text(encoding="utf-8")
    for command in commands.split(";"):
        if command.strip():
            stores.graph.execute_query(command.strip(), database_="neo4j")
    stores.graph.execute_query("CALL db.awaitIndexes(30)", database_="neo4j")
    stores.graph.execute_query(
        "UNWIND $ids AS id MERGE (:Perfil {profileId: id})",
        ids=[row["id"] for row in data["profiles"]], database_="neo4j",
    )
    stores.graph.execute_query(
        "UNWIND $ids AS id MERGE (:Cancion {songId: id})",
        ids=[doc["_id"] for doc in data["songs"]], database_="neo4j",
    )
    stores.graph.execute_query(
        """
        UNWIND $rows AS row
        MATCH (p:Perfil {profileId: row.profileId}), (s:Cancion {songId: row.songId})
        MERGE (p)-[:`ESCUCHÓ`]->(s)
        """,
        rows=data["listens"], database_="neo4j",
    )


def main():
    try:
        data = load_fixture()
        with open_stores() as stores:
            seed(stores, data)
            issues = collect_issues(stores)
            if issues:
                print("Carga con inconsistencias:\n" + "\n".join(issues), file=sys.stderr)
                return 1
            version_pg = stores.postgres.execute("SHOW server_version").fetchone()[0]
            version_mongo = stores.mongo.command("buildInfo")["version"]
            result, _, _ = stores.graph.execute_query(
                "CALL dbms.components() YIELD versions, edition RETURN versions[0] AS version, edition",
                database_="neo4j",
            )
    except (*DATABASE_ERRORS, ValueError, KeyError, TypeError, OSError) as error:
        print(
            f"No se completó la carga ({type(error).__name__}). "
            "Corrija la causa y vuelva a ejecutar el cargador; pueden existir datos parciales.",
            file=sys.stderr,
        )
        return 1
    print(f"PostgreSQL {version_pg} · MongoDB {version_mongo} · Neo4j {result[0]['version']} ({result[0]['edition']})")
    print("Semilla de SoundGraph verificada: sin referencias huérfanas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
