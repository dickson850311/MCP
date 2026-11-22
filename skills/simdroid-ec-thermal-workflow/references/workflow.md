# 伏图 EC 11 步全流程细节

## 文件树

```text
<project_root>\
├─ <stem>_EC.simec          # 01 导入后
├─ tree_after_import.json   # 01 项目树
├─ bbox.csv                 # 02 包围盒
├─ <stem>_v2.simec          # 03 材料/热源/求解域/网格设置
├─ <stem>_v3.simec          # 04 删薄件 + 首次网格
├─ <stem>_v5.simec          # 05 DO + 冻结流动 + 重划网格
├─ <stem>_v5\Solving\result\
│  ├─ T.txt                 # 监控点迭代曲线
│  ├─ Residual(T|U|p_rgh).txt
│  └─ result.h5
├─ temp_extract\*.csv       # 07 关键零件
├─ temp_all\*.csv           # 08 全部零件
├─ 温度结果汇总.csv          # 08 汇总（K + ℃）
├─ report_img\              # 09/10 图
│  ├─ chart_monitor.png
│  ├─ chart_parts.png
│  ├─ chart_strip.png
│  ├─ map_top.png
│  └─ map_lgp.png
└─ <stem>_稳态热仿真报告.docx # 11
```

## 01 导入几何

**输入**：STEP。**输出**：`files.ec`、`files.tree`。

- `SimDocApi.NewDocument(PROJ)` 新建工程；`SetRunMode("Cmd")` 必须在新建之后。
- `SimDocApi.ImportProject(SimDocApi.ExportType.STEP_STP, STP)` 导入 STEP；`Save()`。
- `GetFlexPartsByType("ImportPart")` 取导入体，打印 `Name | Label`；QR-V23 为 59 件。
- `FlexPartApi.exportProjectTree(TREE, "0,1,2,3,4,5,6,7")` 导出树；失败不影响后续。
- **检查**：导入体数、标签、整体外形；产品姿态是否正确（脚本不旋转）。

## 02 导出包围盒

**输入**：`files.ec`。**输出**：`files.bbox`。

- 遍历 `ImportPart`，`p.getGlobalBoundingBox()` 返回 `[xmin,ymin,zmin,xmax,ymax,zmax]`（字符串带 mm）。
- CSV 列：`Object,Label,xmin,ymin,zmin,xmax,ymax,zmax,dx,dy,dz`。
- 同时打印整体 bbox 和当前求解域（`SolutionDomain.get().getValue(["X","Y","Z","SizeX","SizeY","SizeZ","AmbientTemperature"])`）。
- **检查**：行数 = 导入体数；dx/dy/dz 与产品尺寸一致；异常小/异常大的件要做薄壳或删除判断。

## 03 建模型

**输入**：`files.ec`、`files.bbox`。**输出**：`files.v2`。

1. `shutil.copyfile(BASE, PROJ)` 复制工程；`Open(PROJ)` + `SetRunMode("Cmd")`。
2. 建 8 类 `SolidMaterial` 和 `Surface`（发射率），建 `Radiation`（`Agglomeration Radiating`）。
3. 按 1-based 导入序号 `OFFEND`（22 件）删除原导入体，按 bbox 建等效 `Cube`：`BOX_<label>`，位置 = bbox 左下角，尺寸 = dx/dy/dz，赋材料/表面/辐射。
4. 剩余导入体按 `MAP` 赋材料/表面/辐射。
5. 热源：`BodyThermal.create`，`Type=Total Source`，`OverallValue=9.096 W`，挂到 FPC（QR-V23 是第 2 个导入体 `FPC tape_1`）。
6. 监控点：5 个 `MonitorPoint`；QR-V23 坐标见 `parameters.md`。
7. 求解域：`SolutionDomain.get()`，`ExpansionOfCalculationArea=Input ratio`；X ±30%、Y 正 200%/负 50%、Z ±300%；`AmbientTemperature=25 ℃`、`RadiationTemperature=25 ℃`；`ResizeDomain()`。
8. 模型设置：`EnableGravity=1`、`EnableRadiation=1`、`RadiationModel=DO`。
9. 求解器：`EnableMonitorPointConvergence=1`、`RequiredAccuracy=0.1 ℃`、`ResidualThreshold=30`、`MaxIteration=500`。
10. 全局网格：`MinimumSize=0.05 mm`、`MaximumSize=3 mm`、`MaxAspectRatio=100`。
11. `Save()`。

**检查**：`BOX_*` 数量 = 22；剩余导入体 = 37（QR-V23）；热源对象标签含 `FPC tape_1`；求解域约 `550.8 × 792.5 × 134.7 mm`；监控点坐标落在实体内部（不要落在空气）。

## 04 薄件清理 + 首次网格

**输入**：`files.v2`。**输出**：`files.v3`。

- 复制 v2→v3；遍历 `ImportPart` + `Cube`，`min(dx,dy,dz) < 0.1 mm` 的件删除（QR-V23 删 15 件，最终 40 件：24 导入体 + 16 方块）。
- 全局网格最小 0.05 / 最大 6 mm，最大长宽比 100。
- `SimMeshApi.Mesh.Mesh()`；`getMeshStats()`。
- **检查**：网格有效；记录单元数（QR-V23 最终 553,563 = 流体 514,950 + 固体 38,613）；最小尺寸 0.1 mm；最大长宽比很大（薄片切片导致，报告中要说明）。

