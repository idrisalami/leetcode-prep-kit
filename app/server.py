"""Serve the prep app on 127.0.0.1 only: static files from app/static/ and the JSON API.

    python3 app/server.py [--port N] [--no-open]
"""
from __future__ import annotations

import argparse
import errno
import http.client
import json
import os
import re
import select
import shlex
import signal
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.prep import api, paths as paths_mod  # noqa: E402

DEFAULT_PORT = 8765
LAST_PORT = 8775
HOST = "127.0.0.1"
REQUEST_TIMEOUT_S = 30  # per socket read or write; an SSE stream only writes, so a slow coach is fine
WATCH_POLL_S = 0.1
LOCK_NAME = "server.lock"  # my-prep/app/server.lock: {"pid": int, "port": int} of the live server
LOCK_PROBE_S = 2
DIGITS = re.compile(r"[0-9]+")
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".woff2": "font/woff2",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}
SAFETY = {"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}


def static_file(static_root, url_path):
    """The real path of a regular file inside static_root for this URL path, or None."""
    rel = unquote(url_path)
    if rel == "/":
        rel = "/index.html"
    elif rel.startswith("/static/"):
        rel = rel[len("/static"):]
    if "\x00" in rel or "\\" in rel or ".." in rel.split("/"):
        return None
    root = os.path.realpath(static_root)
    full = os.path.realpath(os.path.join(root, rel.lstrip("/")))
    if not full.startswith(root + os.sep) or not os.path.isfile(full):
        return None
    if os.path.splitext(full)[1].lower() not in CONTENT_TYPES:
        return None
    return full


class Handler(BaseHTTPRequestHandler):
    server_version = "PrepKit"
    sys_version = ""
    protocol_version = "HTTP/1.1"
    timeout = REQUEST_TIMEOUT_S

    def version_string(self):
        return self.server_version

    def log_message(self, fmt, *args):  # quiet: the API logs its own errors
        pass

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def do_PATCH(self):
        self._dispatch("PATCH")

    def _dispatch(self, method):
        parts = urlsplit(self.path)
        if parts.path.startswith("/api/"):
            self._api(method, parts)
        elif method == "GET":
            self._static(parts.path)
        else:
            self._plain(405, b"Method not allowed.\n", {"Allow": "GET"})

    def _refuse(self, status, code, detail):
        self.close_connection = True
        self._send(api.json_response(status, {"error": code, "detail": detail}))

    def _api(self, method, parts):
        app = self.server.app
        query = {k: v[0] for k, v in parse_qs(parts.query).items() if v}
        headers = {k: v for k, v in self.headers.items()}
        if str(self.headers.get("Host", "")).lower() not in app.hosts:
            # refuse before reading a body that may never come
            self.close_connection = True
            self._send(app.handle(method, parts.path, query, headers, b""))
            return
        if self.headers.get("Transfer-Encoding") is not None:
            self._refuse(400, "bad_request", "Transfer-Encoding is not supported; send Content-Length.")
            return
        values = self.headers.get_all("Content-Length") or []
        if len(values) > 1 or (values and not DIGITS.fullmatch(values[0])):
            self._refuse(400, "bad_request", "Bad Content-Length.")
            return
        length = int(values[0]) if values else 0
        if length > api.MAX_BODY:
            self._refuse(413, "too_large", "Request body too large.")
            return
        try:
            body = self.rfile.read(length) if length else b""
        except (socket.timeout, OSError):
            body = None
        if body is None or len(body) < length:  # the client stalled or went away mid-body
            self.close_connection = True
            return
        self._send(app.handle(method, parts.path, query, headers, body))

    def _write(self, status, headers, body):
        """Send a whole response; a client that already left is not an error."""
        try:
            self.send_response(status)
            for k, v in headers.items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except OSError:
            self.close_connection = True

    def _send(self, resp):
        if resp.stream is not None:
            self._send_stream(resp)
        else:
            self._write(resp.status, resp.headers, resp.body or b"")

    def _send_stream(self, resp):
        self.close_connection = True
        done = threading.Event()
        watcher = None
        try:
            self.send_response(resp.status)
            for k, v in resp.headers.items():
                self.send_header(k, v)
            self.send_header("Connection", "close")
            self.end_headers()
            if resp.cancel is not None:
                watcher = threading.Thread(target=self._watch, args=(resp.cancel, done), daemon=True)
                watcher.start()
            for chunk in resp.stream:
                self.wfile.write(chunk)
                self.wfile.flush()
        except OSError:
            if resp.cancel is not None:
                resp.cancel.set()
        finally:
            done.set()
            if watcher is not None:
                watcher.join(timeout=1)
            close = getattr(resp.stream, "close", None)
            if close:
                close()

    def _watch(self, cancel, done):
        """Set cancel as soon as the client closes its end, without waiting for the next write."""
        conn = self.connection
        while not done.is_set():
            try:
                readable, _, _ = select.select([conn], [], [], WATCH_POLL_S)
                if readable and not conn.recv(65536):
                    cancel.set()
                    return
            except (OSError, ValueError):
                cancel.set()
                return

    def _plain(self, status, body, extra=None):
        headers = {"Content-Type": "text/plain; charset=utf-8"}
        headers.update(SAFETY)
        headers.update(extra or {})
        self._write(status, headers, body)

    def _static(self, url_path):
        full = static_file(self.server.paths.static, url_path)
        if full is None:
            self._plain(404, b"Not found.\n")
            return
        with open(full, "rb") as fh:
            data = fh.read()
        headers = {"Content-Type": CONTENT_TYPES[os.path.splitext(full)[1].lower()]}
        headers.update(SAFETY)
        self._write(200, headers, data)


def reuse_address():
    """SO_REUSEADDR lets a restart bind the port while old connections linger (TIME_WAIT). On
    Windows the same option would let a second server share a live port, so it stays off there."""
    return os.name != "nt"


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = reuse_address()

    def server_close(self):
        app = getattr(self, "app", None)
        if app is not None:
            app.shutdown()  # kill live coach groups and remove their folders
        super().server_close()


def make_server(paths, port, coach_cmd=None, host=HOST):
    if host != HOST:
        raise ValueError("The prep app binds to 127.0.0.1 only.")
    # a handler class per server, so one server's settings (the timeout) never leak into another
    httpd = Server((HOST, port), type("Handler", (Handler,), {"timeout": REQUEST_TIMEOUT_S}))
    try:
        httpd.paths = paths
        httpd.app = api.App(paths, httpd.server_address[1], coach_cmd=coach_cmd)
    except Exception:
        httpd.server_close()
        raise
    return httpd


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run the LeetCode prep app on 127.0.0.1.")
    parser.add_argument("--port", type=int, default=None,
                        help="port to use (default %d, or the next free one up to %d)"
                        % (DEFAULT_PORT, LAST_PORT))
    parser.add_argument("--no-open", action="store_true", help="do not open a browser tab")
    args = parser.parse_args(argv)
    args.explicit_port = args.port is not None
    if args.port is None:
        args.port = DEFAULT_PORT
    return args


def coach_command():
    raw = os.environ.get("PREP_COACH_CMD", "").strip()
    return shlex.split(raw) if raw else None


def _lock_path(paths):
    return os.path.join(paths.my_prep, "app", LOCK_NAME)


def _read_lock(paths):
    """(pid, port) from the lock file, or None when it is missing or not of that shape."""
    try:
        with open(_lock_path(paths), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    pid, port = data.get("pid"), data.get("port")
    for value in (pid, port):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            return None
    return pid, port


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _answers(port):
    """True when a prep app answers on this port within LOCK_PROBE_S seconds."""
    conn = http.client.HTTPConnection(HOST, port, timeout=LOCK_PROBE_S)
    try:
        conn.request("GET", "/api/setup/status", headers={"Host": "%s:%d" % (HOST, port)})
        resp = conn.getresponse()
        resp.read()
        return resp.status == 200
    except (OSError, http.client.HTTPException):
        return False
    finally:
        conn.close()


def running_port(paths):
    """The port of another prep app already serving this kit, or None when the lock is stale."""
    lock = _read_lock(paths)
    if lock is None:
        return None
    pid, port = lock
    if not _pid_alive(pid) or not _answers(port):
        return None
    return port


def write_lock(paths, port):
    """Record this process and its port; a stale lock is replaced. A failure is not fatal."""
    path = _lock_path(paths)
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"pid": os.getpid(), "port": port}, fh)
        os.replace(tmp, path)
    except OSError as exc:
        print("Could not write %s: %s" % (path, exc), file=sys.stderr)


