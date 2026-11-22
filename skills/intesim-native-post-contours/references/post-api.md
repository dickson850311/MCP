# INTESIM 8.0 Post API Notes

这些结论来自 INTESIM 8.0 主 GUI 的实际调用，不是通用 CAE 后处理假设。

## Entry points

- 主 GUI：`D:\INTESIM8.0\GUI\intesim.exe`。Post 视图是在当前主窗口内新建的后处理上下文，不是在顶部“后处理”标签里。
- 顶部“后处理”标签进入的是“仿真报告 / 新建 Bug 报告 / Record / Play”，不是结果云图查看器。
- `D:\INTESIM8.0\GUI\Intesim-Post.exe -s script.py` 是结果转换器/脚本宿主，不会生成可见 Post 窗口，也不会执行 Python 脚本；不要把它当 Post GUI。
- `Intesim-Post-Batch.exe -h` 只打印许可证 feature XML，不是批量出图工具。
- MCP 桥的 `post.open` 在桥宿主里会报 `Post Window is Not open!`；出图走主 GUI 控制台，不走桥。

## Required order

```python
Window.closePostWindow()
Mesh.openFile(r"...\MODEL.model_1.model.xml")
time.sleep(10)                      # 模型加载时间，按模型大小 10–15 s
Post.openPostWindow(r"...\RESULT.res.inp", "M_Thermal_Auto")
time.sleep(4)
Post.setBeamAndShell3DView(True)    # 热场外表皮
```

没有加载模型就调用 `Post.openPostWindow` 会让主窗口崩溃。必须打开 `*.model_1.model.xml`；只打开 `*.model` 会提示 `0 Physics Models`，拿不到 `M_Thermal_Auto` / `M_Struct_Auto`。

切换模型时重复：

```python
Window.closePostWindow()
time.sleep(2)
Mesh.openFile(next_model_xml)
time.sleep(10)
Post.openPostWindow(next_res_inp, next_model_name)
time.sleep(4)
```

## Nodal scalar

```python
sp = Post.newScalar(model_name)
sp.name = "temperature"
sp.dataAdapterID = 0
for cid in range(1, 30):
    sp.appendCompId(cid)

sp.setDraw(True)
sp.setDrawContour(True)
sp.setShowIsoLine(False)
sp.min = -40.0
sp.max = 20.0
sp.length = 400
sp.dataCount = 10
sp.location = 0
sp.setAutoPosition(True)
sp.hideoutrange = False
sp.showmaxlabel = False
sp.showminlabel = False
sp.showminmaxid = False
sp.drawMethod = "Default"
sp.drawRangeSetting = False
sp.show()
```

`NodalScalar` 可用字段：`name`、`dataAdapterID`、`appendCompId(id)`、`clearCompList()`、`compList`、`setDraw(bool)`、`setDrawContour(bool)`、`setShowIsoLine(bool)`、`min`、`max`、`length`、`dataCount`、`location`、`setAutoPosition(bool)`、`hideoutrange`、`showmaxlabel`、`showminlabel`、`showminmaxid`、`drawMethod`、`drawRangeSetting`、`show()`。

`setShowLabel(False)` / `setShowLabelByValue(False)` / `setShowLabelBack(False)` 在部分版本可用；包在 `try/except` 里，避免版本差异。

## Known adapter IDs

| Variable | dataAdapterID | Notes |
|---|---:|---|
| `temperature` | 0 | 热场节点温度 |
| `displacement x` | 0 | 按手册顺序推断，使用前用实际结果确认 |
| `displacement y` | 1 | 推断 |
| `displacement z` | 2 | 已验证 |
| `displacement sum` | 3 | 已验证，即 \|U\| |
| `von Mises` | 15 | 手册示例 |

`Post.GetAdaptorId(model, description, isNode)` 存在，可用于反查，但不同版本返回值不稳定；能确定时优先在 config 里显式写 `adapter`。

## View and export

```python
Post.setView("SolidView")
Post.fitDirectionView(0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0)

ps = Post.PlotSetting()
ps.showLogo = False
ps.showDescription = True
ps.showDate = False
ps.showLegendBar = True
ps.legendFontSize = 20
ps.legendPrecision = 1
ps.legendSplitNumber = 8
ps.showCoordinateSystem = False
ps.apply()

Post.savePicture(1600, 900, 100, out_png)
```

- 1600×900 适配主视口；1600×1200 会裁切模型。
- `Post.setView("FitView")` 比 `fitDirectionView` 更紧，边缘更容易裁。
- `Post.lookAt(...)` 试过一次会把模型移出视口，不要用。
- 结构图左右外侧圆环可能轻微裁边，这是 16:9 与模型外形比例导致的；主体和 legend 完整即可。
- `Post.savePicture` 生成的 1600×900 PNG 是未压缩的，单张约 5.77 MB；DOCX ZIP 会把它压到几十 KB，不能用 DOCX 体积判断是否写入。

## Plot settings

`Post.PlotSetting()` 可用：`showLogo`、`showDescription`、`showDate`、`showLegendBar`、`legendFontSize`、`legendPrecision`、`legendSplitNumber`、`showCoordinateSystem`、`legendType`、`legendMinColor`、`legendMaxColor`、`apply()`。

云图左上角的 `Physics Model` / `step` / `time` 来自 `showDescription=True`；不要为了“干净”把它关掉，它是原生图的重要证据。

## Cutting planes

`Post.newCuttingPlane()` 可用，属性包括 `name`、`id`、`owner`、`setPlanePara(a,b,c,d)`、`appendCompID`、`show()`、`Edit()`，平面方程 `ax+by+cz+d=0`。

但 `appendCompID` 曾触发 `Model ID is wrong 0 does not exist`，剖面图有杂点，未作为报告图采用。若要用剖面，先小范围验证组件 ID。

## Color-scale caveat

Post legend 的范围由当前 scalar 的 `min` / `max` 和显示组件集合决定。若完整结果里有一个孤立节点是 1.00 ℃，但它不属于当前显示组件，legend 可能显示 20.00 ℃ 下限。图题/导语要写清“图内色标”与“完整结果统计 Tmin”的差别，不能改图迁就文字。

## Debug

- 每次脚本执行写日志；先看日志里的 `OPEN_MODEL` / `OPEN_POST` / `SAVED`。
- 若 `Post.openPostWindow` 抛出异常，先确认模型是否真的加载完成，再确认 `model_name` 是否与 XML 内物理场名完全一致。
- 若输出是空白图，检查 `sp.setDraw(True)`、`sp.show()` 和 `Post.setView("SolidView")` 是否在 save 前执行。
