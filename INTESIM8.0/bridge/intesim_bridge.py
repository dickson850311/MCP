#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
INTESIM 8.0 宿主桥 (bridge)
===========================
运行在 INTESIM 自带的 Python 3.8 进程内部，通过本机 TCP 向外部 MCP server
暴露官方脚本 API（Window / Model / Mesh / Post / CAD / Global ...）。

设计约束
--------
* 仅使用 Python 标准库（socket / json / threading / struct / logging ...），
  不依赖任何第三方包，避免与宿主内嵌环境冲突。
* 帧协议：4 字节大端长度(N) + N 字节 UTF-8 JSON。
* 请求: {"id": str, "tool": str, "args": {...}}
* 响应: {"id": str, "ok": bool, "result": ..., "error": str | null}

加载方式（三选一，详见 README）
--------------------------------
A. 命令行:  intesim.exe -f <本脚本路径>
B. 软件内:  文件 > 执行脚本 > 选择本脚本
C. 插件:    放入 GUI\\plugin 目录并在 ini 的 autoLoadPluginComd 中加载
"""

import os
import sys
import json
import time
import struct
import socket
import logging
import threading
import traceback

# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #
def _here_dir():
    f = globals().get("__file__")
    if f:
        return os.path.dirname(os.path.abspath(f))
    # 宿主以 exec 方式执行、未注入 __file__ 时的回退
    if sys.argv and sys.argv[0]:
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.getcwd()


HERE = _here_dir()
CONFIG_PATH = os.path.join(HERE, "bridge_config.json")
LOG_PATH = os.path.join(HERE, "bridge.log")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5099


def _load_config():
    cfg = {
        "host": os.environ.get("INTESIM_BRIDGE_HOST", DEFAULT_HOST),
        "port": int(os.environ.get("INTESIM_BRIDGE_PORT", str(DEFAULT_PORT))),
        "allow_eval": os.environ.get("INTESIM_BRIDGE_ALLOW_EVAL", "false").lower() == "true",
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user = json.load(f)
            for k in ("host", "port", "allow_eval"):
                if k in user:
                    cfg[k] = user[k]
        except Exception as e:
            sys.stderr.write("bridge config load failed: %s\n" % e)
    return cfg


CONFIG = _load_config()

# --------------------------------------------------------------------------- #
# 日志（宿主内 stdout 可能不可见，同时落文件）
# --------------------------------------------------------------------------- #
logger = logging.getLogger("intesim-bridge")
logger.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
try:
    _fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    _fh.setFormatter(_fmt)
    logger.addHandler(_fh)
except Exception:
    pass
_ch = logging.StreamHandler(sys.stdout)
_ch.setFormatter(_fmt)
logger.addHandler(_ch)

# --------------------------------------------------------------------------- #
# 官方模块探测
# --------------------------------------------------------------------------- #
# 宿主脚本环境通常已把 GUI 目录加入 sys.path，并在全局命名空间注入
# Window / Model / Mesh / Post / CAD / Global 等包装模块。
OFFICIAL_MODULES = ["Window", "Model", "Mesh", "Post", "CAD", "Global", "physics", "tools"]

_modules = {}
_missing = []


def _discover_modules():
    g = globals()
    for name in OFFICIAL_MODULES:
        mod = g.get(name)
        if mod is None:
            try:
                mod = __import__(name)
            except Exception:
                mod = None
        if mod is not None:
            _modules[name] = mod
        else:
            _missing.append(name)


_discover_modules()
logger.info("official modules loaded: %s; missing: %s",
            sorted(_modules.keys()), _missing)


def _mod(name):
    return _modules.get(name)


# --------------------------------------------------------------------------- #
# 安全序列化：把 boost.python 包装对象尽量转成 JSON 原生类型
# --------------------------------------------------------------------------- #
def _to_native(obj, depth=0):
    if depth > 4:
        return repr(obj)
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_to_native(x, depth + 1) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _to_native(v, depth + 1) for k, v in obj.items()}

    # boost.python 列表 / 集合：优先 count()+at(i)，其次 len()+迭代
    count = getattr(obj, "count", None)
    at = getattr(obj, "at", None)
    if callable(count) and callable(at):
        try:
            n = count()
            return [_to_native(at(i), depth + 1) for i in range(n)]
        except Exception:
            pass
    try:
        return [_to_native(x, depth + 1) for x in obj]
    except Exception:
        pass

    # 普通包装对象：抽取可读属性
    info = {"__class__": type(obj).__name__}
    for attr in ("name", "id", "Id", "label"):
        v = getattr(obj, attr, None)
        if v is not None:
            try:
                info[attr] = _to_native(v, depth + 1)
            except Exception:
                info[attr] = repr(v)
    return info


def _arg(args, key, default=None):
    return (args or {}).get(key, default)


# --------------------------------------------------------------------------- #
# 工具处理器
# --------------------------------------------------------------------------- #
def h_ping(args):
    return {"pong": True, "time": time.time(), "python": sys.version.split()[0]}


def h_status(args):
    info = {
        "bridge": "intesim-bridge",
        "python": sys.version.split()[0],
        "modules": sorted(_modules.keys()),
        "missing_modules": _missing,
        "allow_eval": CONFIG["allow_eval"],
        "cwd": os.getcwd(),
    }
    win = _mod("Window")
    if win is not None:
        for getter, key in (
            ("getProjectFileName", "project_file"),
            ("getWorkingDirectory", "working_dir"),
            ("isUIMode", "ui_mode"),
        ):
            fn = getattr(win, getter, None)
            if callable(fn):
                try:
                    info[key] = _to_native(fn())
                except Exception as e:
                    info[key] = "error: %s" % e
    return info


def h_project_open(args):
    path = _arg(args, "path")
    if not path:
        raise ValueError("argument 'path' is required")
    mesh = _mod("Mesh")
    if mesh is not None and hasattr(mesh, "openFile"):
        mesh.openFile(path)
        return {"opened": path}
    raise RuntimeError("Mesh.openFile unavailable in this session")


def h_project_info(args):
    out = {}
    win = _mod("Window")
    if win is not None:
        for getter, key in (
            ("getProjectFileName", "project_file"),
            ("getWorkingDirectory", "working_dir"),
        ):
            fn = getattr(win, getter, None)
            if callable(fn):
                try:
                    out[key] = _to_native(fn())
                except Exception as e:
                    out[key] = "error: %s" % e
    return out


def _list_models():
    """遍历全局 models 列表（ModelList）。"""
    models = None
    g = globals()
    for cand in ("models", "Models"):
        if cand in g:
            models = g[cand]
            break
    if models is None:
        m = _mod("Model")
        if m is not None:
            models = getattr(m, "models", None)
    result = []
    if models is not None:
        count = getattr(models, "count", None)
        at = getattr(models, "at", None)
        if callable(count) and callable(at):
            for i in range(count()):
                result.append(_to_native(at(i)))
        else:
            result = [_to_native(x) for x in models]
    return result


def h_model_list(args):
    return {"models": _list_models()}


def h_model_solve(args):
    name = _arg(args, "model_name")
    if not name:
        raise ValueError("argument 'model_name' is required")
    model = _mod("Model")
    if model is None:
        raise RuntimeError("Model module unavailable")
    fn = getattr(model, "solvePhysicsModel", None) or getattr(model, "solveModel", None)
    if not callable(fn):
        raise RuntimeError("solve function unavailable")
    fn(name)
    return {"solved": name}


def h_mesh_import(args):
    name = _arg(args, "name")
    unit = _arg(args, "unit", "mm")
    replace = _arg(args, "replace", "")
    if not name:
        raise ValueError("argument 'name' is required")
    mesh = _mod("Mesh")
    if mesh is None:
        raise RuntimeError("Mesh module unavailable")
    mesh.importMesh(name, unit, replace)
    return {"imported": name, "unit": unit}


def h_mesh_export(args):
    name = _arg(args, "name")
    flag = _arg(args, "flag", 1)
    if not name:
        raise ValueError("argument 'name' is required")
    mesh = _mod("Mesh")
    mesh.exportMesh(name, flag)
    return {"exported": name}


def h_mesh_component_info(args):
    comp = _arg(args, "comp_name")
    if not comp:
        raise ValueError("argument 'comp_name' is required")
    mesh = _mod("Mesh")
    fn = getattr(mesh, "getComponentInfo", None)
    if not callable(fn):
        raise RuntimeError("getComponentInfo unavailable")
    return {"component": comp, "info": _to_native(fn(comp))}


def h_post_open(args):
    f = _arg(args, "file")
    model = _arg(args, "model_name", "")
    post = _mod("Post")
    if post is None:
        raise RuntimeError("Post module unavailable")
    fn = getattr(post, "openPostFile", None) or getattr(post, "openPostWindow", None)
    fn(f, model)
    return {"opened": f, "model": model}


def h_post_extract_max(args):
    name = _arg(args, "name")
    if not name:
        raise ValueError("argument 'name' is required")
    post = _mod("Post")
    fn = getattr(post, "extractMaxValue", None)
    if not callable(fn):
        raise RuntimeError("extractMaxValue unavailable")
    return {"max": _to_native(fn(name))}


def h_post_save_picture(args):
    w = int(_arg(args, "width", 1280))
    h = int(_arg(args, "height", 960))
    q = int(_arg(args, "quality", 90))
    name = _arg(args, "name", "")
    post = _mod("Post")
    if post is not None and hasattr(post, "savePicture"):
        post.savePicture(w, h, q, name)
    else:
        win = _mod("Window")
        if win is not None and hasattr(win, "saveGraphics"):
            win.saveGraphics(w, h, q, name)
        else:
            raise RuntimeError("save picture API unavailable")
    return {"saved": name, "size": [w, h]}


def h_view_set(args):
    view = _arg(args, "view", "fitView")
    win = _mod("Window")
    if win is not None and hasattr(win, "setView"):
        win.setView(view)
        return {"view": view}
    post = _mod("Post")
    if post is not None and hasattr(post, "setView"):
        post.setView(view)
        return {"view": view}
    raise RuntimeError("setView unavailable")


def h_script_run(args):
    """受限脚本执行（默认关闭，需 bridge_config.json 中 allow_eval=true）。"""
    if not CONFIG["allow_eval"]:
        raise RuntimeError("script.run is disabled; set allow_eval=true in bridge_config.json")
    code = _arg(args, "code")
    mode = _arg(args, "mode", "eval")  # eval | exec
    if not code:
        raise ValueError("argument 'code' is required")
    sandbox = dict(_modules)
    sandbox["globals"] = globals()
    if mode == "exec":
        exec(compile(code, "<mcp-bridge>", "exec"), sandbox)
        return {"executed": True}
    return {"result": _to_native(eval(compile(code, "<mcp-bridge>", "eval"), sandbox))}


HANDLERS = {
    "ping": h_ping,
    "status": h_status,
    "project.open": h_project_open,
    "project.info": h_project_info,
    "model.list": h_model_list,
    "model.solve": h_model_solve,
    "mesh.import": h_mesh_import,
    "mesh.export": h_mesh_export,
    "mesh.component_info": h_mesh_component_info,
    "post.open": h_post_open,
    "post.extract_max": h_post_extract_max,
    "post.save_picture": h_post_save_picture,
    "view.set": h_view_set,
    "script.run": h_script_run,
}


def dispatch(tool, args):
    handler = HANDLERS.get(tool)
    if handler is None:
        raise KeyError("unknown tool: %s" % tool)
    return handler(args or {})


# --------------------------------------------------------------------------- #
# 帧协议
# --------------------------------------------------------------------------- #
def _recv_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise EOFError("connection closed")
        buf += chunk
    return buf


def _read_frame(conn):
    header = _recv_exact(conn, 4)
    (size,) = struct.unpack(">I", header)
    if size == 0 or size > 16 * 1024 * 1024:
        raise ValueError("invalid frame size: %d" % size)
    payload = _recv_exact(conn, size)
    return json.loads(payload.decode("utf-8"))


def _write_frame(conn, obj):
    payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    conn.sendall(struct.pack(">I", len(payload)) + payload)


def _handle_connection(conn, addr):
    logger.info("client connected: %s", addr)
    try:
        while True:
            try:
                req = _read_frame(conn)
            except EOFError:
                break
            rid = req.get("id")
            tool = req.get("tool")
            args = req.get("args", {}) or {}
            logger.info("dispatch tool=%s id=%s", tool, rid)
            try:
                result = dispatch(tool, args)
                resp = {"id": rid, "ok": True, "result": result, "error": None}
            except Exception as e:
                tb = traceback.format_exc()
                logger.error("tool %s failed: %s\n%s", tool, e, tb)
                resp = {"id": rid, "ok": False, "result": None,
                        "error": "%s: %s" % (type(e).__name__, e)}
            _write_frame(conn, resp)
    except Exception as e:
        logger.error("connection %s error: %s", addr, e)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        logger.info("client disconnected: %s", addr)


def serve():
    host, port = CONFIG["host"], CONFIG["port"]
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(8)
    logger.info("bridge listening on %s:%d (allow_eval=%s)", host, port, CONFIG["allow_eval"])
    while True:
        conn, addr = srv.accept()
        t = threading.Thread(target=_handle_connection, args=(conn, addr), daemon=True)
        t.start()


def main():
    logger.info("INTESIM bridge starting, python=%s", sys.version)
    try:
        serve()
    except Exception:
        logger.error("bridge fatal:\n%s", traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
else:
    # 被插件/宿主以模块方式加载时，后台线程启动服务，不阻塞宿主主线程
    logger.info("bridge imported as module; starting background server")
    _t = threading.Thread(target=main, daemon=True)
    _t.start()
