# -*- coding: utf-8 -*-
"""
INTESIM 桥接 TCP 客户端（运行在外部 Python，纯标准库）。

帧协议（与 bridge/intesim_bridge.py 一致）：
    4 字节大端长度 N + N 字节 UTF-8 JSON
    请求: {"id", "tool", "args"}
    响应: {"id", "ok", "result", "error"}
"""

import json
import time
import uuid
import struct
import socket
import threading


class BridgeError(RuntimeError):
    pass


class BridgeClient(object):
    def __init__(self, host="127.0.0.1", port=5099, timeout=30.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    def _connect(self):
        if self._sock is not None:
            return
        sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        sock.settimeout(self.timeout)
        self._sock = sock

    def _close(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
        self._sock = None

    def _ensure_connected(self):
        if self._sock is None:
            self._connect()

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise BridgeError("bridge closed the connection")
            buf += chunk
        return buf

    # ------------------------------------------------------------------ #
    def call(self, tool, args=None, retries=1):
        """同步调用桥工具；失败自动重连一次。"""
        args = args or {}
        last_err = None
        for attempt in range(retries + 1):
            try:
                with self._lock:
                    self._ensure_connected()
                    rid = uuid.uuid4().hex
                    req = {"id": rid, "tool": tool, "args": args}
                    payload = json.dumps(req, ensure_ascii=False).encode("utf-8")
                    self._sock.sendall(struct.pack(">I", len(payload)) + payload)

                    header = self._recv_exact(4)
                    (size,) = struct.unpack(">I", header)
                    body = self._recv_exact(size)
                    resp = json.loads(body.decode("utf-8"))

                if not resp.get("ok"):
                    raise BridgeError(resp.get("error") or "bridge returned failure")
                return resp.get("result")
            except (socket.error, BridgeError, OSError) as e:
                last_err = e
                with self._lock:
                    self._close()
                if attempt < retries:
                    time.sleep(0.3)
                else:
                    raise BridgeError("cannot reach INTESIM bridge at %s:%d: %s"
                                      % (self.host, self.port, e))
        raise BridgeError(last_err)

    def ping(self):
        return self.call("ping", {})
