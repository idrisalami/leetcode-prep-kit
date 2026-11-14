"""The real HTTP server on an ephemeral port, in a thread: static files, guards, SSE."""
from __future__ import annotations

import errno
import http.client
import io
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import threading
import unittest
from unittest import mock

from app import server
from app.prep import paths
from app.tests.kit import make_kit
from app.tests.test_coach import pid_alive

FAKE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_coach.py")
REAL = paths.default()


class ServerCase(unittest.TestCase):
    def setUp(self):
        kit = make_kit(self)
        shutil.copyfile(os.path.join(REAL.data, "problems.json"), os.path.join(kit.data, "problems.json"))
        shutil.copytree(REAL.tests_dir, kit.tests_dir)
        shutil.copytree(REAL.static, kit.static)
        with open(os.path.join(kit.static, "index.html"), "w") as fh:  # the real page belongs to the front end
            fh.write("<!doctype html><title>t</title><h1>Prep</h1>\n")
        with open(os.path.join(kit.app, "server.py"), "w") as fh:
            fh.write("SECRET = 1\n")
        with open(os.path.join(kit.static, "notes.exe"), "w") as fh:
            fh.write("x")
        self.kit = kit
        patcher = mock.patch.dict(os.environ, {"FAKE_COACH_MODE": "auto"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.httpd = server.make_server(kit, 0, coach_cmd=[sys.executable, FAKE])
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05})
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            h = {"Host": "127.0.0.1:%d" % self.port}
            if body is not None:
                h["Content-Type"] = "application/json"
            h.update(headers or {})
            conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=h)
            resp = conn.getresponse()
            data = resp.read()
            return resp.status, dict((k.lower(), v) for k, v in resp.getheaders()), data
        finally:
            conn.close()


class StaticTests(ServerCase):
    def test_index(self):
        status, headers, data = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "text/html; charset=utf-8")
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertEqual(headers["x-content-type-options"], "nosniff")
        self.assertIn(b"<h1>", data)

    def test_nothing_outside_static(self):
        for path in ("/static/../server.py", "/app/server.py", "/../server.py", "/%2e%2e/server.py",
                     "/static/%2e%2e/server.py", "/notes.exe", "/nope.html", "/static/"):
            status, headers, _ = self.request("GET", path)
            self.assertEqual(status, 404, path)
            self.assertEqual(headers["x-content-type-options"], "nosniff")

    def test_static_prefix_alias(self):
        status, _, data = self.request("GET", "/static/index.html")
        self.assertEqual(status, 200)
        self.assertIn(b"<h1>", data)

    def test_api_through_the_socket(self):
        status, headers, data = self.request("GET", "/api/problem/two-sum")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["slug"], "two-sum")
        status, _, _ = self.request("GET", "/api/overview", headers={"Host": "evil.example"})
        self.assertEqual(status, 403)
        status, _, data = self.request("POST", "/api/heartbeat", {"slug": None, "seconds": 1},
                                       headers={"Origin": "http://evil.example"})
        self.assertEqual(status, 403)
        status, _, data = self.request("POST", "/api/heartbeat", {"slug": None, "seconds": 1},
                                       headers={"Origin": "http://localhost:%d" % self.port,
                                                "Host": "localhost:%d" % self.port})
        self.assertEqual(status, 200)

    def test_sse_stream(self):
        status, headers, data = self.request("POST", "/api/problem/two-sum/coach", {"kind": "hint"})
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "text/event-stream; charset=utf-8")
        lines = [l for l in data.decode().split("\n") if l.startswith("data: ")]
        self.assertGreaterEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[-1][6:])["done"], True)


class RawCase(ServerCase):
    def connect(self):
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        self.addCleanup(sock.close)
        return sock

    def head(self, method, path, extra="", host=None):
        return ("%s %s HTTP/1.1\r\nHost: %s\r\n%s\r\n"
                % (method, path, host or "127.0.0.1:%d" % self.port, extra)).encode()

    def read_all(self, sock):
        chunks = []
        while True:
            try:
                data = sock.recv(65536)
            except socket.timeout:
                self.fail("the server neither answered nor closed the connection")
            if not data:
                return b"".join(chunks)
            chunks.append(data)

    def status_of(self, raw):
        return int(raw.split(b" ", 2)[1])


