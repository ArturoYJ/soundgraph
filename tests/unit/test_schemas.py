"""
Pruebas unitarias de los modelos Pydantic (backend/schemas.py).

Cubren validación de entrada sin necesidad de bases de datos ni red.
Verifican los invariantes más importantes:
- Login: longitud de código, formato de profileId.
- PlaylistInput: strip de whitespace, longitud mínima.
- NoteUpdate: límites de notas, strip de texto y fuente.
- TrackOrder: lista de IDs válidos.
- Song / Editorial / Credit / Note: construcción correcta.
"""

import unittest

import pytest
from pydantic import ValidationError

from backend.schemas import (
    Credit, Editorial, Login, Note, NoteUpdate, PlaylistInput,
    Profile, Song, SongSummary, TrackOrder,
)


class TestLogin(unittest.TestCase):
    def test_valid_login(self):
        login = Login(profileId="p-ana-main", code="secret123")
        self.assertEqual(login.profileId, "p-ana-main")

    def test_empty_code_rejected(self):
        with self.assertRaises(ValidationError):
            Login(profileId="p-ana-main", code="")

    def test_code_too_long_rejected(self):
        with self.assertRaises(ValidationError):
            Login(profileId="p-ana-main", code="x" * 129)

    def test_invalid_profile_id_format_rejected(self):
        # El profileId debe empezar con letra o dígito
        with self.assertRaises(ValidationError):
            Login(profileId="-invalid", code="ok")

    def test_extra_fields_rejected(self):
        with self.assertRaises(ValidationError):
            Login(profileId="p-ana-main", code="ok", extra="no")


class TestPlaylistInput(unittest.TestCase):
    def test_valid_name(self):
        p = PlaylistInput(name="Rock clásico")
        self.assertEqual(p.name, "Rock clásico")

    def test_whitespace_stripped(self):
        p = PlaylistInput(name="  Rock clásico  ")
        self.assertEqual(p.name, "Rock clásico")

    def test_empty_name_rejected(self):
        with self.assertRaises(ValidationError):
            PlaylistInput(name="")

    def test_whitespace_only_rejected(self):
        with self.assertRaises(ValidationError):
            PlaylistInput(name="   ")

    def test_name_at_max_length_accepted(self):
        PlaylistInput(name="x" * 100)

    def test_name_exceeds_max_length_rejected(self):
        with self.assertRaises(ValidationError):
            PlaylistInput(name="x" * 101)


class TestNoteUpdate(unittest.TestCase):
    def test_valid_single_note(self):
        nu = NoteUpdate(notes=[{"text": "Mi nota", "source": "Referencia"}])
        self.assertEqual(len(nu.notes), 1)
        self.assertEqual(nu.notes[0].text, "Mi nota")

    def test_empty_notes_list_rejected(self):
        with self.assertRaises(ValidationError):
            NoteUpdate(notes=[])

    def test_exceeds_twenty_notes_rejected(self):
        notes = [{"text": "t", "source": "s"}] * 21
        with self.assertRaises(ValidationError):
            NoteUpdate(notes=notes)

    def test_note_text_stripped(self):
        nu = NoteUpdate(notes=[{"text": "  texto  ", "source": "fuente"}])
        self.assertEqual(nu.notes[0].text, "texto")

    def test_note_source_stripped(self):
        nu = NoteUpdate(notes=[{"text": "texto", "source": "  fuente  "}])
        self.assertEqual(nu.notes[0].source, "fuente")

    def test_empty_text_after_strip_rejected(self):
        with self.assertRaises(ValidationError):
            NoteUpdate(notes=[{"text": "   ", "source": "ok"}])

    def test_note_extra_fields_rejected(self):
        with self.assertRaises(ValidationError):
            NoteUpdate(notes=[{"text": "ok", "source": "ok", "extra": "no"}])


class TestTrackOrder(unittest.TestCase):
    def test_valid_order(self):
        to = TrackOrder(songIds=["c-cream", "c-soWhat"])
        self.assertEqual(to.songIds[0], "c-cream")

    def test_empty_list_accepted(self):
        # max_length=1000 pero min no está restringido; lista vacía es válida en el schema
        to = TrackOrder(songIds=[])
        self.assertEqual(to.songIds, [])

    def test_exceeds_1000_rejected(self):
        with self.assertRaises(ValidationError):
            TrackOrder(songIds=["c-x"] * 1001)

    def test_invalid_song_id_format_rejected(self):
        with self.assertRaises(ValidationError):
            TrackOrder(songIds=["-invalid"])


class TestSongConstruction(unittest.TestCase):
    def test_song_with_editorial(self):
        song = Song(
            songId="c-cream",
            title="C.R.E.A.M.",
            editorial=Editorial(
                credits=[Credit(name="Wu-Tang Clan", role="Artist")],
                notes=[Note(text="Clásico", source="wikipedia.org")],
            ),
        )
        self.assertEqual(song.songId, "c-cream")
        self.assertEqual(song.editorial.credits[0].name, "Wu-Tang Clan")
        self.assertEqual(song.editorial.notes[0].text, "Clásico")

    def test_editorial_with_empty_sections(self):
        editorial = Editorial()
        self.assertEqual(editorial.credits, [])
        self.assertEqual(editorial.notes, [])


class TestProfile(unittest.TestCase):
    def test_listener_role(self):
        p = Profile(profileId="p-ana-main", displayName="Ana", role="listener")
        self.assertEqual(p.role, "listener")

    def test_editor_role(self):
        p = Profile(profileId="p-editor", displayName="Editor", role="editor")
        self.assertEqual(p.role, "editor")

    def test_invalid_role_rejected(self):
        with self.assertRaises(ValidationError):
            Profile(profileId="p-x", displayName="X", role="admin")
