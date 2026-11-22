# -*- coding: utf-8 -*-
"""QR-V23-15.4 背光模组稳态热仿真报告 v3（300 步版本，数值全部取自本轮 CSV/TXT）"""
import os, csv, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ec_paths import P as CFG
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BASE = CFG("project_root", r"D:\mcp-servers\ec-api\QR-V23_EC")
IMG = CFG("files.report_img", os.path.join(BASE, "report_img"))
OUT = CFG("files.report_docx", os.path.join(BASE, "QR-V23-15.4_稳态热仿真报告_v3.docx"))

doc = Document()
st = doc.styles["Normal"]
st.font.name = "等线"
st.font.size = Pt(10.5)
st._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
for sec in doc.sections:
    sec.left_margin = Cm(2.2); sec.right_margin = Cm(2.2)
    sec.top_margin = Cm(2.0); sec.bottom_margin = Cm(2.0)

def H(text, level=1):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        r.font.name = "等线"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
        r.font.color.rgb = RGBColor(0x1F, 0x3B, 0x57)
    return p

def P(text, bold=False, size=10.5, space=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space)
    p.paragraph_format.line_spacing = 1.25
    r = p.add_run(text)
    r.bold = bold
    r.font.size = Pt(size)
    r.font.name = "等线"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
    return p

