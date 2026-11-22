from neo4j import Query
from pymongo import ReturnDocument

from backend.schemas import Song, SongPage, SongSummary
from scripts.storage import DATABASE_DIR

RECOMMENDATIONS_QUERY = (DATABASE_DIR / "neo4j/queries/recommendations.cypher").read_text(encoding="utf-8")


class CatalogRepository:
    def __init__(self, client):
        self.client = client
        self.songs = client.soundgraph.songs

    @staticmethod
    def song(document):
        return Song(songId=document["_id"], title=document["title"], editorial=document["editorial"])

    def ready(self):
        self.client.admin.command("ping")

    def by_ids(self, song_ids):
        if not song_ids:
            self.ready()
            return {}
        return {doc["_id"]: self.song(doc) for doc in self.songs.find({"_id": {"$in": list(song_ids)}})}

    def exists(self, song_id):
        return self.songs.find_one({"_id": song_id}, {"_id": 1}) is not None

    def list_songs(self, after, limit):
        criteria = {"_id": {"$gt": after}} if after is not None else {}
        documents = list(self.songs.find(criteria, {"title": 1}).sort("_id", 1).limit(limit + 1))
        return SongPage(
            items=[SongSummary(songId=doc["_id"], title=doc["title"]) for doc in documents[:limit]],
            nextAfter=documents[limit - 1]["_id"] if len(documents) > limit else None,
        )

    def find_song(self, song_id):
        document = self.songs.find_one({"_id": song_id})
        return self.song(document) if document else None

    def replace_notes(self, song_id, notes):
        document = self.songs.find_one_and_update(
            {"_id": song_id}, {"$set": {"editorial.notes": [note.model_dump() for note in notes]}},
            return_document=ReturnDocument.AFTER,
        )
        return self.song(document) if document else None


class GraphRepository:
    def __init__(self, driver):
        self.driver = driver

    def ready(self):
        self.driver.execute_query(Query("RETURN 1", timeout=3), database_="neo4j", routing_="r")

    def recommendations(self, profile_id, limit):
        records, _, _ = self.driver.execute_query(
            Query(RECOMMENDATIONS_QUERY, timeout=4), profile_id=profile_id, limit=limit,
            database_="neo4j", routing_="r",
        )
        return [(row["song_id"], row["affinity"]) for row in records]
