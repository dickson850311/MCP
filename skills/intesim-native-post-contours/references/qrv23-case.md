# QR-V23 Native Post Case

这是一个已经跑通并交付的完整案例，可作为配置示例。工程路径和数值仅用于复现，不要写死到其他项目。

## Inputs

| Case | Model XML | Result `.res.inp` | Physics model |
|---|---|---|---|
| thermal_cold | `D:\mcp-servers\intesim-mcp\projects\QRV23_AUTO_thermal_cold.model_1.model.xml` | `...\QRV23_AUTO_thermal_cold.model_1.model.res\QRV23_AUTO_thermal_cold.model_1.model_partition0_M_Thermal_Auto_th_0016.res.inp` | `M_Thermal_Auto` |
| thermal_hot | `...\QRV23_AUTO_thermal_hot.model_1.model.xml` | `...\QRV23_AUTO_thermal_hot.model_1.model.res\...M_Thermal_Auto_th_0016.res.inp` | `M_Thermal_Auto` |
| struct_cold | `...\QRV23_AUTO_struct_cold.model_1.model.xml` | `...\QRV23_AUTO_struct_cold.model_1.model.res\...M_Struct_Auto_advso_0001.res.inp` | `M_Struct_Auto` |
| struct_hot | `...\QRV23_AUTO_struct_hot.model_1.model.xml` | `...\QRV23_AUTO_struct_hot.model_1.model.res\...M_Struct_Auto_advso_0001.res.inp` | `M_Struct_Auto` |

网格：63,549 节点 / 190,981 Tet4；29 个组件；冷段 1800 s，热段 1800 s。

## Figures

| # | Output | Scalar | adapter | component IDs | min / max | beam/shell |
|---|---|---|---:|---|---|---|
| 1 | `native_thermal_cold.png` | `temperature` | 0 | 1–29 | −40.0 / 20.0 | True |
| 2 | `native_thermal_hot.png` | `temperature` | 0 | 1–29 | 1.0 / 85.0 | True |
| 3 | `native_struct_cold_UZ.png` | `displacement z` | 2 | 1–29 | −9.61697336e-06 / 2.07523272e-05 | False |
| 4 | `native_struct_cold_US.png` | `displacement sum` | 3 | 1–29 | 0.0 / 7.74211994e-04 | False |
| 5 | `native_struct_hot_UZ.png` | `displacement z` | 2 | 1–29 | −2.25105012e-05 / 1.03721667e-05 | False |
| 6 | `native_struct_hot_US.png` | `displacement sum` | 3 | 1–29 | 0.0 / 8.38730761e-04 | False |

输出目录：`D:\mcp-servers\intesim-mcp\tools\qrv23_auto_figs`；每张 1600×900，未压缩 PNG 约 5,770,190 字节。

## Results used in captions

- thermal_cold：Tmin −40.00 ℃ / Tmax 20.00 ℃ / Tmean −2.2366 ℃；图内 legend −4.0e+01～2.0e+01。
- thermal_hot：Tmin 1.00 ℃ / Tmax 85.00 ℃ / Tmean 44.0884 ℃；图内 legend 2.0e+01～8.5e+01。
- struct_cold：|U|max 0.774212 mm；UX −0.653053～+0.652921 mm；UY −0.417323～+0.418049 mm；UZ −0.009617～+0.020752 mm。
- struct_hot：|U|max 0.838731 mm；UX −0.707331～+0.707476 mm；UY −0.452887～+0.452102 mm；UZ −0.022511～+0.010372 mm。

热段 legend 下限显示 20.00 ℃，是因为 1.00 ℃ 的孤立节点不在当前 Post 显示组件集合内；完整结果统计的 Tmin 仍是 1.00 ℃。图题写“色标 20.00～85.00 ℃”，导语加注两者不矛盾。

## DOCX mapping

原报告 `瀚达美_QR-V23_POC冷热冲击_INTESIM实算报告.docx`：

- 7 个 inline shape：前 6 个依次对应图 1–6，第 7 个是 `compare.png`。
- 图片部件 `/word/media/image1.png`～`image6.png`，`rId11`～`rId16`。
- 原图宽 15.6 cm，高 9.52～9.86 cm。
- 第 67 段是第 4 章导语；图题在第 71、75、79、81、85、87 段。
- 表 1（`doc.tables[1]`）第 7 行第 2 列原为“本次实算节点场投影”。

替换后：

- 6 张图统一 15.6 cm 宽、8.78 cm 高（16:9）。
- 图题全部改为“INTESIM Post 原生”。
- 表 1“云图来源”改为“INTESIM Post 原生后处理云图”。
- 原稿被 Word 占用时另存为 `..._原生Post云图版.docx`。

## Commands used

主 GUI 控制台：

```python
Window.closePostWindow(); time.sleep(2)
Mesh.openFile(r"...\QRV23_AUTO_thermal_cold.model_1.model.xml"); time.sleep(10)
Post.openPostWindow(r"...\...M_Thermal_Auto_th_0016.res.inp", "M_Thermal_Auto")
time.sleep(4)
Post.setBeamAndShell3DView(True)
# newScalar / PlotSetting / savePicture
```

结构工况同一模型连续出两张图：打开一次 Post，先 `newScalar` 出 UZ，再 `newScalar` 出 |U|，不需要重新打开模型。

## Observed output

- 温度图呈大面积单色 + 少量异色节点，因为 29 个组件之间没有绑定/热接触，冷、热外表面与内部界面之间存在温度跳变；这是真实结果。
- 结构图左右外侧圆环略有裁边，主体和色标完整。
- 图内 legend、左上角 `Physics Model` / `step` / `time` 标注均保留。
