@echo off
rem ============================================================
rem 启动 INTESIM 8.0 并在进程内加载 MCP 宿主桥
rem 说明: -f 表示以脚本文件模式在宿主内执行(脚本路径在前, -f 在后);
rem       若你的版本该参数行为不同, 请改为在软件内手动: 文件 > 执行脚本 > 选 intesim_bridge.py
rem ============================================================
setlocal

set "INTESIM_EXE=D:\INTESIM8.0\GUI\intesim.exe"
set "BRIDGE_SCRIPT=%~dp0..\bridge\intesim_bridge.py"
set "INTESIM_BRIDGE_PORT=5099"

if not exist "%INTESIM_EXE%" (
  echo [ERROR] INTESIM executable not found: %INTESIM_EXE%
  echo         Please edit INTESIM_EXE in this bat file.
  exit /b 1
)

start "" "%INTESIM_EXE%" "%BRIDGE_SCRIPT%" -f
echo [INFO] Launched INTESIM with bridge script: %BRIDGE_SCRIPT%
echo [INFO] Bridge listens on 127.0.0.1:%INTESIM_BRIDGE_PORT%
endlocal
