# Report Integration: Replace DOCX Figures with Native Post PNGs

## What to inspect first

```python
from docx import Document
doc = Document(source_docx)
print(len(doc.inline_shapes), len(doc.tables), len(doc.paragraphs))
for i, sh in enumerate(doc.inline_shapes):
    print(i, sh.width.cm, sh.height.cm)
```

- `inline_shapes` 按文档顺序排列；报告前 N 张图通常是 `inline_shapes[0..N-1]`。
- 图片实际存放在 `/word/media/imageN.png`，通过 `rId` 关联到 inline shape。
- 后续的对比图、示意图不要动；只替换要改的前 N 张。

## Replace image binary in place

```python
from docx import Document
from docx.shared import Cm

doc = Document(source_docx)
for i, path in enumerate(image_paths):
    sh = doc.inline_shapes[i]
    rId = sh._inline.graphic.graphicData.pic.blipFill.blip.embed
    part = doc.part.related_parts[rId]
    part._blob = open(path, "rb").read()

    # 16:9 native PNG, keep 15.6 cm width; height from pixel aspect
    sh.width = Cm(15.6)
    sh.height = Cm(15.6 * 900.0 / 1600.0)
doc.save(output_docx)
```

关键点：

- 直接改 `part._blob`，不要改 `rId`，也不要新增图片关系。
- 新图必须是同格式（PNG 换 PNG）；JPEG 换 PNG 会留下错误的 content type。
- 宽高必须同时按新图比例设置，否则 Word 会拉伸。原生图 1600×900，15.6 cm 宽对应 8.78 cm 高。
- 不要裁剪原生图去适配旧图框；保留原生 legend 和左上角标注。

## Text replacements

图题、章节导语和表格说明要和图片同口径。推荐按前缀定位，不依赖绝对段号：

```python
def set_text(p, text):
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ""

for p in doc.paragraphs:
    if p.text.strip().startswith("图 1"):
        set_text(p, "图 1  冷段 1800 s 外表面温度云图（INTESIM Post 原生，色标 −40.00～20.00 ℃）")
```

表格单元格按完整旧文本精确匹配：

```python
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            if cell.text.strip() == "本次实算节点场投影":
                set_text(cell.paragraphs[0], "INTESIM Post 原生后处理云图")
```

## Caption and legend consistency

- 图题写“INTESIM Post 原生”，不要写“节点投影”。
- 色标范围照图内 legend 写；若图内 legend 下限与完整结果 Tmin 不一致，在图题或导语里加注，例如：
  “图内色标 20.00～85.00 ℃；完整结果 Tmin 1.00 ℃ 的孤立节点不在当前显示组件集合内。”
- 位移图内 legend 单位是 m，正文和表格换算成 mm，并在图题中写清对应范围。

## Locked DOCX

Word 打开 DOCX 时会在同目录生成 `~$原文件名.docx`。此时 `doc.save(原路径)` 会抛 `PermissionError: [Errno 13] Permission denied`。

处理顺序：

1. 优先关闭 Word，再原地保存；保存前保留 `SOURCE_DOCX.docx` 备份。
2. 不能关闭时，另存为新文件名（例如 `..._原生Post云图版.docx`），不要反复重试覆盖。
3. `scripts/replace_docx_figures.py` 已内置 fallback：输出被占用时自动保存为 `output + fallback_suffix + .docx`。

## Package-size sanity check

原生 PNG 是未压缩的，1600×900 单张约 5.77 MB；DOCX 内部 ZIP 可把它压到几十 KB。六张图的新 DOCX 可能只有 0.5–0.7 MB，这是正常的，不要误判为图片没写入。需要核验时直接检查：

```python
import zipfile
z = zipfile.ZipFile(docx_path)
for info in z.infolist():
    if info.filename.startswith("word/media/"):
        print(info.filename, info.file_size, info.compress_size)
```

六张原生图的 `file_size` 应各约 5,770,190 字节（1600×900 未压缩 PNG）。