def remove_lock(paths, port):
    """Remove the lock file, but only while it still names this process and port."""
    if _read_lock(paths) != (os.getpid(), port):
        return
    try:
        os.remove(_lock_path(paths))
    except OSError:
        pass


def _stop_on_sigterm():
    def stop(signum, frame):
        raise SystemExit(0)
    try:
        signal.signal(signal.SIGTERM, stop)
    except (ValueError, OSError, AttributeError):  # not the main thread, or no SIGTERM here
        pass


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    paths = paths_mod.default()
    if os.path.islink(paths.my_prep):
        print("my-prep/ is a symbolic link. The app needs it to be a real folder inside the kit.",
              file=sys.stderr)
        return 1
    other = running_port(paths)
    if other is not None:
        url = "http://127.0.0.1:%d/" % other
        print("The prep app is already running at %s" % url)
        sys.stdout.flush()
        if not args.no_open:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        return 0
    ports = [args.port] if args.explicit_port else list(range(DEFAULT_PORT, LAST_PORT + 1))
    httpd = None
    for port in ports:
        try:
            httpd = make_server(paths, port, coach_cmd=coach_command())
            break
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
    if httpd is None:
        if args.explicit_port:
            print("Port %d is in use. Pick another with --port N." % args.port, file=sys.stderr)
        else:
            print("Ports %d to %d are all in use. Pick one with --port N."
                  % (DEFAULT_PORT, LAST_PORT), file=sys.stderr)
        return 1
    port = httpd.server_address[1]
    url = "http://127.0.0.1:%d/" % port
    try:
        write_lock(paths, port)
        _stop_on_sigterm()
        for line in httpd.app.startup_lines():
            print(line)
        print("The prep app is running at %s (Ctrl+C to stop)." % url)
        sys.stdout.flush()
        if not args.no_open:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    except SystemExit:
        print("Stopped.")
    finally:
        remove_lock(paths, port)
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
