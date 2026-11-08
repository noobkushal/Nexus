"""NEXUS Windows companion: authenticated, loopback-only workspace bridge."""
from __future__ import annotations
import hmac, json, os, secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

VERSION = "0.1.0"
HOST = "127.0.0.1"
PORT = int(os.environ.get("NEXUS_COMPANION_PORT", "8765"))
TOKEN = os.environ.get("NEXUS_COMPANION_TOKEN", "")
WORKSPACE = Path(os.environ.get("NEXUS_WORKSPACE_ROOT", Path.cwd())).expanduser().resolve()
MAX_BYTES = 1_000_000
ALLOWED_SUFFIXES = {".txt", ".md", ".json", ".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".html", ".yml", ".yaml", ".toml", ".sql", ".sh", ".ps1"}
DENIED_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519", "credentials.json", "secrets.json", "companion.token"}
ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}


def resolve_workspace_path(relative: str) -> Path:
    if not relative or "\x00" in relative:
        raise ValueError("A non-empty relative path is required.")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("Absolute paths and parent traversal are not allowed.")
    resolved = (WORKSPACE / candidate).resolve()
    if resolved != WORKSPACE and WORKSPACE not in resolved.parents:
        raise ValueError("Path escapes the configured workspace.")
    return resolved


def is_allowed_file(path: Path) -> bool:
    name = path.name.lower()
    if name in DENIED_NAMES or name.startswith(".env") or path.name.startswith("."):
        return False
    return path.suffix.lower() in ALLOWED_SUFFIXES


class Handler(BaseHTTPRequestHandler):
    server_version = "NEXUS-Companion/0.1"

    def log_message(self, fmt, *args):
        print("NEXUS companion:", fmt % args)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def origin_allowed(self):
        origin = self.headers.get("Origin")
        return not origin or origin in ALLOWED_ORIGINS

    def authorized(self):
        supplied = self.headers.get("Authorization", "")
        return bool(TOKEN) and hmac.compare_digest(supplied, "Bearer " + TOKEN)

    def guard(self):
        if not self.origin_allowed():
            self.send_json(403, {"error": "origin_not_allowed"})
            return False
        if not self.authorized():
            self.send_json(401, {"error": "unauthorized"})
            return False
        return True

    def do_OPTIONS(self):
        if not self.origin_allowed():
            self.send_json(403, {"error": "origin_not_allowed"})
            return
        origin = self.headers.get("Origin", "")
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-NEXUS-LOCAL-CONFIRM")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if not self.guard():
            return
        parsed = urlsplit(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/v1/status":
            self.send_json(200, {"name": "NEXUS Windows Companion", "version": VERSION, "status": "ready",
                "workspace": str(WORKSPACE), "capabilities": ["workspace.list", "workspace.read", "workspace.write"],
                "execution": "disabled", "remote_access": "disabled"})
            return
        if parsed.path == "/v1/files":
            relative = params.get("path", [""])[0]
            try:
                directory = resolve_workspace_path(relative) if relative else WORKSPACE
                if not directory.is_dir():
                    self.send_json(404, {"error": "directory_not_found"})
                    return
                entries = []
                for child in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
                    try:
                        resolved = child.resolve()
                        if resolved != WORKSPACE and WORKSPACE not in resolved.parents:
                            continue
                        if child.name.startswith(".") or child.name.lower() in DENIED_NAMES:
                            continue
                        if child.is_dir():
                            entries.append({"name": child.name, "type": "directory"})
                        elif child.is_file() and is_allowed_file(child):
                            entries.append({"name": child.name, "type": "file", "size": child.stat().st_size})
                    except OSError:
                        continue
                self.send_json(200, {"path": relative, "entries": entries})
            except ValueError as exc:
                self.send_json(400, {"error": str(exc)})
            return
        if parsed.path == "/v1/files/read":
            relative = params.get("path", [""])[0]
            try:
                target = resolve_workspace_path(relative)
                if not target.is_file() or not is_allowed_file(target):
                    self.send_json(404, {"error": "file_not_found_or_type_not_allowed"})
                    return
                if target.stat().st_size > MAX_BYTES:
                    self.send_json(413, {"error": "file_too_large"})
                    return
                self.send_json(200, {"path": relative, "content": target.read_text(encoding="utf-8")})
            except (ValueError, UnicodeDecodeError) as exc:
                self.send_json(400, {"error": str(exc)})
            except OSError:
                self.send_json(404, {"error": "file_not_found"})
            return
        self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        if not self.guard():
            return
        if self.path != "/v1/files/write":
            self.send_json(404, {"error": "not_found"})
            return
        if self.headers.get("X-NEXUS-LOCAL-CONFIRM") != "true":
            self.send_json(403, {"error": "explicit_local_confirmation_required"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "invalid_content_length"})
            return
        if length <= 0 or length > MAX_BYTES + 8192:
            self.send_json(413, {"error": "request_too_large"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            relative, content = payload["path"], payload["content"]
            if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_BYTES:
                raise ValueError("Content must be UTF-8 text no larger than 1 MB.")
            target = resolve_workspace_path(relative)
            if not is_allowed_file(target):
                self.send_json(400, {"error": "file_type_not_allowed"})
                return
            if not target.parent.is_dir():
                self.send_json(400, {"error": "parent_directory_must_exist"})
                return
            parent = target.parent.resolve()
            if parent != WORKSPACE and WORKSPACE not in parent.parents:
                self.send_json(400, {"error": "path_escapes_workspace"})
                return
            temp = target.with_name(target.name + ".nexus-tmp-" + secrets.token_hex(6))
            temp.write_text(content, encoding="utf-8", newline="")
            os.replace(temp, target)
            self.send_json(200, {"saved": True, "path": relative, "bytes": len(content.encode("utf-8"))})
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc)})
        except OSError:
            self.send_json(500, {"error": "workspace_write_failed"})


def main():
    if len(TOKEN) < 32:
        raise SystemExit("Set NEXUS_COMPANION_TOKEN to a random secret of at least 32 characters.")
    if not WORKSPACE.is_dir():
        raise SystemExit("Workspace directory does not exist: " + str(WORKSPACE))
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    print("NEXUS companion listening on http://" + HOST + ":" + str(PORT))
    print("Workspace: " + str(WORKSPACE))
    print("No shell execution or remote network listener is enabled.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping NEXUS companion...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