class StaticSafetyTests(RawCase):
    def test_a_symlink_out_of_static_is_not_served(self):
        outside = os.path.join(self.kit.root, "secret.txt")
        with open(outside, "w") as fh:
            fh.write("secret")
        os.symlink(outside, os.path.join(self.kit.static, "link.txt"))
        status, _, data = self.request("GET", "/link.txt")
        self.assertEqual(status, 404)
        self.assertNotIn(b"secret", data)

    def test_server_header_has_no_trailing_space(self):
        _, headers, _ = self.request("GET", "/")
        self.assertEqual(headers["server"], "PrepKit")


class BodyTests(RawCase):
    def test_an_oversized_body_is_413_over_the_socket(self):
        with mock.patch.object(server.api, "MAX_BODY", 1000):
            status, _, data = self.request("POST", "/api/heartbeat", {"slug": None, "x": "y" * 2000})
        self.assertEqual(status, 413)
        self.assertEqual(json.loads(data)["error"], "too_large")

    def test_an_oversized_content_length_with_no_body_is_413_at_once(self):
        sock = self.connect()
        sock.sendall(self.head("POST", "/api/heartbeat",
                               "Content-Type: application/json\r\nContent-Length: 99999999\r\n"))
        started = time.monotonic()
        raw = self.read_all(sock)  # no body is ever sent: only the pre-read limit check can answer
        self.assertLess(time.monotonic() - started, 2)
        self.assertEqual(self.status_of(raw), 413)
        self.assertIn(b"too_large", raw)
        self.assertIn(b"Request body too large.", raw)
        self.assertNotIn(b"Bad Content-Length.", raw)

    def test_content_length_must_be_plain_digits(self):
        # leading spaces after the colon are optional whitespace in HTTP and are stripped by the
        # parser, so only the forms that int() would accept and HTTP does not are listed here
        for value in ("1_2", "+5", "5 ", "5\t", "1 2", "0x5", "-1", "５"):
            sock = self.connect()
            sock.sendall(self.head("POST", "/api/heartbeat",
                                   "Content-Type: application/json\r\nContent-Length: %s\r\n" % value)
                         + b"{}{}{}{}{}{}{}")
            raw = self.read_all(sock)
            self.assertEqual(self.status_of(raw), 400, value)
            self.assertIn(b"Bad Content-Length.", raw, value)

    def test_chunked_bodies_are_refused(self):
        sock = self.connect()
        sock.sendall(self.head("POST", "/api/heartbeat", "Content-Type: application/json\r\n"
                               "Transfer-Encoding: chunked\r\n") + b"2\r\n{}\r\n0\r\n\r\n")
        raw = self.read_all(sock)
        self.assertEqual(self.status_of(raw), 400)
        self.assertIn(b"Transfer-Encoding", raw)

    def test_a_truncated_body_times_out(self):
        self.assertIsNot(self.httpd.RequestHandlerClass, server.Handler, "one handler class per server")
        self.assertEqual(self.httpd.RequestHandlerClass.timeout, server.REQUEST_TIMEOUT_S)
        self.httpd.RequestHandlerClass.timeout = 0.3
        errors = []
        self.httpd.handle_error = lambda request, address: errors.append(sys.exc_info()[1])
        sock = self.connect()
        sock.sendall(self.head("POST", "/api/heartbeat", "Content-Type: application/json\r\n"
                               "Content-Length: 100\r\n") + b"{")
        started = time.monotonic()
        self.read_all(sock)
        self.assertLess(time.monotonic() - started, 3)
        time.sleep(0.1)
        self.assertEqual(errors, [])

    def test_a_foreign_host_is_refused_before_the_body_is_read(self):
        sock = self.connect()
        sock.sendall(self.head("POST", "/api/heartbeat", "Content-Type: application/json\r\n"
                               "Content-Length: 100\r\n", host="evil.example"))
        started = time.monotonic()
        raw = self.read_all(sock)
        self.assertEqual(self.status_of(raw), 403)
        self.assertLess(time.monotonic() - started, 3)

    def test_the_read_timeout_does_not_cut_a_slow_stream(self):
        self.assertIsNot(self.httpd.RequestHandlerClass, server.Handler, "one handler class per server")
        self.httpd.RequestHandlerClass.timeout = 0.3
        os.environ["FAKE_COACH_MODE"] = "slow"
        os.environ["FAKE_COACH_SLOW"] = "1"
        self.httpd.app.coach_idle = 0.2
        status, _, data = self.request("POST", "/api/problem/two-sum/coach", {"kind": "hint"})
        self.assertEqual(status, 200)
        lines = [l for l in data.decode().split("\n") if l.startswith("data: ")]
        self.assertEqual(json.loads(lines[-1][6:])["done"], True)
        self.assertIn(": ping", data.decode())

    def test_a_client_gone_before_the_body_leaves_no_traceback(self):
        called = threading.Event()
        real = self.httpd.app.handle

        def handle(*args):
            called.set()
            time.sleep(0.3)
            resp = real(*args)
            resp.body = b"x" * (8 * 1024 * 1024)
            return resp

        errors = []
        self.httpd.handle_error = lambda request, address: errors.append(sys.exc_info()[1])
        with mock.patch.object(self.httpd.app, "handle", side_effect=handle):
            sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
            sock.sendall(self.head("GET", "/api/overview"))
            self.assertTrue(called.wait(5))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            sock.close()
            time.sleep(1.0)
        self.assertEqual(errors, [])


