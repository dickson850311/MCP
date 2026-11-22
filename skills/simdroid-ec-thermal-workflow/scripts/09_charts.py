# -*- coding: utf-8 -*-
"""生成报告用图表（监控点曲线、零件最高温排行）与收敛统计"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ec_paths import P as CFG
import pymupdf as fitz

BASE = CFG("project_root", r"D:\mcp-servers\ec-api\QR-V23_EC")
IMG = CFG("files.report_img", os.path.join(BASE, "report_img"))
os.makedirs(IMG, exist_ok=True)
T_TXT = CFG("files.result_t", os.path.join(BASE, "QR-V23_v5", "Solving", "result", "T.txt"))

# ---- 读取监控点数据 ----
rows = []
with open(T_TXT, encoding="utf-8", errors="replace") as fp:
    for line in fp:
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 7:
            it = int(float(parts[1]))
            rows.append((it, [float(v) for v in parts[2:7]]))

names = ["MP_LED_C", "MP_LED_L", "MP_LED_R", "MP_LGP", "MP_PANEL"]
print("迭代数:", len(rows), "末次:", rows[-1][0])

# 收敛性：最后 10 步最大变化
d_last = max(abs(rows[-1][1][i] - rows[-11][1][i]) for i in range(5))
print("最后10步监控点最大变化: %.4f K" % d_last)
for i, n in enumerate(names):
    print("  %-10s 末值 %.2f K (%.2f C) 首个 %.2f K" % (n, rows[-1][1][i], rows[-1][1][i] - 273.15, rows[0][1][i]))

# ---- 图表1：监控点温度-迭代曲线 ----
W, H = 720, 420
M = 70
doc = fitz.open()
pg = doc.new_page(width=W, height=H)
xmin, xmax = rows[0][0], rows[-1][0]
ymin = min(min(r[1]) for r in rows) - 1
ymax = max(max(r[1]) for r in rows) + 1
def X(v): return M + (v - xmin) / (xmax - xmin) * (W - 2 * M)
def Y(v): return H - M - (v - ymin) / (ymax - ymin) * (H - 2 * M)
pg.draw_line((M, H - M), (W - M, H - M), color=(0, 0, 0), width=1)
pg.draw_line((M, M), (M, H - M), color=(0, 0, 0), width=1)
# 网格与刻度（温度 C）
for k in range(6):
    tv = ymin + (ymax - ymin) * k / 5
    y = Y(tv)
    pg.draw_line((M, y), (W - M, y), color=(0.85, 0.85, 0.85), width=0.5)
    pg.insert_text((M - 42, y + 4), "%.0f" % (tv - 273.15), fontsize=9)
for k in range(5):
    it = xmin + (xmax - xmin) * k / 4
    pg.insert_text((X(it) - 8, H - M + 16), "%d" % it, fontsize=9)
pg.insert_text((W / 2 - 40, H - 24), "Iteration", fontsize=10)
pg.insert_text((8, M - 30), "T (degC)", fontsize=10)

colors = [(0.85, 0.1, 0.1), (0.95, 0.55, 0.1), (0.9, 0.8, 0.1), (0.1, 0.4, 0.85), (0.1, 0.65, 0.3)]
for i in range(5):
    seq = [(X(r[0]), Y(r[1][i])) for r in rows]
    for a, b in zip(seq[:-1], seq[1:]):
        pg.draw_line(a, b, color=colors[i], width=1.4)
for i, n in enumerate(names):
    pg.insert_text((W - M - 130, M + 18 + 14 * i), n, fontsize=9, color=colors[i])
pg.insert_text((M, M - 12), "Monitor point temperature vs iteration", fontsize=11)
doc.save(os.path.join(IMG, "chart_monitor.pdf"))
pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
pix.save(os.path.join(IMG, "chart_monitor.png"))
doc.close()

# ---- 图表2：零件最高温排行 ----
import csv
rows2 = []
with open(os.path.join(BASE, "温度结果汇总.csv"), encoding="utf-8-sig") as fp:
    for r in csv.DictReader(fp):
        rows2.append((r["零件标签"], float(r["最高温_C"]), float(r["平均温_C"])))
rows2.sort(key=lambda x: -x[1])
rows2 = rows2[:18]
W2, H2 = 760, 500
M2 = 150
doc = fitz.open()
pg = doc.new_page(width=W2, height=H2)
vmax = rows2[0][1] + 2
bar_h = (H2 - 2 * 40) / len(rows2)
def X2(v): return M2 + v / vmax * (W2 - M2 - 40)
for k, (lab, mx, mean) in enumerate(rows2):
    y = 30 + k * bar_h
    pg.draw_rect(fitz.Rect(M2, y + 2, X2(mx), y + bar_h - 4), color=None, fill=(0.85, 0.25, 0.2))
    pg.draw_rect(fitz.Rect(M2, y + 2, X2(mean), y + bar_h - 4), color=None, fill=(0.2, 0.45, 0.8))
    pg.insert_text((8, y + bar_h / 2 + 3), lab[:26], fontsize=8)
    pg.insert_text((X2(mx) + 4, y + bar_h / 2 + 3), "%.1f" % mx, fontsize=8)
for k in range(6):
    v = vmax * k / 5
    pg.draw_line((X2(v), 26), (X2(v), H2 - 12), color=(0.88, 0.88, 0.88), width=0.5)
    pg.insert_text((X2(v) - 6, H2 - 2), "%.0f" % v, fontsize=8)
pg.insert_text((8, 18), "Max / mean temperature by part (degC)   red=max  blue=mean", fontsize=9)
doc.save(os.path.join(IMG, "chart_parts.pdf"))
pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
pix.save(os.path.join(IMG, "chart_parts.png"))
doc.close()
print("图表生成完成:", os.listdir(IMG))