def TBL(headers, rows, fs=8.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(fs)
        r.font.name = "等线"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            r = p.add_run(str(v))
            r.font.size = Pt(fs)
            r.font.name = "等线"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i else WD_ALIGN_PARAGRAPH.LEFT
    return t

# ---------- 读数据 ----------
rows = []
with open(os.path.join(BASE, "温度结果汇总.csv"), encoding="utf-8-sig") as fp:
    for r in csv.DictReader(fp):
        for k in ("最低温_K", "最高温_K", "平均温_K", "最低温_C", "最高温_C", "平均温_C"):
            r[k] = float(r[k])
        r["单元数"] = int(r["单元数"])
        rows.append(r)
rows.sort(key=lambda r: -float(r["最高温_C"]))

def g(prefix):
    for r in rows:
        if r["零件标签"].startswith(prefix):
            return r
    raise KeyError(prefix)

def f(prefix, col="最高温_C"):
    return float(g(prefix)[col])

fpc = g("FPC tape")
frm = g("Frame 01")
sol = g("BOX_SOLID")
dbef = g("BOX_DBEF")
bef = g("BOX_BEF")
dif = g("BOX_DIFF")
ref = g("BOX_REF_2")
lgp = g("LGP_1")
tie = g("PRT0029")
blk = g("BLACK tapa-1003")
blk2 = g("BLACK tapa-1002")
tie2 = g("TIEZHI-1")
gst = g("BOX_GST-MID")

# ---------- 封面 ----------
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("\nQR-V23-15.4 背光模组\nLED 稳态热仿真分析报告")
r.bold = True; r.font.size = Pt(24); r.font.name = "等线"
r._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
P("")
info = [("产品型号", "QR-V23-15.4 背光模组（15.4 吋）"),
        ("分析类型", "稳态共轭传热（自然对流 + 离散坐标法 DO 辐射）"),
        ("求解软件", "伏图电子散热 Simdroid Electronic Cooling V2026.7.3（求解器 7.1）"),
        ("工程文件", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23_v5.simec"),
        ("求解设置", "8 进程并行，最大迭代步 300（本版按用户要求从 200 步提高到 300 步重算）"),
        ("计算日期", "2026-11-20（300 步本轮 20:42 启动、21:03 结束，求解耗时 21 min）"),
        ("工况", "LED 60 颗 × 100 mA，总热功率 9.096 W，环境 25 ℃，静止空气")]
TBL(["项目", "内容"], info, fs=9)
doc.add_page_break()

# ---------- 1 摘要 ----------
H("1  结论摘要", 1)
P("在 25 ℃ 静止空气、开启 DO 辐射、LED 总功耗 9.096 W 的条件下，跑满 300 步迭代后温度分布如下：")
TBL(["部位", "最高温度", "平均温度", "对应节点/说明"],
    [["FPC / LED 载板", "%.1f ℃" % fpc["最高温_C"], "%.1f ℃" % fpc["平均温_C"], "LED 所在条带，全局最热点"],
     ["塑胶边框 Frame 01", "%.1f ℃" % frm["最高温_C"], "%.1f ℃" % frm["平均温_C"], "仅靠 LED 一侧局部过热，其余接近环境"],
     ["等效 SOLID 壳体", "%.1f ℃" % sol["最高温_C"], "%.1f ℃" % sol["平均温_C"], "原 SOLID 薄膜件以正交块替代"],
     ["上增亮膜 DBEF", "%.1f ℃" % dbef["最高温_C"], "%.1f ℃" % dbef["平均温_C"], "等效块，膜层热阻未真实建模"],
     ["导光板 LGP", "%.1f ℃" % lgp["最高温_C"], "%.1f ℃" % lgp["平均温_C"], "板面大部分接近环境，仅靠 LED 端升温"],
     ["下铁框 PRT0029", "%.1f ℃" % tie["最高温_C"], "%.1f ℃" % tie["平均温_C"], "金属件，导热好、温度梯度小"],
     ["遮光胶带 BLACK tapa", "%.1f ℃" % blk["最高温_C"], "%.1f ℃" % blk["平均温_C"], "贴 LED 附近，整段温度较均匀"]],
    fs=8.5)
P("要点：热量高度集中在 FPC 上 LED 所在的一条窄带（宽 0.13 mm、长 333.9 mm），局部热流密度极大，"
  "FPC 表面出现 %.1f ℃ 热点；热量沿铁框与边框向四周扩散后迅速衰减，模组大部分区域仍接近 25 ℃ 环境。"
  % fpc["最高温_C"], space=8)

# ---------- 2 概述 ----------
H("2  项目概述与目标", 1)
P("目标：给出 QR-V23-15.4 背光模组在额定电流下的稳态温度分布，重点回答三个问题——"
  "① LED 区域（FPC 载板）温度水平；② 导光板与屏面（膜片组）受热程度；"
  "③ 下铁框、塑胶边框等结构件是否超过材料耐温。")
P("输入资料：STEP 几何 QR-V23-15.4 2024-6-12.stp（59 个零件）、BOM 表、"
  "LED 规格书 RF3014ZWH-EMC-F-GL（100 mA 单颗热功率 151.60 mW）。")

# ---------- 3 建模 ----------
H("3  建模与简化口径", 1)
P("3.1  几何", bold=True, space=2)
P("STEP 导入后共 59 个零件，整体包围盒 344.25 × 226.42 × 19.24 mm；导光板 334.86 × 214.19 × 3.09 mm，"
  "FPC 条带 333.9 × 0.13 × 3.47 mm（位于 y ≈ −108.96 mm）。")
P("3.2  简化（关键，直接影响结果可信度）", bold=True, space=2)
TBL(["简化项", "做法", "影响"],
    [["22 件薄膜/壳体类零件", "按其精确包围盒替换为等效正交方块（BOX_ 前缀），保留原厚度与位置",
      "膜层内部导热被“等效均匀化”，界面接触热阻消失，膜片温度偏高"],
     ["15 件厚度 < 0.1 mm 辅料", "剔除（各类胶带、标签、薄涂层）",
      "减少薄壁切片，但对局部热桥有轻微影响"],
     ["最终参与计算零件", "40 件（24 个导入体 + 16 个等效块）", "—"]],
    fs=8.5)
P("说明：这样处理的直接原因是原始 CAD 中 12 个装配体（SOLID、REF、DIFF/BEF/DBEF、6 条膜片胶带、GST/遮光泡棉）"
  "被网格器判定为“非正交元件”，无法生成 cut-cell 网格；替换为正交块后网格通过，代价是膜层热阻不真实。", space=8)
P("3.3  求解域", bold=True, space=2)
P("按宽 ±30%、正高 +200%、负高 −50%、厚 ±300% 扩张，得到 550.80 × 792.45 × 134.71 mm 的计算域；"
  "6 个外边界均设为 Open（0 m/s、0 Pa、25 ℃）。")

# ---------- 4 材料 ----------
H("4  材料、热源与边界条件", 1)
TBL(["材料", "导热系数 k (W/m·K)", "发射率 ε", "用于零件"],
    [["PC", "0.3", "0.8", "导光板、膜片、塑胶边框"],
     ["PET", "0.3", "0.8", "反射/扩散膜"],
     ["TAPE 胶带", "0.5", "0.8", "各类胶带"],
     ["FOAM 泡棉", "0.15", "0.8", "GST 遮光泡棉"],
     ["Mg 镁合金", "72", "0.5", "结构件（未处理铝按 0.5）"],
     ["SUS304", "16.3", "0.3", "下铁框"],
     ["FPC（含铜 20%）", "25", "0.8", "FPC 载板"]],
    fs=8.5)
P("热源：Total Source 类型施加于 FPC tape_1，总量 9.096 W（60 颗 × 151.60 mW，100 mA）。", space=4)
P("辐射：DO 模型，参与面按“聚合面辐射（Agglomeration Radiating）”处理，环境与辐射温度均 25 ℃。", space=4)
P("流动：自然对流，重力 9.81 m/s² 竖直向下；6 面开口边界绑定 Constant 条件。", space=8)

# ---------- 5 网格 ----------
H("5  网格", 1)
TBL(["指标", "数值"],
    [["总单元数", "553,563（流体 514,950 / 固体 38,613）"],
     ["最小 / 最大尺寸", "0.1 mm / 6 mm"],
     ["最大长宽比", "274,234（薄片切片导致）"],
     ["最大偏斜度", "0"],
     ["最大非正交度", "0.025"],
     ["劣质面（>70°）", "0"],
     ["网格状态", "Mesh is valid"]],
    fs=8.5)
P("网格质量提示：BOX_REF-L-R、BOX_REF-TOP 两个 0.125 mm 薄壁把最小单元压到 0.06 mm，"
  "长宽比因此极大；对温度场影响有限，但对局部热流精度有影响。", space=8)

# ---------- 6 求解与收敛 ----------
H("6  求解设置与收敛性", 1)
TBL(["设置项", "取值"],
    [["求解类型", "稳态、单相、Flow And Heat"],
     ["辐射", "DO，每 5 步更新一次"],
     ["并行核数", "8（在【选项】→【对象相关】中设置；日志确认 Total processes 8 / threads 8）"],
     ["最大迭代步", "300（本轮按要求由 200 改为 300）"],
     ["温度收敛判据", "监控点 0.1 ℃ / 残差阈值 30"],
     ["实际计算", "跑满 300 步（达步数上限），求解耗时 20 min 59 s"],
     ["末步 T 残差", "107（未达 30 阈值）"],
     ["最后 10 步监控点变化", "≤ 0.195 K"]],
    fs=8.5)
P("判定：300 步后温度仍在缓慢单调上升（LED 中部监控点每步约 +0.02 K），残差由 199 步时的约 145 降到 107，"
  "仍未达到 30 的收敛阈值。因此本版结果比 199 步版整体高约 4 K，但仍属于“温度尚未完全稳定”的偏保守偏低估计，"
  "不能当作极限工况的最终判据。", bold=True, space=6)

# ---------- 7 结果 ----------
H("7  计算结果", 1)
P("7.1  监控点（第 299 步采样）", bold=True, space=2)
TBL(["监控点", "位置说明", "温度 (℃)"],
    [["MP_LED_C", "LED 条带中部", "98.3"],
     ["MP_LED_L", "LED 条带左端", "91.8"],
     ["MP_LED_R", "LED 条带右端", "89.0"],
     ["MP_LGP", "导光板中心（落在流体单元，不可用）", "25.7"],
     ["MP_PANEL", "屏面中心（落在流体单元，不可用）", "25.7"]],
    fs=8.5)
P("注：MP_LGP / MP_PANEL 从第 1 步起即基本恒等于环境温度，判断监控点落在空气域而非固体单元，"
  "因此导光板与屏面温度以下面的零件体数据统计为准。", space=6)

P("7.2  监控点温度随迭代的演化（0→300 步）", bold=True, space=2)
doc.add_picture(os.path.join(IMG, "chart_monitor.png"), width=Cm(15.5))
P("图 7-1  LED 条带三点与两个可疑监控点的温度演化（纵轴 ℃，横轴迭代步）", size=8.5, space=8)

P("7.3  各零件温度排行", bold=True, space=2)
doc.add_picture(os.path.join(IMG, "chart_parts.png"), width=Cm(15.5))
P("图 7-2  零件最高温（红）与平均温（蓝）对比（前 18 项）", size=8.5, space=8)

P("7.4  关键零件温度明细（完整 40 件见附表 CSV）", bold=True, space=2)
sel = [r for r in rows if any(k in r["零件标签"] for k in
        ("FPC tape", "Frame 01", "BOX_SOLID", "DBEF", "BEF", "DIFF", "LGP_1", "PRT0029",
         "BLACK tapa", "TIEZHI", "GST-MID", "FOG-GST-B", "REF_2"))][:14]
TBL(["零件", "最高 ℃", "平均 ℃", "最低 ℃"],
    [[r["零件标签"][:26], r["最高温_C"], r["平均温_C"], r["最低温_C"]] for r in sel], fs=8.5)

P("7.5  温度分布图（由导出体数据重构）", bold=True, space=2)
doc.add_picture(os.path.join(IMG, "chart_strip.png"), width=Cm(15.5))
P("图 7-3  LED 条带（FPC）沿线温度包络：中段 95–105 ℃，峰值 %.1f ℃，两端降至 81–83 ℃。" % fpc["最高温_C"],
  size=8.5, space=6)
doc.add_picture(os.path.join(IMG, "map_lgp.png"), width=Cm(15.5))
P("图 7-4  导光板板面温度分布（4 mm 网格取单元最大值）：除靠近 LED 的下边缘一条窄带外，整板基本维持在 25 ℃ 附近。",
  size=8.5, space=6)
P("说明：以上两图由 result.h5 导出的体数据（145,312 个采样点）重构，非软件界面渲染的云图；"
  "伏图原生云图需要在界面里生成，无界面批处理模式下只能输出占位图片。", size=8.5, space=8)

P("7.6  迭代步数敏感性（199 步 vs 300 步）", bold=True, space=2)
TBL(["部位（最高温）", "199 步 (℃)", "300 步 (℃)", "增量 (K)"],
    [["FPC / LED 载板", "103.1", "%.1f" % fpc["最高温_C"], "+%.1f" % (fpc["最高温_C"] - 103.09)],
     ["塑胶边框 Frame 01", "101.9", "%.1f" % frm["最高温_C"], "+%.1f" % (frm["最高温_C"] - 101.86)],
     ["等效 SOLID 壳体", "100.9", "%.1f" % sol["最高温_C"], "+%.1f" % (sol["最高温_C"] - 100.91)],
     ["DIFF 扩散膜", "92.8", "%.1f" % dif["最高温_C"], "+%.1f" % (dif["最高温_C"] - 92.84)],
     ["BEF 增亮膜", "92.2", "%.1f" % bef["最高温_C"], "+%.1f" % (bef["最高温_C"] - 92.18)],
     ["DBEF 上增亮膜", "91.3", "%.1f" % dbef["最高温_C"], "+%.1f" % (dbef["最高温_C"] - 91.28)],
     ["导光板 LGP", "80.9", "%.1f" % lgp["最高温_C"], "+%.1f" % (lgp["最高温_C"] - 80.87)],
     ["下铁框 PRT0029", "74.3", "%.1f" % tie["最高温_C"], "+%.1f" % (tie["最高温_C"] - 74.29)]],
    fs=8.5)
P("结论：多跑 101 步后各热点普遍再升高约 4 K，且末步仍在上涨，说明 200 步版本是系统性偏低；"
  "若需作为定案数据，建议继续加步（400–500 步）或调整松弛因子/收敛阈值后复算。", space=8)

# ---------- 8 结论 ----------
H("8  结论与风险说明", 1)
P("8.1  可判定的结论", bold=True, space=2)
P("① LED 区域是唯一显著热区：FPC 载板表面最高 %.1f ℃、平均 %.1f ℃，热点与 LED 排布条带重合；"
  "② 结构件中塑胶边框局部 %.1f ℃、下铁框最高 %.1f ℃，金属件温差小、散热路径通畅；"
  "③ 导光板整体平均仅 %.1f ℃，热量没有明显传导到板面中心，最热点出现在靠 LED 的端部（%.1f ℃）；"
  "④ 膜片组（DIFF/BEF/DBEF）最高 %.1f–%.1f ℃，集中在 LED 侧端部。"
  % (fpc["最高温_C"], fpc["平均温_C"], frm["最高温_C"], tie["最高温_C"],
     lgp["平均温_C"], lgp["最高温_C"], dif["最高温_C"], dbef["最高温_C"]), space=6)
P("8.2  需补数据才能判定", bold=True, space=2)
P("① LED 结温：本次只有 LED 载板表面温度，缺少 LED 封装 Rth(j-s) 与焊盘结构，不能直接换算结温；"
  "② 屏面（面板）温度：监控点落在流体域失效，需在面板实体内部另设监控点重算；"
  "③ 驱动电流口径：现按 100 mA（9.096 W），若实际为 120 mA 则热功率升至 11.508 W，温升约再增 20–25%。", space=6)
P("8.3  不可判定 / 结果风险", bold=True, space=2)
P("① 膜片、胶带以等效正交块替代，层间接触热阻与真实膜层导热被抹平，膜片温度存在偏差；"
  "② 15 件 <0.1 mm 辅料被剔除，局部热桥缺失；"
  "③ 网格长宽比过大（薄壁切片），局部热流精度受限；"
  "④ 300 步仍因步数上限停止，残差 107 未达判据，温度仍在缓慢上升，本版数值偏低。", space=6)
P("建议：若要用于设计定案，需按 8.2 补齐 LED 结温模型与屏面监控点，把膜片改为真实薄层网格或分层导热系数，"
  "并把最大迭代步提到 400 以上、确认 T 残差降到 30 以下再取结果。", bold=True, space=8)

# ---------- 9 复现 ----------
H("9  复现路径", 1)
P("工程：D:\\mcp-servers\\ec-api\\QR-V23_EC\\QR-V23_v5.simec（最大迭代步 300 已保存）", size=9)
P("结果：QR-V23_v5\\Solving\\result\\result.h5（190,837,662 B，2026-11-20 21:03:50）、"
  "result\\T.txt（监控点曲线）、Residual(T|U|p_rgh).txt（残差）", size=9)
P("统计：D:\\mcp-servers\\ec-api\\QR-V23_EC\\温度结果汇总.csv（40 件最值/均值，本轮重算）", size=9)
P("界面复现：打开工程 → 分析页签【求解器控制】把“迭代步数 最大”设为 300 → 【重新初始化并计算】；"
  "核数在【文件】→【选项】→【对象相关】→ 并行核数 = 8。", size=9)

doc.save(OUT)
print("报告生成:", OUT, os.path.getsize(OUT))
