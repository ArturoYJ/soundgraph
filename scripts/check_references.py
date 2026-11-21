import sys

from scripts.storage import DATABASE_ERRORS, open_stores


def collect_issues(stores):
    profiles = {row[0] for row in stores.postgres.execute("SELECT profile_id FROM profiles")}
    songs = {doc["_id"] for doc in stores.mongo.songs.find({}, {"_id": 1})}
    issues = []
    records, _, _ = stores.graph.execute_query(
        """
        MATCH (n)
        WHERE n:Perfil OR n:Cancion
        RETURN labels(n) AS kinds, n.profileId AS profile_id, n.songId AS song_id
        """,
        database_="neo4j",
    )
    for row in records:
        for label, key, ids in (
            ("Perfil", "profile_id", profiles), ("Cancion", "song_id", songs)
        ):
            if label not in row["kinds"]:
                continue
            value = row[key]
            if not isinstance(value, str) or not value.strip():
                issues.append(f"graph_missing_id:{label}")
            elif value not in ids:
                issues.append(f"graph_orphan:{label}:{value}")
    for playlist_id, song_id in stores.postgres.execute(
        "SELECT playlist_id, song_id FROM playlist_tracks"
    ):
        if song_id not in songs:
            issues.append(f"playlist_orphan:{playlist_id}:{song_id}")
    return sorted(issues)


def main():
    try:
        with open_stores() as stores:
            issues = collect_issues(stores)
    except (*DATABASE_ERRORS, KeyError) as error:
        print(f"No se completó la auditoría: {type(error).__name__}.", file=sys.stderr)
        return 2
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1
    print("Referencias entre motores: sin incidencias.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
