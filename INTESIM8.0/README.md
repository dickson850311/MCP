# INTESIM 8.0 · MCP 桥接

让支持 MCP（Model Context Protocol）的客户端（豆包 / Claude Desktop / VS Code 等）通过本地网络调用本机 INTESIM 8.0 的脚本 API：打开工程、查看模型、提交求解、导入导出网格、后处理取结果、截图等。

## 1. 架构

```
┌───────────────────────┐   stdio JSON-RPC (换行分隔)   ┌────────────────────────────┐
│ MCP 客户端             │ ◄───────────────────────────► │ mcp_server.py (外部进程)    │
│ 豆包 / Claude / VSCode │                               │ 内置 Python 3.8, 纯标准库   │
└───────────────────────┘                               └───────────────┬────────────┘
                                                                 │ 127.0.0.1:5099
                                                                 │ 长度前缀 JSON 帧
                                              ┌──────────────────▼─────────────┐
                                              │ intesim_bridge.py (宿主桥)     │
                                              │ 运行在 INTESIM 进程内置 Python │
                                              │ 调用 Window/Model/Mesh/Post...  │
                                              └──────────────────┬─────────────┘
                                                                 │
                                              ┌──────────────────▼─────────────┐
                                              │ INTESIM 8.0  (intesim.exe)     │
                                              └────────────────────────────────┘
```

**为什么是双进程？** INTESIM 的官方脚本绑定模块（`_Window / _Model / _Mesh / _Post ...`）由宿主 `intesim.exe` 在启动时注册，只能在其进程内调用；外部 Python 无法直接 `import`。因此桥脚本必须被加载进 INTESIM 进程，MCP server 再通过本机 TCP 与它通信。

## 2. 本机侦察结果（已确认）

| 项 | 值 |
|---|---|
| 安装目录 | `D:\INTESIM8.0` |
| 主程序 | `D:\INTESIM8.0\GUI\intesim.exe` |
| 内置 Python | `D:\INTESIM8.0\Python38\python.exe`（3.8.10） |
| 官方脚本模块 | `Window / Model / Mesh / Post / CAD / Global / physics` |
| 官方自带 RPC 端口 | `5000`（私有协议，本桥未复用） |
| 本桥监听端口 | `5099`（可在 `bridge/bridge_config.json` 改） |

## 3. 目录结构

```
intesim-mcp/
├── server/
│   ├── mcp_server.py        # MCP stdio 服务端（对客户端）
│   └── bridge_client.py     # 到宿主桥的 TCP 客户端（帧协议 + 断线重连）
├── bridge/
│   ├── intesim_bridge.py    # 宿主桥（在 INTESIM 内置 Python 内运行）
│   ├── bridge_plugin.py      # 插件形式加载包装（方式 C）
│   └── bridge_config.json    # 桥配置：host / port / allow_eval
├── launch/
│   ├── start_intesim_with_bridge.bat  # 带桥启动 INTESIM
│   ├── mcp_server.bat                 # 启动 MCP server
│   └── mcp_config_example.json       # MCP 客户端配置片段
└── tests/
    ├── fake_bridge.py        # 测试用假桥
    └── test_protocol.py      # 帧协议 + MCP 握手端到端自测
```

## 4. 快速开始

### 4.1 在 INTESIM 进程内加载宿主桥（三选一）

**方式 A · 命令行带桥启动（推荐先试）**
双击或运行：
```
launch\start_intesim_with_bridge.bat
```
它执行 `intesim.exe <bridge\intesim_bridge.py> -f`（脚本路径在前，`-f` 为脚本文件模式）。若你的版本该参数行为不同，改用方式 B。

**方式 B · 软件内手动执行脚本（最稳妥）**
1. 正常打开 INTESIM 8.0；
2. 菜单 **文件 → 执行脚本**（或脚本面板的“执行脚本”）；
3. 选择 `bridge\intesim_bridge.py`；
4. 看到桥日志 `bridge listening on 127.0.0.1:5099` 即成功（日志同时写入 `bridge\bridge.log`）。

