# -*- coding: utf-8 -*-
"""帧协议 + BridgeClient + MCP server 端到端自测。运行: python test_protocol.py"""
import os
import sys
import json
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(HERE, "..", "server")
sys.path.insert(0, SERVER_DIR)
sys.path.insert(0, HERE)

from bridge_client import BridgeClient, BridgeError  # noqa: E402
from fake_bridge import FakeBridge  # noqa: E402


def test_bridge_client():
    fb = FakeBridge()
    port = fb.start()
    try:
        c = BridgeClient("127.0.0.1", port, timeout=5)
        pong = c.ping()
        assert pong["pong"] is True, pong
        status = c.call("status")
        assert status["fake"] is True
        echo = c.call("echo", {"a": 1, "b": "x"})
        assert echo == {"a": 1, "b": "x"}
        try:
            c.call("boom")
            raise AssertionError("expected BridgeError")
        except BridgeError:
            pass
        print("[ok] BridgeClient protocol round-trip")
    finally:
        fb.stop()


def test_mcp_server_end_to_end():
    fb = FakeBridge()
    port = fb.start()
    env = dict(os.environ)
    env["INTESIM_BRIDGE_PORT"] = str(port)
    env["INTESIM_BRIDGE_HOST"] = "127.0.0.1"
    py = os.environ.get("MCP_TEST_PYTHON", sys.executable)
    proc = subprocess.Popen(
        [py, os.path.join(SERVER_DIR, "mcp_server.py")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, text=True, encoding="utf-8", bufsize=1,
    )
    try:
        def send(obj):
            proc.stdin.write(json.dumps(obj) + "\n")
            proc.stdin.flush()

        def recv():
            line = proc.stdout.readline()
            return json.loads(line) if line.strip() else None

        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": "2024-11-05", "capabilities": {}}})
        init = recv()
        assert init["result"]["serverInfo"]["name"] == "intesim-mcp-server", init
        assert "tools" in init["result"]["capabilities"], init

        send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        listed = recv()
        names = [t["name"] for t in listed["result"]["tools"]]
        assert "ping" in names and "model.solve" in names, names
        assert len(names) >= 12, names

        send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
              "params": {"name": "ping", "arguments": {}}})
        call = recv()
        assert call["result"]["isError"] is False, call
        text = call["result"]["content"][0]["text"]
        assert "pong" in text, text
        print("[ok] MCP server initialize / tools/list / tools/call end-to-end")
    finally:
        proc.stdin.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        fb.stop()


if __name__ == "__main__":
    test_bridge_client()
    test_mcp_server_end_to_end()
    print("ALL TESTS PASSED")