class CoachProcessTests(RawCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.mkdtemp(prefix="server-coach-")
        self.addCleanup(shutil.rmtree, tmp, True)
        self.log = os.path.join(tmp, "log.json")
        self.child_log = os.path.join(tmp, "child")
        os.environ.update({"FAKE_COACH_MODE": "spawn", "FAKE_COACH_LOG": self.log,
                           "FAKE_COACH_CHILD_LOG": self.child_log})

    def start_stream(self):
        sock = self.connect()
        body = json.dumps({"kind": "hint"}).encode()
        sock.sendall(self.head("POST", "/api/problem/two-sum/coach",
                               "Content-Type: application/json\r\nContent-Length: %d\r\n"
                               % len(body)) + body)
        got = b""
        while b"data: " not in got:
            data = sock.recv(65536)
            self.assertTrue(data, "the stream closed before the first delta")
            got += data
        with open(self.log) as fh:
            seen = json.load(fh)
        started = time.monotonic()
        while not os.path.exists(self.child_log) and time.monotonic() - started < 5:
            time.sleep(0.02)
        with open(self.child_log) as fh:
            child = int(fh.read())
        self.assertTrue(pid_alive(seen["pid"]) and pid_alive(child))
        return sock, seen, child

    def assert_gone(self, pids, within):
        started = time.monotonic()
        alive = list(pids)
        while alive and time.monotonic() - started < within:
            alive = [p for p in alive if pid_alive(p)]
            time.sleep(0.02)
        self.assertEqual(alive, [], "still running %.1f s after" % within)

    def test_a_disconnect_kills_the_coach_and_its_grandchild_promptly(self):
        sock, seen, child = self.start_stream()
        sock.close()
        self.assert_gone([seen["pid"], child], 1.5)
        started = time.monotonic()
        while os.path.exists(seen["cwd"]) and time.monotonic() - started < 2:
            time.sleep(0.02)
        self.assertFalse(os.path.exists(seen["cwd"]))
        os.environ["FAKE_COACH_MODE"] = "auto"
        status, _, _ = self.request("POST", "/api/problem/two-sum/coach", {"kind": "hint"})
        self.assertEqual(status, 200, "the coach slot is free again")

    def test_a_disconnect_in_hang_mode_frees_the_coach_slot_within_two_seconds(self):
        os.environ["FAKE_COACH_MODE"] = "hang"
        sock = self.connect()
        body = json.dumps({"kind": "hint"}).encode()
        sock.sendall(self.head("POST", "/api/problem/two-sum/coach",
                               "Content-Type: application/json\r\nContent-Length: %d\r\n"
                               % len(body)) + body)
        got = b""
        while b": open" not in got:
            data = sock.recv(65536)
            self.assertTrue(data)
            got += data
        time.sleep(0.3)  # let the coach process start and go quiet
        sock.close()
        os.environ["FAKE_COACH_MODE"] = "auto"  # the next coach call must answer, not hang
        started = time.monotonic()
        status = None
        while time.monotonic() - started < 2:
            status, _, _ = self.request("POST", "/api/problem/two-sum/coach", {"kind": "hint"})
            if status != 409:
                break
            time.sleep(0.05)
        self.assertEqual(status, 200, "a new coach call is accepted within 2 s of the disconnect")

    def test_shutdown_kills_live_coaches_and_removes_their_folders(self):
        sock, seen, child = self.start_stream()
        self.stop()
        self.assert_gone([seen["pid"], child], 1.5)
        self.assertFalse(os.path.exists(seen["cwd"]))


class ReuseAddressTests(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "on Windows reuse would let a second server take a live port")
    def test_a_port_can_be_bound_again_right_after_a_server_stops(self):
        kit = make_kit(self)
        httpd = server.make_server(kit, 0)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05})
        thread.start()
        # the server closes first (Connection: close), which leaves its end in TIME_WAIT
        sock = socket.create_connection(("127.0.0.1", port), timeout=5)
        sock.sendall(("GET /api/overview HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nConnection: close\r\n\r\n"
                      % port).encode())
        while sock.recv(65536):
            pass
        sock.close()
        httpd.shutdown()
        httpd.server_close()
        thread.join()
        again = server.make_server(kit, port)  # no wait: a lingering connection must not block it
        again.server_close()

    def test_a_live_listener_still_blocks_the_port(self):
        kit = make_kit(self)
        first = server.make_server(kit, 0)
        self.addCleanup(first.server_close)
        with self.assertRaises(OSError) as ctx:
            server.make_server(kit, first.server_address[1])
        self.assertEqual(ctx.exception.errno, errno.EADDRINUSE)

    def test_windows_keeps_exclusive_binding(self):
        with mock.patch.object(os, "name", "nt"):
            self.assertFalse(server.reuse_address())
        with mock.patch.object(os, "name", "posix"):
            self.assertTrue(server.reuse_address())


