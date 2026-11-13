# -*- coding: utf-8 -*-
"""
插件形式加载包装（对应 INTESIM 的 plugin.LoadPlugin 机制）。

部署方式（方式 C，自动加载）：
  1. 把本目录下的 intesim_bridge.py / bridge_config.json / bridge_plugin.py
     复制到  D:\\INTESIM8.0\\GUI\\plugin\\IntesimMcpBridge\\
  2. 在 intesim.ini 的 [General] 下追加:
        autoLoadPluginComd=plugin.LoadPlugin('IntesimMcpBridge')
  3. 重启 INTESIM。

注意: 插件目录名需与 LoadPlugin 名称一致; 本文件在宿主内置 Python 中执行,
仅使用标准库。
"""
import os
import sys

_f = globals().get("__file__")
_here = os.path.dirname(os.path.abspath(_f)) if _f else os.getcwd()
if _here not in sys.path:
    sys.path.insert(0, _here)

# 以模块方式导入; intesim_bridge 底部会在后台线程启动 TCP 服务, 不阻塞宿主。
import intesim_bridge  # noqa: E402,F401