## 05 辐射 + 冻结流动 + 重划网格

**输入**：`files.v3`。**输出**：`files.v5`。

- 复制 v3→v5；`SolverControl`：`FrozenFlowField=1`、`MaxIteration=300`、`T_Factor=0.3`、`U_Factor=0.5`、`P_Factor=0.5`。
- `ModelSetup`：`EnableRadiation=1`、`RadiationModel=DO`。
- 全局网格最小 0.1 / 最大 6 mm，最大长宽比 100；`Mesh.Mesh()`；`Save()`。
- **检查**：DO 已生效；冻结流动 = 1；网格有效；如果 04 网格已失败，先修几何/薄件，不要盲目改 0.05。

## 06 求解

**输入**：`files.v5`。**输出**：`Solving\result\`。

- `Open`、`SetRunMode("Cmd")`；打印 `FrozenFlowField`、`MaxIteration`、收敛判据。
- `SimAnalysisApi.Analysis.reinitializeAndCompute()`；完成后 `Save()`。
- QR-V23 实测：8 进程，300 步，约 20 min 59 s；T 残差约 107（阈值 30），最后 10 步监控点变化 ≤0.195 K。**未收敛**。
- **检查**：`T.txt` 行数 ≈ 步数；残差曲线；监控点末值；`result.h5` 大小。

## 07 关键零件结果

**输入**：`files.v5`。**输出**：`files.temp_extract\*.csv`。

- 按标签前缀匹配：`FPC tape_1`、`LGP_1`、`DBEF`、`PRT0029_tiekuang`、`Frame 01`。
- 每个对象 `SimResultApi.SimResult.ExportResult(f, obj, "Volume", "Scalar Solid T")`。
- CSV 表头 `Point No., Coord X, Coord Y, Coord Z, Solid T (K)`；第 5 列温度。
- **检查**：每个目标至少一个 CSV；max/min 合理（K，约 298 K 起）。

## 08 全部零件统计

**输入**：`files.v5`。**输出**：`files.temp_all\*.csv`、`files.summary_csv`。

- 遍历 `ImportPart` + `Cube`，逐个导出 `Scalar Solid T`；每个 CSV 从 `Point No.` 行后读第 5 列。
- 汇总列：`零件标签,类型,对象名,单元数,最低温_K,最高温_K,平均温_K,最低温_C,最高温_C,平均温_C`。
- QR-V23 最终 40 行；`FPC tape_1` 最高 107.33 ℃、平均 96.38 ℃；`Frame 01` 最高 106.09 ℃；`BOX_SOLID` 105.14 ℃。
- **检查**：行数 = 参与计算件数；温度不出现 0 K/负值；关键件不为空。

## 09 图表

**输入**：`files.result_t`、`files.summary_csv`。**输出**：`chart_monitor.png`、`chart_parts.png`。

- `T.txt` 解析：跳过 `#`，每行至少 7 列；第 2 列迭代步，第 3–7 列 5 个监控点温度（K）。
- 最后 10 步最大变化 = 收敛辅助判据；QR-V23 约 0.195 K。
- 图 1：5 条监控点 T-迭代曲线；图 2：前 18 件最高温/平均温横向条形图。
- **检查**：迭代数 > 10；曲线末端走平（但残差可能仍未达阈值）。

## 10 温度图

**输入**：`files.temp_all`。**输出**：`map_top.png`、`chart_strip.png`、`map_lgp.png`。

- 所有 CSV 的点 `(x,y,z,T)` 汇总；全局俯视 1.5 mm 网格，取每格最大 T；色标固定 25–103 ℃（QR-V23 报告口径）。
- LED 条带：`abs(y + 108.96) < 2.0`，按 x 每 2 mm 分箱取最大；输出沿线温度。
- LGP 图：文件名含 `LGP` 的 CSV，4 mm 网格取最大；色标按该件 min/max 动态；输出 `map_lgp.png`。
- 这些图是**体数据重构**，不是 EC 原生云图；原生云图需 GUI 后处理，批处理模式只能导出数据。
- **检查**：三张 PNG 存在且非 0 字节；LGP 文件被匹配到；坐标范围与产品一致。

## 11 Word 报告

**输入**：`files.summary_csv`、`report_img` 四张图。**输出**：`files.report_docx`。

- 读汇总 CSV，按最高温降序；用标签前缀 `g(prefix)` 取关键件。
- 章节：摘要、项目概述、建模与简化、材料/热源/边界、网格、求解与收敛、结果、结论与风险、复现路径。
- `doc.add_picture` 依次插入 `chart_monitor.png`、`chart_parts.png`、`chart_strip.png`、`map_lgp.png`。
- **检查**：DOCX 至少 4 张嵌入图；关键表数值与 CSV 一致；报告文字中的“300 步/残差 107/未收敛”等结论不要被旧模板覆盖。

## 依赖与重跑

```text
01 → 02 → 03 → 04 → 05 → 06 → 07/08 → 09/10 → 11
```

- `01` 会覆盖 `files.ec`；只重跑后段用 `-From`。
- `-From 6` 需要 `files.v5` 已存在。
- `-From 7` 需要 `Solving\result` 已存在。
- `11` 需要 `09`/`10` 的四张图；缺图先补 09/10。
- 换产品时，`03` 的 `OFFEND`/`MAP`/`P_HEAT` 和 `11` 的组件前缀最容易出错。
