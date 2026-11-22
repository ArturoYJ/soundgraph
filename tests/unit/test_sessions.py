"""
Pruebas unitarias del servicio de sesiones (backend/services/sessions.py).

Cubren:
- hash_cookie: formato válido, inválido y None.
- configure_codes: valida longitud mínima y unicidad.
- sign_in: credenciales correctas, incorrectas y perfil inexistente.
- current_profile: token válido, expirado/ausente y formato inválido.

No requieren Docker ni bases de datos reales: todas las dependencias
externas (sql) se reemplazan con mocks.
"""

import hashlib
import unittest
from unittest.mock import MagicMock, patch

from backend.errors import ApiError
from backend.schemas import Login, Profile
from backend.services import sessions


def _mock_profile(profile_id="p-ana-main", role="listener"):
    return Profile(profileId=profile_id, displayName="Ana", role=role)


def _valid_codes():
    return {
        "p-ana-main": "A" * 24,
        "p-sofia": "B" * 24,
        "p-new": "C" * 24,
        "p-editor": "D" * 24,
    }


class TestHashCookie(unittest.TestCase):
    """hash_cookie valida el formato del token antes de calcular el SHA-256."""

    def test_valid_token_returns_sha256(self):
        # 43 chars Base64url → longitud exacta que genera token_urlsafe(32)
        token = "a" * 43
        result = sessions.hash_cookie(token)
        expected = hashlib.sha256(token.encode("ascii")).hexdigest()
        self.assertEqual(result, expected)

    def test_none_returns_none(self):
        self.assertIsNone(sessions.hash_cookie(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(sessions.hash_cookie(""))

    def test_token_too_short_returns_none(self):
        self.assertIsNone(sessions.hash_cookie("x" * 42))

    def test_token_with_invalid_chars_returns_none(self):
        # El patrón exige A-Za-z0-9_- únicamente
        self.assertIsNone(sessions.hash_cookie("!" * 43))

    def test_token_too_long_returns_none(self):
        self.assertIsNone(sessions.hash_cookie("a" * 44))


class TestConfigureCodes(unittest.TestCase):
    """configure_codes rechaza variables de entorno ausentes o repetidas."""

    def test_raises_when_code_is_too_short(self):
        env = {k: "X" * 23 for k in sessions.CREDENTIALS.values()}
        with patch.dict("os.environ", env, clear=False):
            with self.assertRaises(RuntimeError):
                sessions.configure_codes()

    def test_raises_when_codes_are_not_unique(self):
        # Dos perfiles con el mismo código → debe fallar
        env = {k: "SHARED_CODE_VALUE_FOR_TEST" for k in sessions.CREDENTIALS.values()}
        with patch.dict("os.environ", env, clear=False):
            with self.assertRaises(RuntimeError):
                sessions.configure_codes()

    def test_accepts_valid_unique_codes(self):
        env = {v: chr(65 + i) * 24 for i, v in enumerate(sessions.CREDENTIALS.values())}
        with patch.dict("os.environ", env, clear=False):
            codes = sessions.configure_codes()
        self.assertEqual(set(codes.keys()), set(sessions.CREDENTIALS.keys()))
        self.assertEqual(len(set(codes.values())), len(codes))


class TestSignIn(unittest.TestCase):
    """sign_in autentifica o lanza ApiError(401)."""

    def _credentials(self, profile_id, code):
        return Login(profileId=profile_id, code=code)

    def test_valid_credentials_return_profile_and_token(self):
        codes = _valid_codes()
        sql = MagicMock()
        sql.find_profile.return_value = _mock_profile()
        profile, token = sessions.sign_in(
            sql, codes, self._credentials("p-ana-main", codes["p-ana-main"]), previous=None
        )
        self.assertEqual(profile.profileId, "p-ana-main")
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)
        sql.create_session.assert_called_once()

    def test_wrong_code_raises_401(self):
        codes = _valid_codes()
        sql = MagicMock()
        with self.assertRaises(ApiError) as ctx:
            sessions.sign_in(
                sql, codes, self._credentials("p-ana-main", "wrong-code"), previous=None
            )
        self.assertEqual(ctx.exception.status, 401)
        self.assertEqual(ctx.exception.code, "invalid_credentials")
        sql.find_profile.assert_not_called()

    def test_unknown_profile_raises_401(self):
        codes = _valid_codes()
        sql = MagicMock()
        with self.assertRaises(ApiError) as ctx:
            sessions.sign_in(
                sql, codes, self._credentials("p-unknown", "A" * 24), previous=None
            )
        self.assertEqual(ctx.exception.status, 401)

    def test_profile_not_in_db_raises_401(self):
        # El código es correcto pero find_profile devuelve None (perfil eliminado)
        codes = _valid_codes()
        sql = MagicMock()
        sql.find_profile.return_value = None
        with self.assertRaises(ApiError) as ctx:
            sessions.sign_in(
                sql, codes, self._credentials("p-ana-main", codes["p-ana-main"]), previous=None
            )
        self.assertEqual(ctx.exception.status, 401)

    def test_previous_token_is_revoked_on_new_login(self):
        codes = _valid_codes()
        sql = MagicMock()
        sql.find_profile.return_value = _mock_profile()
        previous_token = "p" * 43
        sessions.sign_in(
            sql, codes, self._credentials("p-ana-main", codes["p-ana-main"]),
            previous=previous_token,
        )
        # create_session recibe el hash del previous como cuarto argumento
        args = sql.create_session.call_args[0]
        expected_prev_hash = hashlib.sha256(previous_token.encode("ascii")).hexdigest()
        self.assertEqual(args[3], expected_prev_hash)


class TestCurrentProfile(unittest.TestCase):
    """current_profile resuelve la sesión o lanza ApiError(401)."""

    def test_valid_token_returns_profile(self):
        sql = MagicMock()
        sql.find_session.return_value = _mock_profile()
        token = "v" * 43
        profile = sessions.current_profile(sql, token)
        self.assertEqual(profile.profileId, "p-ana-main")
        expected_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
        sql.find_session.assert_called_once_with(expected_hash)

    def test_expired_or_missing_session_raises_401(self):
        sql = MagicMock()
        sql.find_session.return_value = None
        with self.assertRaises(ApiError) as ctx:
            sessions.current_profile(sql, "v" * 43)
        self.assertEqual(ctx.exception.status, 401)
        self.assertEqual(ctx.exception.code, "session_required")

    def test_none_token_raises_401_without_db_call(self):
        sql = MagicMock()
        with self.assertRaises(ApiError) as ctx:
            sessions.current_profile(sql, None)
        self.assertEqual(ctx.exception.status, 401)
        sql.find_session.assert_not_called()

    def test_malformed_token_raises_401_without_db_call(self):
        sql = MagicMock()
        with self.assertRaises(ApiError):
            sessions.current_profile(sql, "bad-token!")
        sql.find_session.assert_not_called()