class BindTests(unittest.TestCase):
    def test_only_loopback(self):
        kit = make_kit(self)
        for host in ("0.0.0.0", "", "localhost", "::"):
            with self.assertRaises(ValueError):
                server.make_server(kit, 0, host=host)

    def test_parse_args(self):
        args = server.parse_args([])
        self.assertEqual((args.port, args.no_open, args.explicit_port), (8765, False, False))
        args = server.parse_args(["--port", "9000", "--no-open"])
        self.assertEqual((args.port, args.no_open, args.explicit_port), (9000, True, True))


def dead_pid():
    """The pid of a process that has already exited."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


class LockTests(ServerCase):
    def lock_path(self):
        return os.path.join(self.kit.my_prep, "app", "server.lock")

    def put_lock(self, text):
        os.makedirs(os.path.dirname(self.lock_path()), exist_ok=True)
        with open(self.lock_path(), "w") as fh:
            fh.write(text)

    def test_write_and_remove_the_lock(self):
        server.write_lock(self.kit, 8770)
        with open(self.lock_path()) as fh:
            self.assertEqual(json.load(fh), {"pid": os.getpid(), "port": 8770})
        server.remove_lock(self.kit, 8770)
        self.assertFalse(os.path.exists(self.lock_path()))
        server.remove_lock(self.kit, 8770)  # already gone: no error

    def test_a_lock_that_names_another_process_is_left_alone(self):
        self.put_lock(json.dumps({"pid": os.getpid() + 1, "port": 8770}))
        server.remove_lock(self.kit, 8770)
        self.assertTrue(os.path.exists(self.lock_path()))
        self.put_lock(json.dumps({"pid": os.getpid(), "port": 8771}))
        server.remove_lock(self.kit, 8770)
        self.assertTrue(os.path.exists(self.lock_path()))

    def test_a_live_server_is_found(self):
        self.put_lock(json.dumps({"pid": os.getpid(), "port": self.port}))
        self.assertEqual(server.running_port(self.kit), self.port)

    def test_stale_locks_are_ignored(self):
        self.assertIsNone(server.running_port(self.kit))  # no file
        for text in ("{not json", "[]", json.dumps({"pid": "x", "port": self.port}),
                     json.dumps({"pid": True, "port": self.port}),
                     json.dumps({"pid": dead_pid(), "port": self.port})):
            self.put_lock(text)
            self.assertIsNone(server.running_port(self.kit), text)
        with socket.socket() as sock:  # a live pid but nothing answers on that port
            sock.bind(("127.0.0.1", 0))
            free = sock.getsockname()[1]
        self.put_lock(json.dumps({"pid": os.getpid(), "port": free}))
        self.assertIsNone(server.running_port(self.kit))

    def test_main_exits_at_once_when_the_app_already_runs(self):
        self.put_lock(json.dumps({"pid": os.getpid(), "port": self.port}))
        out = io.StringIO()
        with mock.patch.object(server.paths_mod, "default", return_value=self.kit), \
                mock.patch.object(server, "make_server") as make, \
                mock.patch.object(server.webbrowser, "open") as browser, \
                mock.patch.object(sys, "stdout", out):
            self.assertEqual(server.main(["--no-open"]), 0)
            browser.assert_not_called()
            self.assertEqual(server.main([]), 0)
            browser.assert_called_once_with("http://127.0.0.1:%d/" % self.port)
        make.assert_not_called()
        self.assertIn("The prep app is already running at http://127.0.0.1:%d/" % self.port,
                      out.getvalue())

    def test_a_symlinked_my_prep_stops_the_start(self):
        real = tempfile.mkdtemp(prefix="prepkit-elsewhere-")
        self.addCleanup(shutil.rmtree, real, True)
        shutil.rmtree(self.kit.my_prep)
        os.symlink(real, self.kit.my_prep)
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(server.paths_mod, "default", return_value=self.kit), \
                mock.patch.object(server, "make_server") as make, \
                mock.patch.object(sys, "stdout", out), mock.patch.object(sys, "stderr", err):
            self.assertEqual(server.main(["--no-open"]), 1)
        make.assert_not_called()
        self.assertIn("my-prep/ is a symbolic link. The app needs it to be a real folder inside "
                      "the kit.", err.getvalue())
        self.assertEqual(os.listdir(real), [])


@unittest.skipIf(os.name == "nt", "uses SIGTERM")
class TwoServersTests(unittest.TestCase):
    """The real entry point in a child process, on a copy of the app code."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="prepkit-two-")
        self.addCleanup(shutil.rmtree, self.root, True)
        skip = shutil.ignore_patterns("statements", "tests", "__pycache__")
        shutil.copytree(REAL.app, os.path.join(self.root, "app"), ignore=skip)
        shutil.copytree(REAL.tests_dir, os.path.join(self.root, "app", "data", "tests"))
        shutil.copytree(REAL.course, os.path.join(self.root, "course"))
        self.lock = os.path.join(self.root, "my-prep", "app", "server.lock")
        self.env = dict(os.environ, PREP_COACH_CMD="%s %s" % (sys.executable, FAKE))

    def start(self, *args):
        return subprocess.Popen([sys.executable, os.path.join(self.root, "app", "server.py"),
                                 "--no-open"] + list(args), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=self.env, text=True)

    def test_a_second_server_exits_and_the_lock_goes_with_the_first(self):
        first = self.start("--port", "0")
        self.addCleanup(lambda: first.poll() is None and first.kill())
        line = first.stdout.readline()
        while line and "is running at" not in line:
            line = first.stdout.readline()
        self.assertIn("is running at", line)
        with open(self.lock) as fh:
            lock = json.load(fh)
        self.assertEqual(lock["pid"], first.pid)
        second = self.start()
        out, _ = second.communicate(timeout=20)
        self.assertEqual(second.returncode, 0)
        self.assertIn("The prep app is already running at http://127.0.0.1:%d/" % lock["port"], out)
        first.terminate()  # SIGTERM
        first.communicate(timeout=20)
        self.assertFalse(os.path.exists(self.lock))


if __name__ == "__main__":
    unittest.main()
