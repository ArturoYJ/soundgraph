"""
Pruebas unitarias del servicio de descubrimiento (backend/services/discovery.py).

Cubren:
- discover: lista completa, parcial (ficha ausente) y sin candidatos.
- playlist_detail: playlist con pistas, vacía y con ficha ausente.
- save_track: inserción nueva, canción ya guardada y canción inexistente.

No requieren Docker: graph, catalog y sql son MagicMock.
"""

import unittest
from unittest.mock import MagicMock

from backend.errors import ApiError
from backend.schemas import Editorial, Profile, Song
from backend.services import discovery


def _profile(profile_id="p-ana-main"):
    return Profile(profileId=profile_id, displayName="Ana", role="listener")


def _song(song_id="c-cream"):
    return Song(
        songId=song_id,
        title="C.R.E.A.M.",
        editorial=Editorial(credits=[], notes=[]),
    )


class TestDiscover(unittest.TestCase):
    """discover coordina graph (candidatos) y catalog (fichas)."""

    def test_full_recommendation_list(self):
        graph = MagicMock()
        catalog = MagicMock()
        graph.recommendations.return_value = [("c-cream", 1)]
        catalog.by_ids.return_value = {"c-cream": _song("c-cream")}

        result = discovery.discover(_profile(), graph, catalog, limit=10)

        self.assertFalse(result.partial)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].song.songId, "c-cream")
        self.assertEqual(result.items[0].affinity, 1)
        graph.recommendations.assert_called_once_with("p-ana-main", 10)

    def test_partial_when_song_missing_from_catalog(self):
        graph = MagicMock()
        catalog = MagicMock()
        # Grafo devuelve dos candidatas pero catalog solo tiene una
        graph.recommendations.return_value = [("c-cream", 2), ("c-missing", 1)]
        catalog.by_ids.return_value = {"c-cream": _song("c-cream")}

        result = discovery.discover(_profile(), graph, catalog, limit=10)

        self.assertTrue(result.partial)
        self.assertEqual(len(result.items), 1)

    def test_empty_candidates_returns_empty_items_not_partial(self):
        graph = MagicMock()
        catalog = MagicMock()
        graph.recommendations.return_value = []
        # catalog.ready() debe llamarse (by_ids vacío llama ready)
        catalog.by_ids.return_value = {}

        result = discovery.discover(_profile("p-new"), graph, catalog, limit=10)

        self.assertFalse(result.partial)
        self.assertEqual(result.items, [])


class TestPlaylistDetail(unittest.TestCase):
    """playlist_detail combina filas de SQL con fichas de MongoDB."""

    def test_playlist_with_tracks_hydrates_songs(self):
        sql = MagicMock()
        catalog = MagicMock()
        sql.detail.return_value = ("Para escuchar", [("c-cream", 1)])
        catalog.by_ids.return_value = {"c-cream": _song("c-cream")}

        result = discovery.playlist_detail(_profile(), sql, catalog, "pl-ana-demo")

        self.assertEqual(result.name, "Para escuchar")
        self.assertEqual(result.trackCount, 1)
        self.assertEqual(result.tracks[0].songId, "c-cream")
        self.assertEqual(result.tracks[0].position, 1)
        self.assertIsNotNone(result.tracks[0].song)

    def test_playlist_empty_does_not_call_catalog(self):
        sql = MagicMock()
        catalog = MagicMock()
        sql.detail.return_value = ("Vacía", [])

        result = discovery.playlist_detail(_profile(), sql, catalog, "pl-empty")

        self.assertEqual(result.trackCount, 0)
        self.assertEqual(result.tracks, [])
        catalog.by_ids.assert_not_called()

    def test_track_with_missing_song_becomes_none(self):
        sql = MagicMock()
        catalog = MagicMock()
        sql.detail.return_value = ("Con huérfana", [("c-orphan", 1)])
        catalog.by_ids.return_value = {}  # ficha ausente

        result = discovery.playlist_detail(_profile(), sql, catalog, "pl-x")

        self.assertIsNone(result.tracks[0].song)
        self.assertEqual(result.tracks[0].songId, "c-orphan")


class TestSaveTrack(unittest.TestCase):
    """save_track verifica la propiedad de la playlist y la existencia de la ficha."""

    def test_new_track_saved_successfully(self):
        sql = MagicMock()
        catalog = MagicMock()
        catalog.exists.return_value = True
        sql.save_track.return_value = (1, True)

        result = discovery.save_track(_profile(), sql, catalog, "pl-ana-demo", "c-cream")

        self.assertTrue(result.created)
        self.assertEqual(result.position, 1)
        self.assertEqual(result.songId, "c-cream")
        sql.owned_playlist.assert_called_once_with("p-ana-main", "pl-ana-demo")

    def test_already_saved_track_returns_created_false(self):
        sql = MagicMock()
        catalog = MagicMock()
        catalog.exists.return_value = True
        sql.save_track.return_value = (1, False)

        result = discovery.save_track(_profile(), sql, catalog, "pl-ana-demo", "c-cream")

        self.assertFalse(result.created)
        self.assertEqual(result.position, 1)

    def test_song_not_in_catalog_raises_404(self):
        sql = MagicMock()
        catalog = MagicMock()
        catalog.exists.return_value = False

        with self.assertRaises(ApiError) as ctx:
            discovery.save_track(_profile(), sql, catalog, "pl-ana-demo", "c-ghost")

        self.assertEqual(ctx.exception.status, 404)
        self.assertEqual(ctx.exception.code, "song_not_found")
        sql.save_track.assert_not_called()

    def test_unowned_playlist_propagates_404(self):
        sql = MagicMock()
        catalog = MagicMock()
        sql.owned_playlist.side_effect = ApiError(404, "playlist_not_found", "No encontramos.")

        with self.assertRaises(ApiError) as ctx:
            discovery.save_track(_profile(), sql, catalog, "pl-ajena", "c-cream")

        self.assertEqual(ctx.exception.status, 404)
        catalog.exists.assert_not_called()
