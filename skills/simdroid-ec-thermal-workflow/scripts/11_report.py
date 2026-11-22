import csv
import datetime
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from ec_paths import P

SUM = P("files.summary_csv", r"D:\mcp-servers\ec-api\QR-V23_EC\温度结果汇总.csv")
IMG = P("files.report_img", r"D:\mcp-servers\ec-api\QR-V23_EC\report_img")
DOC = P("files.report_docx", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_稳态热仿真报告.docx")
PROJ = P("files.v5", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v5.simec")

rows = list(csv.DictReader(open(SUM, encoding='utf-8-sig')))
rows = [r for r in rows if r.get("最高温_C")]
rows.sort(key=lambda r: float(r["最高温_C"]), reverse=True)
print("零件:", len(rows))

def g(prefix):
    for r in rows:
        if r["零件标签"].startswith(prefix):
            return r
    return None

def fnum(r, k):
    try:
        return float(r[k])
    except (KeyError, TypeError, ValueError):
        return float('nan')

fpc = g("FPC tape_1")
frame = g("Frame 01")
lgp = g("LGP_1")
box_solid = g("BOX_SOLID")
box_dbef = g("BOX_DBEF")
box_bef = g("BOX_BEF")
box_diff = g("BOX_DIFF")
box_ref = g("BOX_REF_2")
tiekuang = g("PRT0029")

fpc_max = fnum(fpc, "最高温_C") if fpc else float('nan')
fpc_avg = fnum(fpc, "平均温_C") if fpc else float('nan')
frame_max = fnum(frame, "最高温_C") if frame else float('nan')
frame_avg = fnum(frame, "平均温_C") if frame else float('nan')
lgp_max = fnum(lgp, "最高温_C") if lgp else float('nan')
lgp_avg = fnum(lgp, "平均温_C") if lgp else float('nan')

# ---------- 文档样式 ----------
doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.2)
sec.bottom_margin = Cm(2.2)
sec.left_margin = Cm(2.4)
sec.right_margin = Cm(2.4)

st = doc.styles['Normal']
st.font.name = '宋体'
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

for lvl, size in ((1, 16), (2, 13), (3, 11)):
    h = doc.styles['Heading %d' % lvl]
    h.font.name = '黑体'
    h.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    h.font.size = Pt(size)
    h.font.color.rgb = RGBColor(0, 0, 0)
    h.font.bold = True

def P_(text='', bold=False, size=10.5, align=None, space_after=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.font.size = Pt(size)
    if align == 'center':
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(space_after)
    return p

def bullet(text, size=10.5):
    p = doc.add_paragraph(text, style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    for r in p.runs:
        r.font.size = Pt(size)
    return p

def table(head, data, widths=None, font_size=8.5):
    t = doc.add_table(rows=1, cols=len(head))
    t.style = 'Table Grid'
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(head):
        hdr[i].text = ''
        p = hdr[i].paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(font_size)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in data:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ''
            p = cells[i].paragraphs[0]
            r = p.add_run(str(v))
            r.font.size = Pt(font_size)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    return t

# ---------- 封面 ----------
P_("QR-V23-15.4 背光模组", bold=True, size=20, align='center', space_after=6)
P_("稳态热仿真报告", bold=True, size=26, align='center', space_after=18)
P_("Simdroid Electronic Cooling V2026.7.3", size=11, align='center', space_after=4)
P_("求解器版本 5.0R20260904（Quantum）", size=10, align='center', space_after=24)

info = [
    ("产品", "QR-V23-15.4 背光模组"),
    ("分析类型", "稳态、单相、Flow And Heat、DO 辐射、冻结流动"),
    ("工程文件", PROJ),
    ("热源", "60 颗 RF3014ZWH-EMC-F-GL，100 mA，总热功率 9.096 W"),
    ("环境温度", "25 ℃（环境与辐射温度相同）"),
    ("报告日期", datetime.date.today().isoformat()),
]
table(["项", "内容"], info, widths=[3.2, 12.0], font_size=9)

P_("")
P_("说明：本报告所有温度数值来自本次计算导出的 CSV/TXT；报告不替代设计评审，'
   '结论中的“未收敛/需补数据”必须随报告一起传递。", size=9)

doc.add_page_break()

# ---------- 1 摘要 ----------
doc.add_heading("1 摘要", level=1)
P_("本报告对 QR-V23-15.4 背光模组进行稳态热仿真，目标是评估 LED 工作时的 FPC、导光板、'
   '光学膜片与结构件的温度水平，为散热方案和材料选型提供依据。")

P_("主要结果：", bold=True, space_after=3)
bullet("FPC 最高温度 %.2f ℃，平均 %.2f ℃；热点位于 LED 条带附近。" % (fpc_max, fpc_avg))
bullet("Frame 01 最高 %.2f ℃，平均 %.2f ℃；BOX_SOLID 最高 %.2f ℃。" %
       (frame_max, frame_avg, fnum(box_solid, "最高温_C") if box_solid else float('nan')))
bullet("LGP 导光板最高 %.2f ℃，平均 %.2f ℃；膜片组最高温在 %.1f–%.1f ℃区间。" %
       (lgp_max, lgp_avg, fnum(box_diff, "最高温_C") if box_diff else float('nan'),
        fnum(box_bef, "最高温_C") if box_bef else float('nan')))
bullet("求解跑到 300 步上限，末步 T 残差约 107（阈值 30），最后 10 步监控点变化 ≤0.195 K；'
       '结果仍偏保守偏低，不能作为设计定案。")

P_("结论：当前方案在 100 mA 驱动下 FPC 已超过 100 ℃，需从 LED 热功率、FPC 铜箔面积/厚度、'
   'FPC 与框体贴合导热、辐射/对流边界四方面做优化；在 120 mA 驱动下热功率升至 11.508 W，'
   '温升预计再增 20–25%，必须重算后再评估。", bold=False)

# ---------- 2 项目概述 ----------
doc.add_heading("2 项目概述", level=1)
P_("QR-V23-15.4 为 15.4 英寸背光模组，主要结构包括下铁框、导光板（LGP）、FPC 灯条、'
   '反射/扩散/增亮膜片、胶带与泡棉辅料、镁合金/塑胶结构件。LED 采用 RF3014ZWH-EMC-F-GL，'
   '60 颗沿 FPC 条带布置。")

P_("分析目的：", bold=True, space_after=3)
bullet("量化 LED 工作时的 FPC、LGP、膜片、框体温度分布，识别热点位置。")
bullet("评估现有材料与结构在 100 mA 驱动下的热风险。")
bullet("为后续 120 mA 方案、FPC 铜箔优化、散热膜/石墨片方案提供基线。")

P_("分析范围：", bold=True, space_after=3)
bullet("稳态、单相、不可压缩流动；开启重力与 DO 辐射。")
bullet("流动采用冻结流场（FrozenFlowField=1），只解能量方程与辐射。")
bullet("不包含 LED 封装内部结温、荧光粉发热分布、瞬态开机温升。")

# ---------- 3 建模与简化 ----------
doc.add_heading("3 建模与简化", level=1)
P_("从 STEP 导入 59 个实体。由于伏图区域网格要求正交几何，直接对全部导入体剖分会报'
   '“模型中存在非正交元件，无法剖分网格”。本次按包围盒把 22 个薄壳/异形件替换为等效正交方块，'
   '并删除 15 个最小尺寸 <0.1 mm 的超薄辅料；最终 40 件参与计算（24 个保留 CAD + 16 个等效方块）。")
table(["阶段", "处理", "件数"],
      [["STEP 导入", "原始导入体", "59"],
       ["薄壳等效", "按 bbox 替换为 BOX_* 方块", "22"],
       ["超薄删除", "最小尺寸 <0.1 mm", "15"],
       ["最终参与", "导入体 + 方块", "40"]],
      widths=[4.0, 8.0, 3.0])

P_("简化说明：", bold=True, space_after=3)
bullet("等效方块保留原件的全局包围盒尺寸与材料，但丢失圆角、斜边、内部孔洞；对全局温度影响小，'
       '对界面局部热流有影响。")
bullet("叠层界面接触热阻未显式建模，界面按理想接触处理。")
bullet("FPC 按含铜约 20% 体积分数取等效 k=25 W/(m·K)；实际叠层需改正交各向异性。")
bullet("产品姿态按实际使用姿态导入；脚本不负责旋转，姿态错误会改变自然对流方向。")

# ---------- 4 材料 / 热源 / 边界 ----------
doc.add_heading("4 材料、热源与边界条件", level=1)
P_("4.1 材料参数", bold=True, space_after=3)
table(["材料", "k (W/m·K)", "发射率 ε", "主要用途"],
      [["PC", "0.3", "0.8", "LGP、膜片、塑胶件"],
       ["PET", "0.3", "0.8", "反射/扩散膜"],
       ["TAPE", "0.5", "0.8", "胶带"],
       ["FOAM", "0.15", "0.8", "遮光泡棉"],
       ["MG", "72", "0.5", "镁合金结构件"],
       ["SUS", "16.3", "0.3", "下铁框"],
       ["SIL", "0.3", "0.9", "硅胶/泡棉"],
       ["FPC", "25", "0.8", "FPC 载板（含铜 20%）"]],
      widths=[3.2, 4.2, 3.0, 5.5])

P_("4.2 热源", bold=True, space_after=3)
P_("60 颗 LED，单颗 100 mA 下输入功率 297 mW、辐射通量 145.4 mW、热功率 151.6 mW；'
   '总热功率 9.096 W，以 Total Source 形式施加在 FPC tape_1 上。")
P_("若按 120 mA 驱动：单颗热功率 191.8 mW，总热功率 11.508 W，温升预计再增 20–25%"
   '（估算，需重算确认）。", size=9)

P_("4.3 边界与模型", bold=True, space_after=3)
table(["项", "设置"],
      [["环境温度", "25 ℃"],
       ["辐射温度", "25 ℃"],
       ["辐射模型", "DO（离散坐标法）"],
       ["辐射面类型", "Agglomeration Radiating"],
       ["流动", "冻结流场（FrozenFlowField=1）"],
       ["重力", "开启"],
       ["求解域", "550.80 × 792.45 × 134.71 mm（X ±30%、Y +200%/−50%、Z ±300%）"],
       ["域边界", "六面 Open（工程默认；换项目需核对）"]],
      widths=[4.0, 11.5])

# ---------- 5 网格 ----------
doc.add_heading("5 网格", level=1)
P_("最终网格在 v5 工程重新剖分：全局最小 0.1 mm、最大 6 mm，最大长宽比上限 100。")
table(["指标", "值"],
      [["总单元", "553,563（流体 514,950 / 固体 38,613）"],
       ["最小 / 最大尺寸", "0.1 / 6 mm"],
       ["最大长宽比", "274,234"],
       ["最大偏斜度", "0"],
       ["最大非正交度", "0.025"],
       ["劣质面（>70°）", "0"],
       ["状态", "Mesh is valid"]],
      widths=[5.0, 10.5])
P_("长宽比极大来自薄壁切片（0.1 mm 层厚、6 mm 面内尺寸），不是网格畸变；非正交度与偏斜度均为 0，'
   '全局温度可用。对局部热流/界面温差的精度需做网格无关性确认。", size=9)

# ---------- 6 求解与收敛 ----------
doc.add_heading("6 求解与收敛", level=1)
P_("求解类型为稳态、单相、Flow And Heat；辐射 DO 每 5 步更新；采用 8 进程并行。")
table(["项", "值"],
      [["最大迭代", "300（v5 设置）"],
       ["监控点收敛", "开启，温度精度 0.1 ℃，残差阈值 30"],
       ["实际计算", "300 步，约 20 min 59 s"],
       ["末步 T 残差", "约 107（未达阈值 30）"],
       ["最后 10 步监控点变化", "≤ 0.195 K"],
       ["收敛判定", "未收敛；结果偏保守偏低"]],
      widths=[5.0, 10.5])
P_("收敛说明：300 步是上限，不等于收敛。199→300 步热点普遍再升约 4 K；若作为设计定案，'
   '应继续加步到 400–500 或调松弛/网格，直到残差 <30，并做网格无关性。", size=9)

doc.add_page_break()

# ---------- 7 结果 ----------
doc.add_heading("7 温度结果", level=1)
P_("7.1 关键零件温度", bold=True, space_after=3)
key_rows = []
for key in (fpc, frame, box_solid, box_dbef, box_bef, box_diff, box_ref, tiekuang, lgp):
    if key:
        key_rows.append([key["零件标签"], key["类型"],
                         "%.2f" % fnum(key, "最高温_C"),
                         "%.2f" % fnum(key, "平均温_C"),
                         "%.2f" % fnum(key, "最低温_C")])
table(["零件", "类型", "最高 ℃", "平均 ℃", "最低 ℃"], key_rows,
      widths=[6.0, 3.0, 3.0, 3.0, 3.0])

P_("7.2 全部零件排序（前 18 件）", bold=True, space_after=3)
top_rows = [[r["零件标签"], r["类型"], "%.2f" % fnum(r, "最高温_C"),
             "%.2f" % fnum(r, "平均温_C")] for r in rows[:18]]
table(["零件", "类型", "最高 ℃", "平均 ℃"], top_rows, widths=[7.5, 3.0, 3.5, 3.5])

P_("7.3 监控点曲线", bold=True, space_after=3)
p = os.path.join(IMG, "chart_monitor.png")
if os.path.exists(p):
    doc.add_picture(p, width=Cm(16.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    P_("图 1 监控点温度随迭代变化。MP_LGP/MP_PANEL 落在流体，恒为环境温度，不用于判定板面/屏面温度。", size=9, align='center')

P_("7.4 零件最高温 / 平均温", bold=True, space_after=3)
p = os.path.join(IMG, "chart_parts.png")
if os.path.exists(p):
    doc.add_picture(p, width=Cm(15.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    P_("图 2 关键零件最高温与平均温排序。", size=9, align='center')

P_("7.5 LED 条带温度", bold=True, space_after=3)
p = os.path.join(IMG, "chart_strip.png")
if os.path.exists(p):
    doc.add_picture(p, width=Cm(16.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    P_("图 3 LED 条带沿线最高温度（y≈−108.96 mm）。", size=9, align='center')

P_("7.6 LGP 导光板温度", bold=True, space_after=3)
p = os.path.join(IMG, "map_lgp.png")
if os.path.exists(p):
    doc.add_picture(p, width=Cm(14.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    P_("图 4 LGP 导光板温度分布（4 mm 网格，取单元最大值）。", size=9, align='center')

P_("7.7 温度分布", bold=True, space_after=3)
p = os.path.join(IMG, "map_top.png")
if os.path.exists(p):
    doc.add_picture(p, width=Cm(16.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    P_("图 5 背光模组俯视温度分布（体数据重构，非 EC 原生云图）。", size=9, align='center')

# ---------- 8 结论与风险 ----------
doc.add_heading("8 结论与风险", level=1)
P_("8.1 结论", bold=True, space_after=3)
bullet("100 mA、9.096 W 下，FPC 最高 %.2f ℃、平均 %.2f ℃；Frame 01 最高 %.2f ℃；'
       'LGP 最高 %.2f ℃。热风险集中在 LED 条带与 FPC 局部。" %
       (fpc_max, fpc_avg, frame_max, lgp_max))
bullet("膜片组最高温 %.1f–%.1f ℃，低于 FPC，但长期高温会加速黄化/收缩，需结合材料耐温评估。" %
       (fnum(box_diff, "最高温_C") if box_diff else float('nan'),
        fnum(box_bef, "最高温_C") if box_bef else float('nan')))
bullet("当前计算未收敛（300 步、残差 107），结果偏保守偏低；不能作为设计定案，只能作为优化基线。")

P_("8.2 风险与数据缺口", bold=True, space_after=3)
bullet("LED 驱动电流未最终确认：100 mA 为 9.096 W，120 mA 为 11.508 W；后者温升预计再增 20–25%。")
bullet("FPC 等效 k=25 基于含铜 20% 估算；实际叠层需改正交各向异性并确认铜箔/覆盖膜厚度。")
bullet("叠层界面接触热阻未建模；等效方块抹平了界面细节，局部温差可能被低估。")
bullet("MP_LGP/MP_PANEL 落在流体，不能用于判定板面/屏面温度；需在实体内部重建监控点。")
bullet("设计限值缺失：LED 结温上限、LGP 平面度、膜片翘曲、屏面温度上限需设计输入。")
bullet("批处理未出 EC 原生云图；本报告图片为体数据重构，原生云图需 GUI 后处理。")

P_("8.3 建议", bold=True, space_after=3)
bullet("先确认驱动电流与 LED 规格，按 120 mA 重算一版。")
bullet("FPC 铜箔从 1 oz 加到 2 oz 或增加铜面积，降低面内扩散热阻；必要时贴石墨/铜箔均温。")
bullet("FPC 与下铁框之间增加导热垫/导热胶，把热量导到金属框。")
bullet("把求解步数加到 400–500，残差降到 <30，并做 0.1/0.15/0.2 mm 网格无关性。")
bullet("在 LGP、屏面实体内部建监控点，或用体数据统计替代。")

# ---------- 9 复现 ----------
doc.add_heading("9 复现路径", level=1)
P_("本报告由 Simdroid EC 脚本链 01–11 生成：01 导入 STEP → 02 包围盒 → 03 建模 → 04 薄件清理/网格 → '
   '05 DO+冻结流动/重划网格 → 06 求解 → 07 关键件 → 08 全零件统计 → 09 图表 → 10 温度图 → 11 报告。")
P_("复现命令：", bold=True, space_after=3)
P_("powershell -ExecutionPolicy Bypass -File .\\run_all_ec.ps1", size=9)
P_("只重跑后处理：powershell -ExecutionPolicy Bypass -File .\\run_all_ec.ps1 -From 6", size=9)
P_("配置：assets/project_config.json；物理参数在 03/04/05/07/09/10/11 中按表修改。", size=9)
P_("报告模板说明：本脚本是 QR-V23 案例模板，换产品必须改封面、组件前缀、日期、工序；'
   '数值以 温度结果汇总.csv 为准。", size=9)

# ---------- 页脚 ----------
sec = doc.sections[0]
footer = sec.footer.paragraphs[0]
footer.text = "QR-V23-15.4 稳态热仿真报告 | Simdroid EC V2026.7.3 | 生成日期 %s" % datetime.date.today().isoformat()
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
for r in footer.runs:
    r.font.size = Pt(8)

doc.save(DOC)
print("DONE 11 ->", DOC, os.path.getsize(DOC), "B")
