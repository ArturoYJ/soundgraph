import os

import pytest

from scripts.storage import DATABASE_DIR, open_stores

pytestmark = pytest.mark.skipif(
    os.getenv("SOUNDGRAPH_ISOLATED_TEST") != "1",
    reason="Requiere el proyecto Compose soundgraph-test con la semilla local",
)


@pytest.mark.parametrize(
    ("profile_id", "expected"),
    [
        ("p-ana-main", [("c-cream", 1)]),
        ("p-new", []),
    ],
)
def test_recommendation_query(profile_id, expected):
    query = (DATABASE_DIR / "neo4j/queries/recommendations.cypher").read_text(encoding="utf-8")
    with open_stores() as stores:
        rows, _, _ = stores.graph.execute_query(
            query, profile_id=profile_id, limit=10, database_="neo4j"
        )
        assert [(row["song_id"], row["affinity"]) for row in rows] == expected
        if rows:
            assert stores.mongo.songs.find_one({"_id": rows[0]["song_id"]})["title"] == "C.R.E.A.M."
