---
name: simdroid-ec-thermal-workflow
description: 伏图电子散热（Simdroid Electronic Cooling V2026.7.x）从 STEP 导入、零件包围盒、材料/热源/辐射/求解域、薄件清理与网格、DO 辐射+冻结流动、稳态求解、结果 CSV、图表/温度图到 Word 报告的 11 步全流程。用于复现 QR-V23 背光模组热仿真、批量重跑现有 .simec 工程，或在新背光/显示模组上复用该脚本化流程；包含已验证脚本、参数基线、API cookbook、踩坑清单和输出校验。
---

# 伏图电子散热（Simdroid EC）全流程

## 用途

把背光/显示模组的热仿真做成可重复执行的 11 步链路：几何 → 包围盒 → 建模 → 薄件清理/网格 → 辐射/冻结流动 → 求解 → 结果提取 → 统计 → 图表 → 温度图 → Word 报告。

这套脚本已在 **Simdroid Electronic Cooling V2026.7.3（5.0R20260904, Quantum）** 上端到端跑通，案例为 QR-V23-15.4 背光模组。脚本是“已验证参考实现”，换产品时按本文的路径/参数表改，不要重写 API 调用顺序。

不适用于：INTESIM 结构/热场流程、POC 冷热冲击 7200 s 瞬态复现、GUI 手工建模教学。那些属于其他 Skill/工程。

## 前置条件

| 项 | 要求 |
|---|---|
| 安装根 | `D:\Simdroid Electronic Cooling V2026.7.3`（可用 `EC_INSTALL_ROOT` 覆盖） |
| 解释器 | 01–08 用 `<安装根>\bin\python.exe`（Python 3.7.8）；09–11 用系统 Python（需 `pymupdf`、`python-docx`）；`run_ec.ps1` 自动切换 |
| 工作目录 | 必须是 `<安装根>\script\`；`run_ec.ps1` 已处理 |
| 许可 | `C:\Users\<user>\.IBE\licCfg\SimdroidECV2026\IBE.ini` |
| 输入 | 一个 STEP（`.stp/.step`）；QR-V23 为 `QR-V23-15.4 2024-6-12.stp` |
| 工程根 | 默认 `D:\mcp-servers\ec-api\QR-V23_EC`；所有中间 `.simec` 和输出都在这里 |
| Python 包 | 09–11 需要系统 Python 的 `pymupdf`、`python-docx`；EC 3.7 环境只跑 01–08（`import IBE`） |
| 姿态 | 导入后产品必须摆到实际使用姿态（重力方向）。脚本不负责旋转，需在 STEP 或 GUI 预处理 |

## 快速开始

```powershell
cd <skill>\scripts

# 全流程；01 会新建并覆盖 project_config.json 里的 files.ec
powershell -ExecutionPolicy Bypass -File .\run_all_ec.ps1

# 已有 v5 工程，只重跑求解及后处理
powershell -ExecutionPolicy Bypass -File .\run_all_ec.ps1 -From 6

# 指定另一份配置
powershell -ExecutionPolicy Bypass -File .\run_all_ec.ps1 -Config ..\assets\project_config.json
```

首次使用先编辑 `assets/project_config.json` 的 `install_root`、`project_root`、`step_file` 和 `files.*`。脚本内仍保留 QR-V23 默认路径；配置只覆盖路径，不改物理参数。

单步调试：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_ec.ps1 -Script .\03_build_model.py
```

> `run_all_ec.ps1 -From 6` 的前提是 `files.v5` 已存在。若没有，先跑 1–5。`01` 覆盖 `files.ec`，重跑前先备份。

## 11 步流程

