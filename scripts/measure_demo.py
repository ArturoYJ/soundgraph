"""Mide dos rutas de lectura de SoundGraph en el entorno aislado de medición."""

import argparse
import csv
from http.client import HTTPConnection
from http.cookies import SimpleCookie
import json
from math import ceil
import os
from pathlib import Path
from statistics import median
import subprocess
from time import perf_counter_ns


ROOT = Path(__file__).resolve().parents[1]
PROJECT = "soundgraph-bench"
HOST, PORT = "127.0.0.1", 18081
BASE = "/api/v1"
ORIGIN = f"http://{HOST}:{PORT}"
SESSION = BASE + "/demo/sessions"
SCENARIOS = (
    ("recommendations", BASE + "/recommendations?limit=10"),
    ("playlists", BASE + "/playlists"),
)
WARMUP, COUNT = 10, 100


def verify_target():
    env = dict(os.environ, SOUNDGRAPH_API_PORT=str(PORT))
    compose = ["docker", "compose", "-p", PROJECT, "ps", "-q", "api"]
    ids = subprocess.check_output(compose, cwd=ROOT, env=env, text=True).split()
    if len(ids) != 1:
        raise RuntimeError(f"Debe estar levantada una sola API en {PROJECT}.")
    port = subprocess.check_output(["docker", "port", ids[0], "8000/tcp"], text=True).strip()
    if port != f"{HOST}:{PORT}":
        raise RuntimeError("La API de medición no coincide con el puerto local esperado.")


def request(conn, method, path, headers=None, body=None):
    start = perf_counter_ns()
    conn.request(method, path, body=body, headers=headers or {})
    response = conn.getresponse()
    raw = response.read()
    elapsed_ms = (perf_counter_ns() - start) / 1_000_000
    return response.status, response.headers, json.loads(raw) if raw else None, elapsed_ms


def expected(name, payload):
    if name == "recommendations":
        return payload["partial"] is False and [
            (item["song"]["songId"], item["affinity"]) for item in payload["items"]
        ] == [("c-cream", 1)]
    return payload["items"] == [{"playlistId": "pl-ana-demo", "name": "Para escuchar", "trackCount": 0}]


def measure():
    verify_target()
    code = next(
        line.partition("=")[2] for line in (ROOT / ".env.demo").read_text().splitlines()
        if line.startswith("DEMO_CODE_ANA=")
    )
    conn = HTTPConnection(HOST, PORT, timeout=10)
    try:
        status, headers, _, _ = request(
            conn, "POST", SESSION, {"Content-Type": "application/json", "Origin": ORIGIN},
            json.dumps({"profileId": "p-ana-main", "code": code}),
        )
        if status != 201:
            raise RuntimeError(f"No se pudo iniciar la sesión de medición: HTTP {status}.")
        cookie = SimpleCookie()
        for value in headers.get_all("Set-Cookie", []):
            cookie.load(value)
        auth = {"Cookie": "soundgraph_session=" + cookie["soundgraph_session"].coded_value}
        rows = []
        try:
            for name, path in SCENARIOS:
                for i in range(1, WARMUP + COUNT + 1):
                    status, _, body, ms = request(conn, "GET", path, auth)
                    if status != 200 or not expected(name, body):
                        raise RuntimeError(f"Respuesta inesperada en {name}, intento {i}, HTTP {status}.")
                    if i > WARMUP:
                        rows.append((name, i - WARMUP, status, round(ms, 6)))
        finally:
            if request(conn, "DELETE", SESSION + "/current", dict(auth, Origin=ORIGIN))[0] != 204:
                raise RuntimeError("No se pudo cerrar la sesión de medición.")
    finally:
        conn.close()
    return rows


def summarize(rows):
    result = {}
    for name, _ in SCENARIOS:
        values = sorted(row[3] for row in rows if row[0] == name)
        result[name] = {
            "n": len(values),
            "min_ms": round(values[0], 3),
            "median_ms": round(median(values), 3),
            "p95_ms": round(values[ceil(.95 * len(values)) - 1], 3),
            "max_ms": round(values[-1], 3),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path, help="Archivo nuevo de salida.")
    args = parser.parse_args()
    if args.csv.exists():
        parser.error("La ruta de salida ya existe. Elige un nombre nuevo.")
    rows = measure()
    with args.csv.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("scenario", "sample", "status", "latency_ms"))
        writer.writerows(rows)
    print(json.dumps(summarize(rows), indent=2))


if __name__ == "__main__":
    main()
