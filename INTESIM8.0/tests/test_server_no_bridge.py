# -*- coding: utf-8 -*-
"""无桥场景: server 仍应响应 initialize / tools/list; tools/call 应返回桥错误而非崩溃。"""
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(HERE, "..", "server")
env = dict(os.environ)
env["INTESIM_BRIDGE_PORT"] = "5099"  # 无监听

proc = subprocess.Popen(
    [sys.executable, os.path.join(SERVER_DIR, "mcp_server.py")],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    env=env, text=True, encoding="utf-8", bufsize=1,
)

def send(o):
    proc.stdin.write(json.dumps(o) + "\n"); proc.stdin.flush()

def recv():
    return json.loads(proc.stdout.readline())

send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
init = recv()
assert init["result"]["serverInfo"]["name"] == "intesim-mcp-server"

send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
listed = recv()
assert len(listed["result"]["tools"]) >= 12

send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
      "params": {"name": "ping", "arguments": {}}})
call = recv()
assert call["result"]["isError"] is True, call
assert "BridgeError" in call["result"]["content"][0]["text"], call

proc.stdin.close(); proc.terminate()
try: proc.wait(timeout=5)
except Exception: proc.kill()
print("[ok] server works offline; call degrades to BridgeError")