**方式 C · 插件自动加载（随软件启动）**
1. 新建目录 `D:\INTESIM8.0\GUI\plugin\IntesimMcpBridge\`；
2. 把 `intesim_bridge.py`、`bridge_config.json`、`bridge_plugin.py` 复制进去；
3. 在 `D:\INTESIM8.0\GUI\intesim.ini` 的 `[General]` 下追加：
   ```ini
   autoLoadPluginComd=plugin.LoadPlugin('IntesimMcpBridge')
   ```
4. 重启 INTESIM。

### 4.2 配置 MCP 客户端

把 `launch\mcp_config_example.json` 中 `mcpServers.intesim` 一段并入客户端的 MCP 配置（Claude Desktop 为 `claude_desktop_config.json`；VS Code 在设置的 MCP 面板；豆包按其 MCP 接入说明填写）。

```json
{
  "mcpServers": {
    "intesim": {
      "command": "D:\\INTESIM8.0\\Python38\\python.exe",
      "args": ["C:\\path\\to\\intesim-mcp\\server\\mcp_server.py"],
      "env": { "INTESIM_BRIDGE_HOST": "127.0.0.1", "INTESIM_BRIDGE_PORT": "5099" }
    }
  }
}
```

> 路径含中文/空格时保持 JSON 转义；`args[0]` 指向 `mcp_server.py` 的绝对路径。

### 4.3 验证连通

在客户端调用 `ping`，应返回 `{"pong": true, ...}`；再调用 `status` 查看已加载的官方模块与工作目录。也可先跑自测（不依赖真实 INTESIM）：

```
D:\INTESIM8.0\Python38\python.exe tests\test_protocol.py
```

## 5. 已暴露工具

| 工具 | 说明 | 主要参数 |
|---|---|---|
| `ping` | 探测桥与进程存活 | — |
| `status` | 模块可用性、工作目录、工程文件、UI 模式、是否允许脚本执行 | — |
| `project.open` | 打开工程/网格文件 | `path` |
| `project.info` | 当前工程文件名、工作目录 | — |
| `model.list` | 列出模型/物理场 | — |
| `model.solve` | 求解指定模型 | `model_name` |
| `mesh.import` | 导入网格 | `name`, `unit`, `replace` |
| `mesh.export` | 导出网格 | `name`, `flag` |
| `mesh.component_info` | 查询组件信息 | `comp_name` |
| `post.open` | 打开结果文件 | `file`, `model_name` |
| `post.extract_max` | 提取最大值 | `name` |
| `post.save_picture` | 保存视图截图 | `width`, `height`, `quality`, `name` |
| `view.set` | 切换预设视角 | `view` |
| `script.run` | 受限执行 Python（**默认关闭**） | `code`, `mode` |

## 6. 通信协议

**桥 ↔ MCP server（TCP，127.0.0.1:5099）**
- 帧：`4 字节大端无符号长度 N` + `N 字节 UTF-8 JSON`
- 请求：`{"id": "...", "tool": "...", "args": {...}}`
- 响应：`{"id": "...", "ok": true/false, "result": ..., "error": null|"错误信息"}`

**MCP server ↔ 客户端（stdio）**
- JSON-RPC 2.0，换行分隔；实现 `initialize` / `notifications/initialized` / `ping` / `tools/list` / `tools/call`。

## 7. 安全说明

- `script.run` 可在 INTESIM 进程内执行任意 Python，**默认关闭**。需要时在 `bridge/bridge_config.json` 置 `"allow_eval": true`，并仅在可信会话中开启。
- 桥只监听 `127.0.0.1`，不对局域网暴露。
- 桥不保存工程、不修改许可证；所有写操作（求解/导入/导出）作用于当前打开的模型。

## 8. 故障排查

| 现象 | 排查 |
|---|---|
| 客户端报 `cannot reach INTESIM bridge at 127.0.0.1:5099` | 桥未加载：按 4.1 在 INTESIM 内执行脚本；查看 `bridge\bridge.log` 是否有 `listening` |
| `status` 里 `missing_modules` 非空 | 当前脚本会话未注入对应模块；在有界面的完整工程会话中加载桥，而非批处理空会话 |
| 某工具返回 `unavailable` | 该 API 在当前模型/模块下不存在；对照 `D:\INTESIM8.0\GUI\*.py` 的函数签名调整 |
| 端口被占用 | 改 `bridge_config.json` 的 `port`，同步改客户端 `env.INTESIM_BRIDGE_PORT` |
| 中文乱码 | 两端均按 UTF-8；`mcp_server.py` 已强制 stdin/stdout 为 utf-8 |
| 求解/写操作不生效 | 官方 API 多依赖 Qt 主线程；跨线程写操作在个别版本可能不刷新界面，必要时在桥内改为队列 + 主线程定时器执行（见第 10 节） |

## 9. 如何新增工具

1. **桥侧**：在 `intesim_bridge.py` 的 `HANDLERS` 注册一个 `h_xxx(args)`，返回可 JSON 序列化的数据；调用对应官方模块函数。
2. **server 侧**：在 `mcp_server.py` 的 `TOOLS` 增加同名工具与 `inputSchema`。
3. 两端工具名保持一致；自测通过后再接入客户端。

## 10. 已知限制与后续可做

- **线程模型**：当前桥在连接线程内直接调用官方 API。读操作/命令通常可用；若后续发现界面写操作需要主线程，可在桥内引入任务队列，用 Qt 定时器（`QTimer`）在主线程消费。
- **几何建模脚本**：官方手册说明几何/网格部分能力暂不支持脚本录制；本桥的几何类工具以官方 Python API 实际暴露为准。
- **官方私有 RPC（5000 端口）**：已识别其为 `ISServer.exe + JSON + MethodInvoker` 体系，但线格式私有；本桥采用自有的本地帧协议以避免逆向。若后续官方提供公开 SDK/客户端绑定，可把 `bridge_client.py` 替换为官方通道，MCP 侧工具无需改动。
- **结果数据回传**：后处理的场量/云图数据结构较复杂，首版仅回传标量（最大值等）与截图；批量场量导出可在桥内扩展 `Post` 相关接口。
