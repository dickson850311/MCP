# -*- coding: utf-8 -*-
"""测试用假桥：模拟 INTESIM 宿主桥的帧协议，标准库 TCP。"""
import json
import struct
import socket
import threading
import time


class FakeBridge(object):
    def __init__(self, host="127.0.0.1", port=0):
        self.host = host
        self.port = port
        self._srv = None
        self._thread = None
        self._stop = threading.Event()
        self.calls = []

    def _handle(self, conn):
        try:
            while not self._stop.is_set():
                header = self._recv(conn, 4)
                if not header:
                    break
                (size,) = struct.unpack(">I", header)
                body = self._recv(conn, size)
                req = json.loads(body.decode("utf-8"))
                self.calls.append(req)
                tool, args = req.get("tool"), req.get("args", {})
                if tool == "ping":
                    result = {"pong": True, "time": time.time()}
                elif tool == "status":
                    result = {"fake": True, "modules": ["Window", "Mesh", "Model", "Post"]}
                elif tool == "echo":
                    result = args
                elif tool == "boom":
                    raise RuntimeError("simulated failure")
                else:
                    raise KeyError("unknown tool: %s" % tool)
                resp = {"id": req.get("id"), "ok": True, "result": result, "error": None}
                self._send(conn, resp)
        except Exception as e:
            resp = {"id": None, "ok": False, "result": None, "error": str(e)}
            try:
                self._send(conn, resp)
            except Exception:
                pass
        finally:
            conn.close()

    @staticmethod
    def _recv(conn, n):
        buf = b""
        while len(buf) < n:
            c = conn.recv(n - len(buf))
            if not c:
                return buf
            buf += c
        return buf

    @staticmethod
    def _send(conn, obj):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        conn.sendall(struct.pack(">I", len(payload)) + payload)

    def start(self):
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind((self.host, self.port))
        self._srv.listen(4)
        self.port = self._srv.getsockname()[1]
        self._thread = threading.Thread(target=self._accept, daemon=True)
        self._thread.start()
        return self.port

    def _accept(self):
        self._srv.settimeout(0.5)
        while not self._stop.is_set():
            try:
                conn, _ = self._srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def stop(self):
        self._stop.set()
        try:
            self._srv.close()
        except Exception:
            pass
