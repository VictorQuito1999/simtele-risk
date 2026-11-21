import os
import sys
import json
import base64
import urllib.request
import urllib.error
import collections.abc
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'simtele.db')

class TursoRow(collections.abc.Mapping):
    """Representa una fila compatible con sqlite3.Row (acceso por clave y por índice)."""
    def __init__(self, cols, values):
        self._cols = cols
        self._values = values
        self._map = dict(zip(cols, values))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._map[key]

    def __iter__(self):
        return iter(self._cols)

    def __len__(self):
        return len(self._cols)

    def get(self, key, default=None):
        return self._map.get(key, default)

    def keys(self):
        return self._cols

    def values(self):
        return self._values

    def items(self):
        return self._map.items()

    def __repr__(self):
        return f"TursoRow({self._map})"


def _to_hrana_arg(val):
    if val is None:
        return {"type": "null"}
    elif isinstance(val, bool):
        return {"type": "integer", "value": "1" if val else "0"}
    elif isinstance(val, int):
        return {"type": "integer", "value": str(val)}
    elif isinstance(val, float):
        return {"type": "float", "value": val}
    elif isinstance(val, (bytes, bytearray)):
        return {"type": "blob", "base64": base64.b64encode(val).decode("ascii")}
    else:
        try:
            import numpy as np
            if isinstance(val, (np.floating, float)):
                return {"type": "float", "value": float(val)}
            if isinstance(val, (np.integer, int)):
                return {"type": "integer", "value": str(int(val))}
        except ImportError:
            pass
        return {"type": "text", "value": str(val)}


def _from_hrana_val(obj):
    if not isinstance(obj, dict):
        return obj
    t = obj.get("type")
    v = obj.get("value")
    if t == "null":
        return None
    elif t == "integer":
        return int(v) if v is not None else None
    elif t == "float":
        return float(v) if v is not None else None
    elif t in ("text", "string"):
        return str(v) if v is not None else ""
    elif t == "blob":
        return base64.b64decode(obj.get("base64", ""))
    return v


class TursoCursor:
    def __init__(self, cols, rows, last_insert_rowid=None):
        self._cols = cols
        self._rows = [TursoRow(cols, row) for row in rows]
        self._idx = 0
        self.lastrowid = last_insert_rowid

    def fetchone(self):
        if self._idx < len(self._rows):
            r = self._rows[self._idx]
            self._idx += 1
            return r
        return None

    def fetchall(self):
        r = self._rows[self._idx:]
        self._idx = len(self._rows)
        return r

    def __iter__(self):
        return iter(self.fetchall())


class TursoConnection:
    def __init__(self, url, auth_token):
        clean_url = url.strip()
        if clean_url.startswith("libsql://"):
            clean_url = "https://" + clean_url[9:]
        elif clean_url.startswith("http://"):
            clean_url = "https://" + clean_url[7:]
        elif not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url

        self.endpoint = clean_url.rstrip("/") + "/v2/pipeline"
        self.auth_token = auth_token.strip()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def _send_pipeline(self, requests_payload):
        payload = json.dumps({"requests": requests_payload}).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "User-Agent": "simtele-risk-turso/1.0"
        }
        req = urllib.request.Request(self.endpoint, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Error de Turso HTTP {e.code}: {err_body}")

    def execute(self, sql, params=()):
        args = [_to_hrana_arg(p) for p in params]
        requests_payload = [
            {
                "type": "execute",
                "stmt": {
                    "sql": sql,
                    "args": args
                }
            },
            {"type": "close"}
        ]
        data = self._send_pipeline(requests_payload)
        results = data.get("results", [])
        if not results:
            return TursoCursor([], [])

        step = results[0]
        if step.get("type") == "error":
            raise RuntimeError(f"Error SQL en Turso: {step.get('error', {}).get('message', 'Desconocido')}")

        result_data = step.get("response", {}).get("result", {})
        raw_cols = result_data.get("cols", [])
        cols = [c["name"] for c in raw_cols]
        raw_rows = result_data.get("rows", [])

        unwrapped_rows = []
        for r in raw_rows:
            unwrapped_rows.append([_from_hrana_val(cell) for cell in r])

        last_id = result_data.get("last_insert_rowid")
        return TursoCursor(cols, unwrapped_rows, last_insert_rowid=last_id)

    def executemany(self, sql, params_list):
        if not params_list:
            return
        requests_payload = []
        for params in params_list:
            args = [_to_hrana_arg(p) for p in params]
            requests_payload.append({
                "type": "execute",
                "stmt": {"sql": sql, "args": args}
            })
        requests_payload.append({"type": "close"})
        data = self._send_pipeline(requests_payload)
        results = data.get("results", [])
        for r in results:
            if r.get("type") == "error":
                raise RuntimeError(f"Error en executemany de Turso: {r.get('error', {}).get('message')}")

    def executescript(self, sql_script):
        statements = [s.strip() for s in sql_script.split(";") if s.strip()]
        if not statements:
            return
        requests_payload = []
        for stmt in statements:
            requests_payload.append({
                "type": "execute",
                "stmt": {"sql": stmt}
            })
        requests_payload.append({"type": "close"})
        self._send_pipeline(requests_payload)


def get_db():
    turso_url = os.environ.get("TURSO_DATABASE_URL")
    turso_token = os.environ.get("TURSO_AUTH_TOKEN")

    if turso_url and turso_token:
        return TursoConnection(turso_url, turso_token)

    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c
