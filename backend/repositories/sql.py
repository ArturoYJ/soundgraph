from uuid import uuid4

from backend.errors import ApiError, missing_playlist
from backend.schemas import Playlist, Profile


class SqlRepository:
    def __init__(self, db):
        self.db = db

    def ready(self):
        self.db.execute("SELECT 1 FROM demo_sessions LIMIT 1")
        self.db.execute("SELECT 1 FROM personal_access LIMIT 1")

    @staticmethod
    def profile(row):
        return Profile(profileId=row[0], displayName=row[1], role=row[2]) if row else None

    def find_profile(self, profile_id):
        return self.profile(self.db.execute(
            "SELECT profile_id, display_name, role FROM profiles WHERE profile_id=%s",
            (profile_id,),
        ).fetchone())

    def find_session(self, token_hash):
        return self.profile(self.db.execute(
            """SELECT p.profile_id, p.display_name, p.role FROM demo_sessions s
               JOIN profiles p ON p.profile_id=s.profile_id
               WHERE s.token_hash=%s AND s.expires_at > now()""",
            (token_hash,),
        ).fetchone())

    def create_session(self, token_hash, profile_id, expires_at, previous_hash):
        with self.db.transaction():
            self.db.execute("DELETE FROM demo_sessions WHERE expires_at <= now()")
            if previous_hash:
                self.delete_session(previous_hash)
            self.db.execute(
                "INSERT INTO demo_sessions (token_hash, profile_id, expires_at) VALUES (%s,%s,%s)",
                (token_hash, profile_id, expires_at),
            )

    def delete_session(self, token_hash):
        self.db.execute("DELETE FROM demo_sessions WHERE token_hash=%s", (token_hash,))

    def create_personal_profile(self, profile_id, name, code_hash, token_hash, expires_at, previous_hash):
        with self.db.transaction():
            self.db.execute(
                "INSERT INTO profiles (profile_id, display_name, role) VALUES (%s,%s,'listener')",
                (profile_id, name),
            )
            self.db.execute(
                "INSERT INTO personal_access (profile_id, code_hash) VALUES (%s,%s)",
                (profile_id, code_hash),
            )
            self.create_session(token_hash, profile_id, expires_at, previous_hash)
        return Profile(profileId=profile_id, displayName=name, role="listener")

    def find_personal_profile(self, profile_id, code_hash):
        return self.profile(self.db.execute(
            """SELECT p.profile_id, p.display_name, p.role FROM profiles p
               JOIN personal_access a USING (profile_id)
               WHERE p.profile_id=%s AND a.code_hash=%s""", (profile_id, code_hash),
        ).fetchone())

    def graph_pending(self, profile_id):
        row = self.db.execute(
            "SELECT graph_pending FROM personal_access WHERE profile_id=%s", (profile_id,),
        ).fetchone()
        return bool(row and row[0])

    def mark_graph_synced(self, profile_id):
        self.db.execute("UPDATE personal_access SET graph_pending=false WHERE profile_id=%s", (profile_id,))

    def list_playlists(self, owner):
        rows = self.db.execute(
            """SELECT p.playlist_id, p.name, count(t.song_id)
               FROM playlists p LEFT JOIN playlist_tracks t USING (playlist_id)
               WHERE p.owner_id=%s
               GROUP BY p.playlist_id ORDER BY lower(p.name), p.playlist_id""", (owner,)
        )
        return [Playlist(playlistId=row[0], name=row[1], trackCount=row[2]) for row in rows]

    def owned_playlist(self, owner, playlist_id, *, lock=False):
        query = "SELECT name FROM playlists WHERE owner_id=%s AND playlist_id=%s"
        if lock:
            query += " FOR UPDATE"
        row = self.db.execute(query, (owner, playlist_id)).fetchone()
        if not row:
            raise missing_playlist()
        return row[0]

    def tracks(self, playlist_id):
        return list(self.db.execute(
            "SELECT song_id, position FROM playlist_tracks WHERE playlist_id=%s ORDER BY position",
            (playlist_id,),
        ))

    def detail(self, owner, playlist_id):
        with self.db.transaction():
            self.db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            name = self.owned_playlist(owner, playlist_id)
            return name, self.tracks(playlist_id)

    def create_playlist(self, owner, name):
        playlist_id = f"pl-{uuid4().hex}"
        self.db.execute(
            "INSERT INTO playlists (playlist_id, owner_id, name) VALUES (%s,%s,%s)",
            (playlist_id, owner, name),
        )
        return Playlist(playlistId=playlist_id, name=name, trackCount=0)

    def rename_playlist(self, owner, playlist_id, name):
        with self.db.transaction():
            self.owned_playlist(owner, playlist_id, lock=True)
            self.db.execute("UPDATE playlists SET name=%s WHERE playlist_id=%s", (name, playlist_id))
            count = self.db.execute(
                "SELECT count(*) FROM playlist_tracks WHERE playlist_id=%s", (playlist_id,)
            ).fetchone()[0]
        return Playlist(playlistId=playlist_id, name=name, trackCount=count)

    def delete_playlist(self, owner, playlist_id):
        row = self.db.execute(
            "DELETE FROM playlists WHERE owner_id=%s AND playlist_id=%s RETURNING playlist_id",
            (owner, playlist_id),
        ).fetchone()
        if not row:
            raise missing_playlist()

    def save_track(self, owner, playlist_id, song_id):
        with self.db.transaction():
            self.owned_playlist(owner, playlist_id, lock=True)
            row = self.db.execute(
                "SELECT position FROM playlist_tracks WHERE playlist_id=%s AND song_id=%s",
                (playlist_id, song_id),
            ).fetchone()
            if row:
                return row[0], False
            position = self.db.execute(
                "SELECT coalesce(max(position),0)+1 FROM playlist_tracks WHERE playlist_id=%s",
                (playlist_id,),
            ).fetchone()[0]
            self.db.execute(
                "INSERT INTO playlist_tracks (playlist_id, song_id, position) VALUES (%s,%s,%s)",
                (playlist_id, song_id, position),
            )
        return position, True

    def reorder_tracks(self, owner, playlist_id, song_ids):
        with self.db.transaction():
            self.owned_playlist(owner, playlist_id, lock=True)
            existing = self.tracks(playlist_id)
            if len(song_ids) != len(existing) or set(song_ids) != {track[0] for track in existing}:
                raise ApiError(422, "invalid_track_order", "Envía todas las pistas actuales una sola vez.")
            self.db.execute("SET CONSTRAINTS playlist_position_unique DEFERRED")
            with self.db.cursor() as cursor:
                cursor.executemany(
                    "UPDATE playlist_tracks SET position=%s WHERE playlist_id=%s AND song_id=%s",
                    [(position, playlist_id, song_id) for position, song_id in enumerate(song_ids, 1)],
                )

    def remove_track(self, owner, playlist_id, song_id):
        with self.db.transaction():
            self.owned_playlist(owner, playlist_id, lock=True)
            row = self.db.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id=%s AND song_id=%s RETURNING position",
                (playlist_id, song_id),
            ).fetchone()
            if row:
                self.db.execute("SET CONSTRAINTS playlist_position_unique DEFERRED")
                self.db.execute(
                    "UPDATE playlist_tracks SET position=position-1 WHERE playlist_id=%s AND position>%s",
                    (playlist_id, row[0]),
                )
