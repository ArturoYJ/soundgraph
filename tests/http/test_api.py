"""Real HTTP checks. Run only with an isolated soundgraph-test API and its seeded volumes."""

import http.cookiejar
import json
import subprocess
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "http://127.0.0.1:18080"
BASE = "/api/v1"
ANA = "/playlists/pl-ana-demo"
SQL_COMPOSE = ("docker", "compose", "-p", "soundgraph-test")


def local_codes():
    return dict(line.strip().split("=", 1) for line in (ROOT / ".env.demo").read_text().splitlines()
                if line.strip() and not line.startswith("#"))


class Client:
    def __init__(self):
        self.cookies = http.cookiejar.CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookies))

    def send(self, method, path, payload=None, headers=None):
        params = {"Origin": ORIGIN, **(headers or {})}
        body = None
        if payload is not None:
            params["Content-Type"] = "application/json"
            body = json.dumps(payload).encode()
        try:
            with self.opener.open(Request(ORIGIN + path, body, params, method=method), timeout=15) as result:
                status, raw, hdr = result.status, result.read(), result.headers
        except HTTPError as error:
            with error:
                status, raw, hdr = error.code, error.read(), error.headers
        if not raw:
            return status, None, hdr
        return status, json.loads(raw) if hdr.get_content_type() == "application/json" else raw.decode(), hdr


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        container = subprocess.check_output((*SQL_COMPOSE, "ps", "-q", "api"), cwd=ROOT, text=True).strip()
        if not container or "\n" in container:
            raise RuntimeError("Inicia un único contenedor api en soundgraph-test antes de probar.")
        bindings = json.loads(subprocess.check_output(
            ("docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", container),
            cwd=ROOT, text=True,
        ))
        if bindings.get("8000/tcp") != [{"HostIp": "127.0.0.1", "HostPort": "18080"}]:
            raise RuntimeError("soundgraph-test no está publicado solo en 127.0.0.1:18080.")
        cls.codes = local_codes()

    def login(self, profile="p-ana-main", code="DEMO_CODE_ANA"):
        client = Client()
        status, body, headers = client.send(
            "POST", BASE + "/demo/sessions", {"profileId": profile, "code": self.codes[code]}
        )
        self.assertEqual(status, 201, body)
        self.assertEqual(body["profileId"], profile)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=strict", headers["Set-Cookie"])
        return client

    def test_00_same_origin_frontend(self):
        client = Client()
        status, html, headers = client.send("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn('lang="es"', html)
        self.assertIn('src="/assets/app.js"', html)
        self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        for asset in ("app.js", "app.css", "mark.svg"):
            with self.subTest(asset=asset):
                self.assertEqual(client.send("GET", "/assets/" + asset)[0], 200)
        for path in ("/.env.demo", "/assets/.env.demo", "/assets/%2e%2e/.env.demo"):
            with self.subTest(path=path):
                self.assertEqual(client.send("GET", path)[0], 404)
        self.assertNotIn("/", client.send("GET", "/openapi.json")[1]["paths"])

    def test_01_openapi_and_readiness(self):
        client = Client()
        self.assertEqual(client.send("GET", "/health/ready")[:2], (200, {"status": "ok"}))
        self.assertIn("Swagger UI", client.send("GET", "/docs")[1])
        status, schema, _ = client.send("GET", "/openapi.json")
        self.assertEqual(status, 200)
        self.assertIn(BASE + "/recommendations", schema["paths"])
        self.assertEqual(set(schema["paths"][BASE + "/playlists/{playlistId}/tracks/{songId}"]["put"]
                             ["responses"]) & {"200", "201", "503"}, {"200", "201", "503"})
        self.assertFalse(schema["paths"][BASE + "/demo/sessions"]["post"].get("security"))

    def test_02_session_denied_cross_origin_and_revoked(self):
        client = Client()
        status, body, _ = client.send("GET", BASE + "/recommendations")
        self.assertEqual((status, body["code"]), (401, "session_required"))
        status, body, _ = client.send("POST", BASE + "/demo/sessions", {"profileId": "p-ana-main", "code": "wrong"})
        self.assertEqual((status, body["code"]), (401, "invalid_credentials"))
        client = self.login()
        token = next(iter(client.cookies)).value
        self.assertEqual(client.send("GET", BASE + "/demo/sessions/current")[1]["profileId"], "p-ana-main")
        status, body, _ = client.send("POST", BASE + "/playlists", {"name": "No crear"},
                                      {"Origin": "http://localhost:18081"})
        self.assertEqual((status, body["code"]), (403, "invalid_origin"))
        self.assertEqual(client.send("DELETE", BASE + "/demo/sessions/current")[0], 204)
        self.assertEqual(Client().send("GET", BASE + "/demo/sessions/current",
                                      headers={"Cookie": "soundgraph_session=" + token})[0], 401)

    def test_03_recommendation_and_empty_profile(self):
        anna = self.login()
        status, body, _ = anna.send("GET", BASE + "/recommendations")
        self.assertEqual(status, 200)
        self.assertFalse(body["partial"])
        self.assertEqual([(row["song"]["title"], row["affinity"]) for row in body["items"]], [("C.R.E.A.M.", 1)])
        new = self.login("p-new", "DEMO_CODE_NEW")
        self.assertEqual(new.send("GET", BASE + "/recommendations")[:2], (200, {"items": [], "partial": False}))
        self.assertEqual(new.send("GET", BASE + ANA)[0], 404)
        self.assertEqual(new.send("PUT", BASE + ANA + "/tracks/c-cream")[0], 404)

    def test_04_playlist_concurrency_order_and_crud(self):
        client = self.login()
        status, body, _ = client.send("POST", BASE + "/playlists", {"name": "Prueba efímera"})
        self.assertEqual(status, 201, body)
        route = BASE + "/playlists/" + body["playlistId"]
        cookie = "soundgraph_session=" + next(iter(client.cookies)).value
        try:
            self.assertEqual(client.send("PATCH", route, {"name": "  Renombrada  "})[1]["name"], "Renombrada")
            def add_cream(_):
                return Client().send("PUT", route + "/tracks/c-cream", headers={"Cookie": cookie})
            with ThreadPoolExecutor(max_workers=2) as threads:
                outcomes = list(threads.map(add_cream, range(2)))
            self.assertEqual(sorted(outcome[0] for outcome in outcomes), [200, 201])
            self.assertEqual({outcome[1]["position"] for outcome in outcomes}, {1})
            self.assertEqual(client.send("PUT", route + "/tracks/c-soWhat")[0], 201)
            old = client.send("GET", route)[1]
            self.assertEqual([row["songId"] for row in old["tracks"]], ["c-cream", "c-soWhat"])
            self.assertEqual(client.send("PUT", route + "/track-order", {"songIds": ["c-cream"]})[0], 422)
            self.assertEqual(client.send("GET", route)[1], old)
            self.assertEqual(client.send("PUT", route + "/track-order",
                                         {"songIds": ["c-soWhat", "c-cream"]})[0], 204)
            self.assertEqual([row["songId"] for row in client.send("GET", route)[1]["tracks"]],
                             ["c-soWhat", "c-cream"])
            self.assertEqual(client.send("DELETE", route + "/tracks/c-soWhat")[0], 204)
            self.assertEqual(client.send("GET", route)[1]["tracks"][0]["position"], 1)
        finally:
            self.assertEqual(client.send("DELETE", route)[0], 204)
        self.assertEqual(client.send("GET", route)[0], 404)

    def test_05_editor_updates_only_notes(self):
        listener = self.login()
        editor = self.login("p-editor", "DEMO_CODE_EDITOR")
        route = BASE + "/songs/c-cream/editorial"
        original = listener.send("GET", BASE + "/recommendations")[1]["items"][0]
        data = {"notes": [{"text": "Nota de la prueba HTTP", "source": "Prueba aislada"}]}
        self.assertEqual(listener.send("PATCH", route, data)[0], 403)
        self.assertEqual(editor.send("PATCH", route, {"notes": [{"text": "", "source": "x"}]})[0], 422)
        try:
            self.assertEqual(editor.send("PATCH", route, data)[0], 200)
            updated = listener.send("GET", BASE + "/recommendations")[1]["items"][0]
            self.assertEqual(updated["affinity"], original["affinity"])
            self.assertEqual(updated["song"]["editorial"]["credits"], original["song"]["editorial"]["credits"])
            self.assertEqual(updated["song"]["editorial"]["notes"], data["notes"])
        finally:
            editor.send("PATCH", route, {"notes": original["song"]["editorial"]["notes"]})

    def test_06_partial_recommendation_and_orphan_playlist(self):
        client = self.login()
        status, body, _ = client.send("POST", BASE + "/playlists", {"name": "Ficha ausente"})
        self.assertEqual(status, 201, body)
        route = BASE + "/playlists/" + body["playlistId"]
        try:
            self.assertEqual(client.send("PUT", route + "/tracks/c-cream")[0], 201)
            subprocess.run((*SQL_COMPOSE, "run", "--rm", "--no-deps", "tools", "python", "-c",
                            "from scripts.storage import create_mongo_client\n"
                            "with create_mongo_client() as m:\n"
                            "    m.soundgraph.songs.delete_one({'_id':'c-cream'})"),
                           cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(client.send("GET", BASE + "/recommendations")[:2],
                             (200, {"items": [], "partial": True}))
            self.assertIsNone(client.send("GET", route)[1]["tracks"][0]["song"])
            self.assertEqual(client.send("PUT", route + "/tracks/c-cream")[1]["code"], "song_not_found")
        finally:
            subprocess.run((*SQL_COMPOSE, "run", "--rm", "--no-deps", "tools"),
                           cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(client.send("DELETE", route)[0], 204)

    def test_07_graph_failure_is_not_empty_and_recovers(self):
        client = self.login()
        subprocess.run((*SQL_COMPOSE, "stop", "neo4j"), cwd=ROOT, check=True, capture_output=True)
        try:
            status, body, _ = client.send("GET", BASE + "/recommendations")
            self.assertEqual((status, body["code"]), (503, "service_unavailable"))
            self.assertEqual(client.send("GET", "/health/ready")[0], 503)
        finally:
            subprocess.run((*SQL_COMPOSE, "up", "-d", "--wait", "--wait-timeout", "100", "neo4j"),
                           cwd=ROOT, check=True, capture_output=True)
        self.assertEqual(client.send("GET", BASE + "/recommendations")[1]["items"][0]["song"]["songId"], "c-cream")


if __name__ == "__main__":
    unittest.main(verbosity=2)