| # | 脚本 | 做什么 | 关键动作 / 参数 | 产物与检查 |
|---|---|---|---|---|
| 01 | `01_import_geometry.py` | 新建工程、导入 STEP、导出零件树 | `NewDocument` → `SetRunMode("Cmd")` → `ImportProject(STEP_STP)` → `Save` | `files.ec`、`files.tree`；核对导入体数量/名称 |
| 02 | `02_export_bbox.py` | 导出每个导入体的全局包围盒 | `getGlobalBoundingBox()`，写 CSV；同时打印求解域 | `files.bbox`；列：`Object,Label,xmin..zmax,dx,dy,dz` |
| 03 | `03_build_model.py` | 建材料/表面/辐射，替换薄壳件，赋材料，加热源，设监控点、求解域、DO、求解器、网格 | 复制 `files.ec`→`files.v2`；22 个薄壳件按 bbox 换成等效 `Cube`；其余保留 CAD；`Total Source` 热源；`Agglomeration Radiating`；DO；求解域比例；`EnableGravity=1` | `files.v2`；检查零件数、热源落在 FPC、监控点坐标、求解域尺寸 |
| 04 | `04_thin_cleanup_mesh.py` | 删除最小尺寸 <0.1 mm 的超薄辅料，首次剖分 | `files.v2`→`files.v3`；`THIN=0.1`；全局网格最小 0.05 / 最大 6 mm；`Mesh.Mesh()` | `files.v3`；看 `getMeshStats()` 的单元数、最小尺寸、长宽比 |
| 05 | `05_v5_radiation_frozenflow.py` | 冻结流动 + DO 辐射 + 松弛 + 重划网格 | `files.v3`→`files.v5`；`FrozenFlowField=1`；`MaxIteration=300`；T/U/P 松弛 0.3/0.5/0.5；`EnableRadiation=1`、`RadiationModel=DO`；网格最小 0.1 / 最大 6 mm | `files.v5`；确认 DO、冻结流动、网格有效 |
| 06 | `06_solve.py` | 提交稳态求解 | `SimAnalysisApi.Analysis.reinitializeAndCompute()`；结果写 `files.v5\Solving\result\` | `T.txt`、`Residual(T|U|p_rgh).txt`、`result.h5`；检查残差/监控点 |
| 07 | `07_results_key_parts.py` | 导出关键零件 `Scalar Solid T` | 按标签前缀匹配 FPC/LGP/DBEF/铁框/Frame 等；`SimResult.ExportResult(..., "Volume", "Scalar Solid T")` | `files.temp_extract\*.csv`；逐件 min/max |
| 08 | `08_stats_all.py` | 全部零件温度统计 | 遍历 `ImportPart` + `Cube`；每个 CSV 取第 5 列温度；输出 K 与 ℃ | `files.temp_all\*.csv`、`files.summary_csv` |
| 09 | `09_charts.py` | 监控点曲线、零件最高温排行、收敛统计 | 读 `files.result_t` 前 7 列；`pymupdf` 画图；读汇总 CSV 排序 | `files.report_img\chart_monitor.png`、`chart_parts.png` |
| 10 | `10_maps.py` | 体数据重构温度图：全局俯视、LED 条带、LGP 板面 | 读 `files.temp_all`；1.5 mm 全局网格、2 mm 条带分箱、4 mm LGP 网格；取单元最大值 | `map_top.png`、`chart_strip.png`、`map_lgp.png` |
| 11 | `11_report.py` | 生成 Word 报告 | 读 `files.summary_csv` + `report_img` 四张图；数值全部来自 CSV/TXT | `files.report_docx`；检查图片嵌入与关键表 |

依赖关系：`06 → 07/08 → 09/10 → 11`。`09` 读 `T.txt`，`10` 读 `temp_all`，`11` 读 `report_img` 的 `chart_monitor.png`、`chart_parts.png`、`chart_strip.png`、`map_lgp.png`；缺一张 `11` 会在 `add_picture` 处报文件不存在。

## 路径与参数

路径统一在 `assets/project_config.json`；`scripts/ec_paths.py` 支持 `EC_CONFIG` 环境变量和 `{project_root}` 占位符。物理参数仍写在脚本里，换产品时按下面位置改：

| 位置 | 需要改什么 |
|---|---|
| `03_build_model.py` | `OFFEND`（要换成等效方块的 1-based 导入序号）、`MATS`（k/发射率）、`MAP`（序号→材料）、`P_HEAT`（总热功率 W）、监控点坐标、求解域比例、网格 0.05/3、求解器 0.1℃/30/500 |
| `04_thin_cleanup_mesh.py` | `THIN`（默认 0.1 mm）、网格 0.05/6 |
| `05_v5_radiation_frozenflow.py` | 松弛因子、`MaxIteration`、网格 0.1/6 |
| `07_results_key_parts.py` | `TARGETS` 标签前缀 |
| `09_charts.py` | `names` 五个监控点名称必须与 03 创建的一致 |
| `10_maps.py` | LED 条带 y 坐标 `-108.96`、LGP 标签关键字、网格尺寸 |
| `11_report.py` | 封面产品名、工程路径、日期、工序、组件前缀（`FPC tape`、`Frame 01`、`BOX_SOLID`、`BOX_DBEF`、`BOX_BEF`、`BOX_DIFF`、`BOX_REF_2`、`LGP_1`、`PRT0029` 等） |

## 验证门槛

1. **03 后**：导入体数 = bbox 行数；22 个 `BOX_*` 已创建；热源 `9.096 W` 落在 `FPC tape_1`；5 个监控点存在；求解域约 `550.8 × 792.5 × 134.7 mm`。
2. **04/05 后**：`Mesh is valid`；记录流体/固体单元数、最小/最大尺寸、最大长宽比、最大非正交度、劣质面数。非正交度 >70、畸变度 >4、长宽比 >100 视为质量差。
3. **06 后**：`T.txt` 有迭代记录；残差是否降到阈值 30；最后 10 步监控点变化。**300 步是上限，不等于收敛**。
4. **07/08 后**：CSV 温度单位是 K；汇总 CSV 同时给 K/℃；关键零件有数据，不能有空表。
5. **09/10 后**：四张 PNG 均存在且非 0 字节；LGP 图不能缺失。
6. **11 后**：DOCX 能打开，至少嵌入 4 张图；数值与汇总 CSV 一致。

一键校验：

```powershell
python .\scripts\check_pipeline.py --config .\assets\project_config.json
```

## 结果口径（必须分清）

| 口径 | 热源 | 辐射/流动 | 网格 | 步数 | 结果 |
|---|---|---|---|---|---|
| **本代码包 QR-V23 实跑** | 9.096 W（60×151.6 mW @100 mA） | DO + 冻结流动 | 0.1 / 6 mm | 300 步上限 | FPC 最高 **107.33 ℃**；汇总 CSV 40 件 |
| **培训 12.3″ 样机参考** | 222 mW/颗（3.1 V×120 mA） | 未开辐射 | 内部 0.4 / 外部 3 mm | — | LED **59 ℃**；屏面 40+ ℃；背面 45–46 ℃ |

- `107.3 ℃` 是 QR-V23 现有几何 + 原项目材料/热源设置的结果，**不是** POC 冷热冲击工况，也不是设计定案值。
- 该次 300 步跑到步数上限，末步 T 残差约 107（阈值 30），最后 10 步监控点仍变化 ≤0.195 K；199→300 步热点普遍再升约 4 K。作为定案数据应继续加步（建议 400–500）或调松弛/阈值直到残差 <30，并做网格无关性。
- 培训的 `59 ℃` 来自另一颗 222 mW LED、未开辐射的 12.3″ 样机，**不能当作 QR-V23 的期望值**；两者热源差 9.096 W vs 单颗 0.222 W，且辐射/网格不同。
- 若实际驱动为 120 mA，QR-V23 热功率约 11.51 W，温升预计再增 20–25%（估算，需重算确认）。

## 故障处理

| 现象 | 原因 | 处理 |
|---|---|---|
| `import IBE` 失败 | cwd 不在 `<安装根>\script\` | 用 `run_ec.ps1`，不要直接双击脚本 |
| `模型中存在非正交元件，无法剖分网格` | 导入体局部坐标系旋转/面不垂直坐标轴，八叉树网格拒绝 | 用 03 的薄壳等效方块 + 保留部分 CAD；或让结构重导正交 STEP；**不要**把 `LocalMethod` 改 `Octree Based`（会崩内核） |
| 网格量失控/剖分失败 | 薄壳件按实体剖分 | 先 03 换等效块，再 04 删 <0.1 mm 辅料 |
| 04/05 删件后 07/08 取不到结果 | 零件名变了 | 重新核对 `TARGETS`/标签；用 `temp_all` 的汇总 CSV 找实际标签 |
| 监控点恒为环境温度 | 点落在流体域，不在固体 | 把监控点移到实体内部（LED 正中心/板内），或改用体数据统计 |
| `11_report.py` 报 `add_picture` 文件不存在 | 09/10 未生成某张图，尤其 `map_lgp.png` | 先跑 09/10；本 Skill 的 10 已补 LGP 图生成 |
| 300 步后残差仍高 | 只跑满步数上限，未收敛 | 加步/调松弛/网格；报告里明确写“未收敛，偏保守偏低” |
| 报告里的零件名/数值对不上 | `11_report.py` 是 QR-V23 案例模板 | 换产品必须改封面、组件前缀和日期；数值以 CSV 为准 |

## 资源

- `references/workflow.md`：逐步输入/输出、依赖、文件树、验收细节。
- `references/parameters.md`：QR-V23 材料/热源/求解域/网格/求解器/结果，及培训参考值。
- `references/api-cookbook.md`：`SimDocApi` / `SimFPartApi` / `SimPropApi` / `SimMeshApi` / `SimAnalysisApi` / `SimResultApi` 的实际调用片段。
- `references/troubleshooting.md`：失败现象、根因、已验证的修复/禁止项。
- `scripts/`：11 个阶段脚本 + `ec_paths.py` + 两个 PowerShell 入口 + `check_pipeline.py`。
- `assets/project_config.json`：当前 QR-V23 路径配置；`project_config.example.json` 为新项目模板。

## 交付前检查

- `SKILL.md`、`scripts/`、`references/`、`assets/` 齐全；无 `README.md`、示例占位文件、`__pycache__`。
- 所有 `.py` 通过 `py_compile`；两个 `.ps1` 通过 PowerShell Parser。
- 若在本机有现有工程，跑 `check_pipeline.py`，确认四张图 + DOCX 可读。
- GitHub 目标：`dickson850311/MCP` 的 `skills/simdroid-ec-thermal-workflow/`；不要覆盖 `skills/intesim-native-post-contours/`。
