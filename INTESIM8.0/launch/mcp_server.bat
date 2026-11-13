@echo off
rem ============================================================
rem 启动 MCP stdio server (供 MCP 客户端作为 command 调用)
rem 也可在客户端配置里直接用:  python <server\mcp_server.py>
rem ============================================================
setlocal

set "INTESIM_BRIDGE_HOST=127.0.0.1"
set "INTESIM_BRIDGE_PORT=5099"

rem 默认使用 INTESIM 自带的 Python 3.8(路径稳定, 纯标准库即可运行);
rem 如需改用系统 Python, 把下一行改为 python 或其绝对路径。
set "PYTHON_EXE=D:\INTESIM8.0\Python38\python.exe"

"%PYTHON_EXE%" "%~dp0..\server\mcp_server.py" %*

endlocal
