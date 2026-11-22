"""
Pruebas unitarias del repositorio SQL (backend/repositories/sql.py).

Cubren:
- SqlRepository.profile: conversión de fila a objeto Profile y None.
- SqlRepository.list_playlists: construcción de objetos Playlist desde filas.
- SqlRepository.reorder_tracks: valida permutación exacta antes de actualizar.
- SqlRepository.owned_playlist: lanza 404 cuando la fila no existe.

La conexión de base de datos (self.db) se sustituye con un MagicMock,
por lo que estas pruebas no tocan PostgreSQL.
"""

import unittest
from unittest.mock import MagicMock, call

from backend.errors import ApiError
from backend.repositories.sql import SqlRepository


def _repo():
    db = MagicMock()
    return SqlRepository(db), db


class TestProfileStaticMethod(unittest.TestCase):
    """profile convierte una fila en Profile o devuelve None."""

    def test_row_produces_profile(self):
        profile = SqlRepository.profile(("p-ana-main", "Ana", "listener"))
        self.assertEqual(profile.profileId, "p-ana-main")
        self.assertEqual(profile.displayName, "Ana")
        self.assertEqual(profile.role, "listener")

    def test_none_row_returns_none(self):
        self.assertIsNone(SqlRepository.profile(None))

    def test_editor_role_accepted(self):
        profile = SqlRepository.profile(("p-editor", "Editor", "editor"))
        self.assertEqual(profile.role, "editor")


class TestListPlaylists(unittest.TestCase):
    """list_playlists traduce filas SQL a objetos Playlist con trackCount."""

    def test_returns_playlist_objects(self):
        repo, db = _repo()
        db.execute.return_value = [
            ("pl-1", "Rock clásico", 3),
            ("pl-2", "Jazz suave", 0),
        ]
        result = repo.list_playlists("p-ana-main")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].playlistId, "pl-1")
        self.assertEqual(result[0].name, "Rock clásico")
        self.assertEqual(result[0].trackCount, 3)
        self.assertEqual(result[1].trackCount, 0)

    def test_no_playlists_returns_empty_list(self):
        repo, db = _repo()
        db.execute.return_value = []
        result = repo.list_playlists("p-new")
        self.assertEqual(result, [])

    def test_query_filters_by_owner(self):
        repo, db = _repo()
        db.execute.return_value = []
        repo.list_playlists("p-sofia")
        args = db.execute.call_args[0]
        self.assertIn("p-sofia", args[1])


class TestOwnedPlaylist(unittest.TestCase):
    """owned_playlist devuelve el nombre o lanza ApiError 404."""

    def test_returns_name_when_playlist_exists(self):
        repo, db = _repo()
        db.execute.return_value.fetchone.return_value = ("Para escuchar",)
        name = repo.owned_playlist("p-ana-main", "pl-ana-demo")
        self.assertEqual(name, "Para escuchar")

    def test_raises_404_when_not_found(self):
        repo, db = _repo()
        db.execute.return_value.fetchone.return_value = None
        with self.assertRaises(ApiError) as ctx:
            repo.owned_playlist("p-ana-main", "pl-ajena")
        self.assertEqual(ctx.exception.status, 404)
        self.assertEqual(ctx.exception.code, "playlist_not_found")

    def test_lock_appends_for_update(self):
        repo, db = _repo()
        db.execute.return_value.fetchone.return_value = ("Nombre",)
        repo.owned_playlist("p-ana-main", "pl-x", lock=True)
        query_used = db.execute.call_args[0][0]
        self.assertIn("FOR UPDATE", query_used)


class TestReorderTracks(unittest.TestCase):
    """reorder_tracks valida que la permutación sea exacta antes de actualizar."""

    def _setup_existing_tracks(self, db, tracks):
        """Configura el mock para que owned_playlist y tracks devuelvan datos conocidos."""
        # Primera llamada a execute: owned_playlist (devuelve fila con nombre)
        # Segunda llamada: tracks (devuelve lista de pares)
        # Resto: SET CONSTRAINTS + UPDATE
        name_mock = MagicMock()
        name_mock.fetchone.return_value = ("Playlist",)
        tracks_mock = iter(tracks)

        def execute_side(query, *args, **kwargs):
            if "owner_id" in query and "playlist_id" in query and "SELECT name" in query:
                return name_mock
            if "SELECT song_id" in query:
                return list(tracks)
            return MagicMock()

        db.execute.side_effect = execute_side
        db.transaction.return_value.__enter__ = MagicMock(return_value=None)
        db.transaction.return_value.__exit__ = MagicMock(return_value=False)
        db.cursor.return_value.__enter__ = MagicMock(return_value=MagicMock())
        db.cursor.return_value.__exit__ = MagicMock(return_value=False)

    def test_mismatched_song_ids_raises_422(self):
        repo, db = _repo()
        # tracks devuelve [c-a, c-b] pero se envía solo [c-a]
        db.execute.return_value.fetchone.return_value = ("Playlist",)
        db.transaction.return_value.__enter__ = MagicMock(return_value=None)
        db.transaction.return_value.__exit__ = MagicMock(return_value=False)

        # Simular que tracks() devuelve dos elementos
        with unittest.mock.patch.object(repo, "tracks", return_value=[("c-a", 1), ("c-b", 2)]), \
             unittest.mock.patch.object(repo, "owned_playlist", return_value="Playlist"):
            with self.assertRaises(ApiError) as ctx:
                repo.reorder_tracks("p-ana-main", "pl-x", ["c-a"])
            self.assertEqual(ctx.exception.status, 422)
            self.assertEqual(ctx.exception.code, "invalid_track_order")

    def test_wrong_set_raises_422(self):
        repo, db = _repo()
        with unittest.mock.patch.object(repo, "tracks", return_value=[("c-a", 1), ("c-b", 2)]), \
             unittest.mock.patch.object(repo, "owned_playlist", return_value="Playlist"), \
             unittest.mock.patch.object(db, "transaction"):
            db.transaction.return_value.__enter__ = MagicMock(return_value=None)
            db.transaction.return_value.__exit__ = MagicMock(return_value=False)
            with self.assertRaises(ApiError) as ctx:
                repo.reorder_tracks("p-ana-main", "pl-x", ["c-a", "c-WRONG"])
            self.assertEqual(ctx.exception.status, 422)
