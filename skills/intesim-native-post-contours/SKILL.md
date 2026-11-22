---
name: intesim-native-post-contours
description: 从 INTESIM 8.0 已求解的 .res.inp 结果文件导出原生 Post 云图（温度、位移 UZ/|U|、应力等），并把 DOCX 报告中的 Python/matplotlib 节点投影图替换为 Post.savePicture 原生 PNG。Use when the user asks for “INTESIM 原生后处理云图”“Post 云图”“原生 Post 截图”，wants to replace report figures with native Post captures, or needs batch export of thermal/structural contours from INTESIM results. Covers model XML preload, Post window workflow, NodalScalar setup, 1600×900 export, python-docx image replacement, and known crash/crop/legend pitfalls.
---

# INTESIM Native Post Contours

目标：把 INTESIM 求解结果变成 **Post 原生图**，再写回 DOCX。不要用 matplotlib 从 `.res.inp` 画节点投影来冒充原生云图。

## Output contract

- PNG 必须由 `Post.savePicture` 导出，保留 Post 原生模型轮廓、色标、视角，以及左上角 model / step / time 标注。
- DOCX 中按 inline shape 顺序替换前 N 张图；图题、章节导语、表格“云图来源”同步修改。
- 正文与表格统一写清单位：温度 ℃，位移 m 在正文换算为 mm。
- 图题中的色标范围要与图内 legend 一致；若 legend 与完整结果统计不一致，必须加注，不能改图迁就文字。

## Preconditions

- 使用 INTESIM 8.0 **主 GUI** `D:\INTESIM8.0\GUI\intesim.exe`，不是 `Intesim-Post.exe`。
- 已有 `*.model_1.model.xml` 和对应的 `*.res.inp`；模型和结果来自同一次求解。
- 报告替换需要 `python-docx`，建议用 `D:\INTESIM8.0\Python38\python.exe`。
- Post 脚本必须在 GUI 底部脚本控制台执行，`Post` / `Window` / `Mesh` 是控制台注入的全局对象，不能当普通 Python 模块 import。
- **模型 XML 必须先加载**；没有加载模型就直接 `Post.openPostWindow` 会让主窗口崩溃。

## Workflow

1. 复制 `assets/post_export_config.example.json`，按工程填写 `cases`、模型 XML、`.res.inp`、scalar、色标和输出路径。
2. 在 INTESIM 主 GUI 底部控制台执行（Ctrl+Enter 执行，Enter 只换行）：

   ```python
   POST_EXPORT_CONFIG = r"D:\path\to\post_export_config.json"
   exec(open(r"D:\path\to\skills\intesim-native-post-contours\scripts\post_export.py", encoding="utf-8").read())
   ```

3. 检查输出 PNG：1600×900、legend 可见、模型未空白、左上角标注存在。若模型被裁，先看 `references/post-api.md` 的视口说明。
4. 复制 `assets/report_replace_config.example.json`，填写源 DOCX、输出 DOCX、图片顺序、图题/导语/表格替换规则。
5. 用带 python-docx 的 Python 执行：

   ```powershell
   & "D:\INTESIM8.0\Python38\python.exe" scripts\replace_docx_figures.py --config report_replace_config.json
   ```

6. 若源 DOCX 被 Word 占用（目录里有 `~$` 锁文件），脚本会尝试另存为 fallback 文件名；也可以先关闭 Word 再原地保存。

## Critical rules

- **先模型，后 Post**：`Window.closePostWindow()` → `Mesh.openFile(*.model_1.model.xml)` → 等待 10–15 s → `Post.openPostWindow(*.res.inp, model_name)`。
- **打开 `.model.xml`，不要只开 `.model`**；后者会显示 `0 Physics Models`，拿不到 `M_Thermal_Auto` / `M_Struct_Auto`。
- 切换模型前先 `Window.closePostWindow()`，否则旧 Post 上下文会干扰新模型。
- 热场用 `Post.setBeamAndShell3DView(True)` 看外表皮；结构场用 `False` 保留完整实体。
- `Post.savePicture` 用 **1600×900**；1600×1200 会因视口宽高比不匹配裁掉模型。
- `Post.lookAt(...)` 会把模型移出视口，不要用。
- `Post.setView('FitView')` 边缘裁切更严重；用 `Post.setView('SolidView')` + `Post.fitDirectionView(0,0,1,0,1,0,1.0)`。
- 结构图外围圆环可能轻微裁边，这是 16:9 视口与模型外形比例导致的；主体和色标完整即可，不要为了外环把 legend 挤出画面。
- 温度场出现“大面积单色 + 少量异色点”且组件间没有绑定/热接触时，这是真实分区结果，不要插值平滑。
- legend 最小值可能不等于完整结果 Tmin（例如 1.00 ℃ 孤立节点不在当前显示组件集合内）；在图题或导语中注明口径差异。
- `Post.savePicture` 在 1600×900 下输出的是未压缩 PNG，单张约 5.77 MB；报告 DOCX 的 ZIP 压缩率很高，不要据此判断图片没写进去。

## Bundled resources

- `scripts/post_export.py`：在 INTESIM GUI 控制台批量导出原生 PNG。
- `scripts/replace_docx_figures.py`：按 inline shape 顺序替换 DOCX 图片，并替换图题/导语/表格单元格。
- `references/post-api.md`：Post API、adapter ID、崩溃与视口问题的完整说明。
- `references/report-integration.md`：DOCX 图片 part 替换、锁文件、尺寸与图题口径。
- `references/qrv23-case.md`：QR-V23 四工况六张图的真实可复现案例与数值。
- `assets/post_export_config.example.json` / `assets/report_replace_config.example.json`：可直接复制的配置模板。

If the task starts before solving, use the existing INTESIM build/solve workflow first; this skill begins from an existing `.res.inp`.
