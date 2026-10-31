"""Dependency-free local HTTP application for the Genshin growth database."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

from planner import get_connection, list_characters, calculate_plan, set_inventory


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"


class Handler(BaseHTTPRequestHandler):
    def character_image(self, path):
        # An explicit allowlist; never translate arbitrary URL paths to files.
        match = re.fullmatch(r'/images/characters/(manifest\.json|placeholder\.svg|[0-9]{8}(?:-avatar)?\.webp)', path)
        if not match:
            return self.send_json({"error": "Not found"}, 404)
        directory = (STATIC / 'images' / 'characters').resolve()
        target = (directory / match[1]).resolve()
        if target.parent != directory or not target.is_file():
            return self.send_json({"error": "Not found"}, 404)
        try:
            raw = target.read_bytes()
        except OSError:
            return self.send_json({"error": "Not found"}, 404)
        mime = {'.webp': 'image/webp', '.svg': 'image/svg+xml', '.json': 'application/json; charset=utf-8'}[target.suffix]
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-cache' if target.suffix == '.json' else 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(raw)

    def send_json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def static_file(self, name, mime):
        raw = (STATIC / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/images/'):
            return self.character_image(parsed.path)
        if parsed.path in ("/", "/index.html"):
            return self.static_file("index.html", "text/html; charset=utf-8")
        if parsed.path == "/style.css":
            return self.static_file("style.css", "text/css; charset=utf-8")
        if parsed.path == "/app.js":
            return self.static_file("app.js", "text/javascript; charset=utf-8")
        if parsed.path == "/api/health":
            return self.send_json({"ok": True, "service": "Genshin Growth"})
        if parsed.path not in ("/api/characters", "/api/plan", "/api/stats"):
            return self.send_json({"error": "Not found"}, 404)
        try:
            with get_connection() as conn:
                if parsed.path == "/api/characters":
                    return self.send_json(list_characters(conn))
                if parsed.path == "/api/stats":
                    return self.send_json({
                        "characters":conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0],
                        "materials":conn.execute("SELECT COUNT(*) FROM materials").fetchone()[0],
                        "ascension_rows":conn.execute("SELECT COUNT(*) FROM ascension_requirements").fetchone()[0],
                        "talent_rows":conn.execute("SELECT COUNT(*) FROM talent_requirements").fetchone()[0],
                        "revision":conn.execute("SELECT substr(revision,1,10) FROM data_sources WHERE source_name='genshin-db'").fetchone()[0],
                    })
                params = parse_qs(parsed.query)

                def number(key, default):
                    return int(params.get(key, [str(default)])[0])

                result = calculate_plan(
                    conn, number("character_id", 10000023),
                    number("from_phase", 0), number("to_phase", 4),
                    {k:(number(f"{k}_from",1), number(f"{k}_to",d))
                     for k,d in [("attack",1),("skill",4),("burst",6)]},
                )
                return self.send_json(result)
        except (ValueError, TypeError) as exc:
            return self.send_json({"error":str(exc)}, 400)
        except Exception as exc:
            print("GET failure:", exc)
            return self.send_json({"error":"Server error"},500)

    def do_POST(self):
        if urlparse(self.path).path != "/api/inventory":
            return self.send_json({"error": "Not found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not (0 < length < 4096):
                raise ValueError("请求数据长度不合法")
            body = json.loads(self.rfile.read(length))
            with get_connection() as conn:
                result = set_inventory(conn, body["material_id"], body["quantity"])
            return self.send_json({"ok":True,"quantity":result})
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return self.send_json({"error":str(exc)},400)
        except Exception as exc:
            print("POST failure:", exc)
            return self.send_json({"error":"Server error"},500)

    def log_message(self, format, *args):
        if not self.path.startswith("/api/health"):
            super().log_message(format,*args)


def main():
    parser = argparse.ArgumentParser(description="Genshin Growth SQLite Demo")
    parser.add_argument("--port",type=int,default=8765)
    args = parser.parse_args()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    server = ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    print(f"原神养成数据库已启动：{count} 位角色")
    print(f"在浏览器打开 http://127.0.0.1:{args.port} （Ctrl+C 停止）", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
