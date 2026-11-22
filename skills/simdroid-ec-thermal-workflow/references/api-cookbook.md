# 伏图 EC API Cookbook

01–08 在 `<安装根>\script\` 下用 `<安装根>\bin\python.exe` 运行；`import IBE` 即连内核，无需先开 GUI。09–11 不导入 IBE，用系统 Python（需 `pymupdf`、`python-docx`），`run_ec.ps1` 会按脚本名自动切换。

## 连接与文档

```python
import IBE
import SimDocApi, SimFPartApi, SimPropApi, SimMeshApi, SimAnalysisApi, SimResultApi

SimDocApi.NewDocument(PROJ)          # 新建工程
SimDocApi.SetRunMode("Cmd")          # 新建/打开之后调用
SimDocApi.ImportProject(SimDocApi.ExportType.STEP_STP, STP)
SimDocApi.Save()

SimDocApi.Open(PROJ)                 # 打开已有工程
SimDocApi.SetRunMode("Cmd")
parts = SimDocApi.GetFlexPartsByType("ImportPart")
cubes = SimDocApi.GetFlexPartsByType("Cube")
SimDocApi.delete(obj.Object)         # 删除对象
```

- `GetFlexPartsByType` 支持 `"ImportPart"`、`"Cube"` 等。
- 导入体序号是 **1-based**（`parts[i-1]`）。
- 零件标签：`p.getPropertyValue(["Label"])[0]`。
- 对象名：`p.Object`。

## 项目树与包围盒

```python
import FlexPartApi
FlexPartApi.exportProjectTree(TREE, "0,1,2,3,4,5,6,7")

bb = p.getGlobalBoundingBox()   # ["xmin mm","ymin mm","zmin mm","xmax mm",...]
# 转 float: float(str(v).replace("mm","").strip())
```

## 材料 / 表面 / 辐射

```python
m = SimPropApi.SolidMaterial.create("MAT_PC")
m.setValue(["Isotropic"], ["ThermalConductivityType"])
m.setValue(["Constant"], ["ConductivityType"])
m.setValue(["0.3 W/(m*K)"], ["ConstantConductivity"])

s = SimPropApi.Surface.create("SUR_PC")
s.setValue(["0.8"], ["Emissivity"])

rad = SimPropApi.Radiation.create("RAD_Agg")
rad.setValue(["Agglomeration Radiating"], ["SurfaceType"])
```

## 等效方块

```python
c = SimFPartApi.Cube.create("BOX_" + label[:24])
c.setPosition(["%g mm" % x, "%g mm" % y, "%g mm" % z],
              ["XLocation", "YLocation", "ZLocation"])
c.setPropertyValue(["%g mm" % dx, "%g mm" % dy, "%g mm" % dz],
                   ["XLocalSize", "YLocalSize", "ZLocalSize"])
c.setSolidMaterial(matobj[cls])
c.setSurface([surfobj[cls]])
c.setRadiation([rad])
```

## 热源

```python
bt = SimPropApi.BodyThermal.create("BT_LED_total")
bt.setValue(["Total Source"], ["Type"])
bt.setValue(["9.096 W"], ["OverallValue"])
fpc.setBodyThermal(bt)
```

> 用 **总热功率 W**，不要用 W/m³ 体生热率；后者需要零件体积，容易量级错。

## 监控点

```python
mp = SimFPartApi.MonitorPoint.create("MP_LED_C")
mp.setPosition(["0 mm", "-108.9 mm", "1.2 mm"])
```

## 求解域

```python
sd = SimPropApi.SolutionDomain.get()
sd.setValue(["Input ratio"], ["ExpansionOfCalculationArea"])
sd.setValue(["30 %"], ["ProportionXPos"])
sd.setValue(["30 %"], ["ProportionXNeg"])
sd.setValue(["200 %"], ["ProportionYPos"])
sd.setValue(["50 %"], ["ProportionYNeg"])
sd.setValue(["300 %"], ["ProportionZPos"])
sd.setValue(["300 %"], ["ProportionZNeg"])
sd.setValue(["25 ℃"], ["AmbientTemperature"])
sd.setValue(["25 ℃"], ["RadiationTemperature"])
SimPropApi.SolutionDomain.ResizeDomain()
sd.getValue(["SizeX", "SizeY", "SizeZ"])
```

## 模型设置 / 求解器 / 网格

```python
ms = SimPropApi.ModelSetup.get()
ms.setValue([1], ["EnableGravity"])
ms.setValue([1], ["EnableRadiation"])
ms.setValue(["DO"], ["RadiationModel"])

sc = SimPropApi.SolverControl.get()
sc.setValue([1], ["EnableMonitorPointConvergence"])
sc.setValue(["0.1 ℃"], ["RequiredAccuracy"])
sc.setValue(["30"], ["ResidualThreshold"])
sc.setValue(["300"], ["MaxIteration"])
sc.setValue([1], ["FrozenFlowField"])
sc.setValue(["0.3"], ["T_Factor"])
sc.setValue(["0.5"], ["U_Factor"])
sc.setValue(["0.5"], ["P_Factor"])

gm = SimPropApi.GlobalMeshControl.get()
gm.setValue(["0.1 mm"], ["MinimumSize"])
gm.setValue(["6 mm"], ["MaximumSize"])
gm.setValue(["100"], ["MaxAspectRatio"])
```

## 网格与求解

```python
import SimMeshApi
SimMeshApi.Mesh.Mesh()
SimMeshApi.Mesh.getMeshStats()

import SimAnalysisApi
SimAnalysisApi.Analysis.reinitializeAndCompute()
SimDocApi.Save()
```

结果目录：`<project_root>\<stem>_v5\Solving\result\`，含 `T.txt`、`Residual(T|U|p_rgh).txt`、`result.h5`。

## 结果导出

```python
import SimResultApi
SimResultApi.SimResult.ExportResult(f, obj, "Volume", "Scalar Solid T")
```

CSV 表头：

```text
Point No., Coord X, Coord Y, Coord Z, Solid T (K)
```

第 5 列是温度（K）。`07` 用反向扫描最后一列取 float；`08` 固定取 `r[4]`。

## 常用单位字符串

| 类型 | 写法 |
|---|---|
| 长度 | `"0.1 mm"`、`"3 mm"` |
| 导热 | `"25 W/(m*K)"` |
| 温度 | `"25 ℃"`、`"0.1 ℃"` |
| 功率 | `"9.096 W"` |
| 比例 | `"30 %"`、`"200 %"` |

## 已验证的调用顺序坑

1. `SetRunMode("Cmd")` 必须在 `NewDocument`/`Open` 之后。
2. `import IBE` 前 cwd 必须是 `<安装根>\script\`，否则模块导入失败。
3. 导入体的 `LocalMethod` 不要改 `Octree Based`；实测会崩内核。
4. `delete` 后对象列表会变，按原序号缓存的对象可能失效；先记录再删。
5. `getGlobalBoundingBox` 返回带 `mm` 的字符串，必须清洗后转 float。
6. `Mesh.Mesh()` 是阻塞调用；批处理日志里看到 `MESH:` 才算完成。
7. `reinitializeAndCompute()` 是重算；改设置后不要用“继续计算”。
