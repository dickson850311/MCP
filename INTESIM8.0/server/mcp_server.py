# -*- coding: utf-8 -*-
"""
INTESIM 8.0 MCP Server
======================
外部进程（标准 Python，纯标准库），通过 stdio 与 MCP 客户端通信，
通过本机 TCP 连接 INTESIM 内运行的宿主桥 (intesim_bridge.py)。

传输
----
* 上行/下行: stdin/stdout 上的 newline-delimited JSON-RPC 2.0
* 到桥:      localhost TCP, 长度前缀 JSON 帧（见 bridge_client.py）

启动（供 MCP 客户端配置 command/args）
------------------------------------
    python mcp_server.py
环境变量:
    INTESIM_BRIDGE_HOST  默认 127.0.0.1
    INTESIM_BRIDGE_PORT  默认 5099
"""

import os
import sys
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bridge_client import BridgeClient, BridgeError  # noqa: E402

# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #
HOST = os.environ.get("INTESIM_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("INTESIM_BRIDGE_PORT", "5099"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.log"),
    filemode="a",
)
log = logging.getLogger("mcp-intesim")

bridge = BridgeClient(HOST, PORT)

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "intesim-mcp-server", "version": "0.1.0"}

# --------------------------------------------------------------------------- #
# 工具清单（与宿主桥 HANDLERS 对齐）
# --------------------------------------------------------------------------- #
def _prop(typ, description, required=False, default=None):
    p = {"type": typ, "description": description}
    if default is not None:
        p["default"] = default
    return p


TOOLS = [
    {
        "name": "ping",
        "description": "探测宿主桥与 INTESIM 进程是否存活，返回时间戳与 Python 版本。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "status",
        "description": "获取桥接状态：已加载的官方模块、工作目录、工程文件、是否 UI 模式、是否允许脚本执行。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "project.open",
        "description": "在 INTESIM 中打开工程/网格文件（.xml 或网格文件）。",
        "inputSchema": {
            "type": "object",
            "properties": {"path": _prop("string", "要打开的文件绝对路径")},
            "required": ["path"],
        },
    },
    {
        "name": "project.info",
        "description": "获取当前工程文件名与工作目录。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "model.list",
        "description": "列出当前模型树中的分析模型/物理场及其基本信息。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "model.solve",
        "description": "提交并求解指定名称的模型（调用 INTESIM 求解器）。",
        "inputSchema": {
            "type": "object",
            "properties": {"model_name": _prop("string", "要求解的模型名称")},
            "required": ["model_name"],
        },
    },
    {
        "name": "mesh.import",
        "description": "向当前分析对象导入外部网格文件。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": _prop("string", "网格文件路径"),
                "unit": _prop("string", "长度单位，默认 mm", default="mm"),
                "replace": _prop("string", "替换的网格对象名称（可空）", default=""),
            },
            "required": ["name"],
        },
    },
    {
        "name": "mesh.export",
        "description": "导出当前网格到文件。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": _prop("string", "导出文件路径"),
                "flag": _prop("integer", "导出标志，默认 1", default=1),
            },
            "required": ["name"],
        },
    },
    {
        "name": "mesh.component_info",
        "description": "查询指定网格组件（节点/单元/Part 组件）的信息。",
        "inputSchema": {
            "type": "object",
            "properties": {"comp_name": _prop("string", "组件名称")},
            "required": ["comp_name"],
        },
    },
    {
        "name": "post.open",
        "description": "在后处理中打开结果文件。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": _prop("string", "结果文件路径"),
                "model_name": _prop("string", "模型名称（可空）", default=""),
            },
            "required": ["file"],
        },
    },
    {
        "name": "post.extract_max",
        "description": "提取当前云图/结果的最大值。",
        "inputSchema": {
            "type": "object",
            "properties": {"name": _prop("string", "结果/云图名称")},
            "required": ["name"],
        },
    },
    {
        "name": "post.save_picture",
        "description": "保存当前视图截图到文件。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "width": _prop("integer", "图像宽度，默认 1280", default=1280),
                "height": _prop("integer", "图像高度，默认 960", default=960),
                "quality": _prop("integer", "画质 0-100，默认 90", default=90),
                "name": _prop("string", "输出图片路径"),
            },
            "required": ["name"],
        },
    },
    {
        "name": "view.set",
        "description": "切换预设视角（fitView / 正视 / 侧视 / 俯视等）。",
        "inputSchema": {
            "type": "object",
            "properties": {"view": _prop("string", "视角名称，默认 fitView", default="fitView")},
        },
    },
    {
        "name": "script.run",
        "description": "【受限、默认关闭】在 INTESIM 宿主内执行一段 Python 脚本或表达式；需桥配置 allow_eval=true。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": _prop("string", "Python 代码"),
                "mode": _prop("string", "eval 或 exec，默认 eval", default="eval"),
            },
            "required": ["code"],
        },
    },
]

TOOL_NAMES = {t["name"] for t in TOOLS}


# --------------------------------------------------------------------------- #
# JSON-RPC 分发
# --------------------------------------------------------------------------- #
def _result(rid, payload):
    return {"jsonrpc": "2.0", "id": rid, "result": payload}


def _error(rid, code, message):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def _handle(req):
    method = req.get("method")
    rid = req.get("id")
    params = req.get("params", {}) or {}

    if method == "initialize":
        return _result(rid, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })

    if method == "notifications/initialized":
        return None  # 通知，不回包

    if method == "ping":
        return _result(rid, {})

    if method == "tools/list":
        return _result(rid, {"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {}) or {}
        if name not in TOOL_NAMES:
            return _error(rid, -32601, "unknown tool: %s" % name)
        try:
            result = bridge.call(name, arguments)
            text = json.dumps(result, ensure_ascii=False, indent=2, default=str)
            return _result(rid, {
                "content": [{"type": "text", "text": text if text else "null"}],
                "isError": False,
            })
        except BridgeError as e:
            log.error("tool %s bridge error: %s", name, e)
            return _result(rid, {
                "content": [{"type": "text", "text": "BridgeError: %s" % e}],
                "isError": True,
            })
        except Exception as e:
            log.exception("tool %s failed", name)
            return _result(rid, {
                "content": [{"type": "text", "text": "%s: %s" % (type(e).__name__, e)}],
                "isError": True,
            })

    # 未实现的可选方法，返回方法未找到，避免客户端卡死
    return _error(rid, -32601, "method not supported: %s" % method)


def main():
    log.info("MCP server starting, bridge=%s:%d", HOST, PORT)
    stdin = sys.stdin
    stdout = sys.stdout
    # 强制 utf-8，避免 Windows GBK 导致中文报错
    try:
        stdin.reconfigure(encoding="utf-8")
        stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            log.warning("bad JSON-RPC frame: %s", e)
            continue

        try:
            resp = _handle(req)
        except Exception as e:
            log.exception("dispatch fatal")
            resp = _error(req.get("id"), -32603, str(e))

        if resp is not None:
            stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            stdout.flush()


if __name__ == "__main__":
    main()
