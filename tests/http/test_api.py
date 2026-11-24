"""Real HTTP checks. Run only with an isolated soundgraph-test API and its seeded volumes."""

import http.cookiejar
import json
import subprocess
import time
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
        data = {"notes": [
            {"text": "Nota de la prueba HTTP", "source": "Prueba aislada"},
            *original["song"]["editorial"]["notes"],
        ]}
        self.assertEqual(listener.send("PATCH", route, data)[0], 403)
        self.assertEqual(editor.send("PATCH", route, {"notes": [{"text": "", "source": "x"}]})[0], 422)
        try:
            self.assertEqual(editor.send("PATCH", route, data)[0], 200)
            updated = listener.send("GET", BASE + "/recommendations")[1]["items"][0]
            self.assertEqual(updated["affinity"], original["affinity"])
            self.assertEqual(updated["song"]["editorial"]["credits"], original["song"]["editorial"]["credits"])
            self.assertEqual(updated["song"]["editorial"]["notes"], data["notes"])
            self.assertEqual(editor.send("GET", route)[1]["editorial"]["notes"], data["notes"])
        finally:
            self.assertEqual(editor.send("PATCH", route, {"notes": original["song"]["editorial"]["notes"]})[0], 200)

    def test_08_editorial_catalog_reads_and_permissions(self):
        list_route = BASE + "/songs"
        detail = BASE + "/songs/c-cream/editorial"
        guest = Client()
        listener = self.login()
        editor = self.login("p-editor", "DEMO_CODE_EDITOR")
        for path in (list_route, detail):
            self.assertEqual(guest.send("GET", path)[0], 401)
            status, data, _ = listener.send("GET", path)
            self.assertEqual((status, data["code"]), (403, "editor_required"))
        status, page, _ = editor.send("GET", list_route + "?limit=1")
        self.assertEqual(status, 200)
        self.assertEqual(len(page["items"]), 1)
        self.assertEqual(set(page["items"][0]), {"songId", "title"})
        self.assertEqual(page["nextAfter"], page["items"][0]["songId"])
        status, tail, _ = editor.send("GET", list_route + "?after=" + page["nextAfter"])
        self.assertEqual(status, 200)
        self.assertIsNone(tail["nextAfter"])
        self.assertEqual(sorted(x["songId"] for x in page["items"] + tail["items"]),
                         ["c-allBlues", "c-cream", "c-soWhat"])
        self.assertEqual(editor.send("GET", list_route + "?limit=51")[0], 422)
        status, song, _ = editor.send("GET", detail)
        self.assertEqual(status, 200)
        self.assertEqual(song["title"], "C.R.E.A.M.")
        self.assertTrue(song["editorial"]["notes"])
        status, body, _ = editor.send("GET", BASE + "/songs/no-existe/editorial")
        self.assertEqual((status, body["code"]), (404, "song_not_found"))

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

    def personal_graph_synced(self, profile_ids):
        subprocess.run((*SQL_COMPOSE, "run", "--rm", "--no-deps", "tools", "python", "-c",
                        "import sys\nfrom scripts.storage import open_stores\n"
                        "with open_stores() as s:\n"
                        "    for pid in sys.argv[1:]:\n"
                        "        assert s.postgres.execute('SELECT graph_pending FROM personal_access WHERE profile_id=%s', (pid,)).fetchone() == (False,)\n"
                        "        rows, _, _ = s.graph.execute_query('MATCH (p:Perfil {profileId: $pid}) RETURN count(p) AS n', pid=pid, database_='neo4j')\n"
                        "        assert rows[0]['n'] == 1\n", *profile_ids), cwd=ROOT, check=True, capture_output=True)

    def clean_personal_profiles(self, profile_ids):
        if not profile_ids:
            return
        subprocess.run((*SQL_COMPOSE, "run", "--rm", "--no-deps", "tools", "python", "-c",
                        "import sys\nfrom scripts.storage import open_stores\n"
                        "with open_stores() as s:\n"
                        "    for pid in sys.argv[1:]:\n"
                        "        s.graph.execute_query('MATCH (p:Perfil {profileId: $pid}) DETACH DELETE p', pid=pid, database_='neo4j')\n"
                        "        with s.postgres.transaction():\n"
                        "            s.postgres.execute('DELETE FROM playlists WHERE owner_id=%s', (pid,))\n"
                        "            s.postgres.execute('DELETE FROM profiles WHERE profile_id=%s', (pid,))\n", *profile_ids),
                       cwd=ROOT, check=True, capture_output=True)

    def test_09_personal_profiles_persist_relogin_and_isolate_playlists(self):
        clients = [Client(), Client()]
        created = []
        try:
            for client in clients:
                status, body, _ = client.send("POST", BASE + "/profiles", {"displayName": "  Lucía  "})
                self.assertEqual(status, 201)
                created.append(body)
                self.assertEqual(body["displayName"], "Lucía")
                self.assertEqual(body["role"], "listener")
                self.assertFalse(body["graphPending"])
            self.assertNotEqual(created[0]["profileId"], created[1]["profileId"])
            self.assertTrue(created[0]["accessCode"] != created[1]["accessCode"], "Los códigos deben ser independientes")
            lists = []
            for client in clients:
                status, body, _ = client.send("POST", BASE + "/playlists", {"name": "Lista personal"})
                self.assertEqual(status, 201)
                lists.append(body["playlistId"])
            route = BASE + "/playlists/" + lists[0]
            for method, path, payload in (
                ("GET", route, None), ("PATCH", route, {"name": "Ajena"}), ("DELETE", route, None),
                ("PUT", route + "/tracks/c-cream", None), ("DELETE", route + "/tracks/c-cream", None),
                ("PUT", route + "/track-order", {"songIds": []}),
            ):
                self.assertEqual(clients[1].send(method, path, payload)[0], 404)
            for client, identity, playlist_id in zip(clients, created, lists):
                status, current, _ = client.send("GET", BASE + "/demo/sessions/current")
                self.assertEqual(status, 200)
                self.assertEqual(current["profileId"], identity["profileId"])
                self.assertNotIn("accessCode", current)
                self.assertEqual(client.send("DELETE", BASE + "/demo/sessions/current")[0], 204)
                self.assertEqual(client.send("GET", BASE + "/playlists")[0], 401)
                status, current, _ = client.send("POST", BASE + "/sessions", {"code": identity["accessCode"]})
                self.assertEqual(status, 201)
                self.assertEqual(current["displayName"], "Lucía")
                self.assertEqual(current["profileId"], identity["profileId"])
                self.assertEqual([p["playlistId"] for p in client.send("GET", BASE + "/playlists")[1]["items"]], [playlist_id])
                self.assertEqual(client.send("GET", BASE + "/songs")[0], 403)
            self.assertEqual(Client().send("POST", BASE + "/sessions", {"code": "Lucía"})[0], 401)
            for payload in ({"displayName": "  "}, {"displayName": "Isaac", "role": "editor"}):
                self.assertEqual(Client().send("POST", BASE + "/profiles", payload)[0], 422)
            self.personal_graph_synced([p["profileId"] for p in created])
        finally:
            self.clean_personal_profiles([p["profileId"] for p in created])

    def test_10_personal_creation_survives_graph_outage_and_reconciles(self):
        client = Client()
        created = None
        try:
            subprocess.run((*SQL_COMPOSE, "stop", "neo4j"), cwd=ROOT, check=True, capture_output=True)
            try:
                status, body, _ = client.send("POST", BASE + "/profiles", {"displayName": "Perfil pendiente"})
                self.assertEqual(status, 201)
                created = body
                self.assertTrue(body["graphPending"])
                self.assertEqual(client.send("GET", BASE + "/demo/sessions/current")[1]["displayName"], "Perfil pendiente")
                status, body, _ = client.send("GET", BASE + "/recommendations")
                self.assertEqual((status, body["code"]), (503, "service_unavailable"))
                self.assertEqual(client.send("DELETE", BASE + "/demo/sessions/current")[0], 204)
                self.assertEqual(client.send("POST", BASE + "/sessions", {"code": created["accessCode"]})[0], 201)
            finally:
                subprocess.run((*SQL_COMPOSE, "up", "-d", "--wait", "--wait-timeout", "100", "neo4j"), cwd=ROOT, check=True, capture_output=True)
            deadline = time.monotonic() + 60
            while client.send("GET", "/health/ready")[0] != 200:
                if time.monotonic() >= deadline:
                    self.fail("Neo4j no recuperó disponibilidad")
                time.sleep(1)
            status, body, _ = client.send("GET", BASE + "/recommendations")
            self.assertEqual((status, body), (200, {"items": [], "partial": False}))
            self.personal_graph_synced([created["profileId"]])
        finally:
            self.clean_personal_profiles([created["profileId"]] if created else [])

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
        deadline = time.monotonic() + 60
        while True:
            status, body, _ = client.send("GET", "/health/ready")
            if status == 200 and body == {"status": "ok"}:
                break
            self.assertEqual(status, 503, (status, body))
            if time.monotonic() >= deadline:
                self.fail(f"La API no recuperó disponibilidad en 60 s: {status}, {body}")
            time.sleep(1)
        status, body, _ = client.send("GET", BASE + "/recommendations")
        self.assertEqual(status, 200, body)
        self.assertEqual(body["items"][0]["song"]["songId"], "c-cream")


if __name__ == "__main__":
    unittest.main(verbosity=2)
