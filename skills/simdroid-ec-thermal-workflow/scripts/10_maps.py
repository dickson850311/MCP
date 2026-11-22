# -*- coding: utf-8 -*-
"""用导出的体数据绘制温度分布图（俯视投影最大值 + LED 条带温度曲线）"""
import os, csv, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ec_paths import P as CFG
import pymupdf as fitz

BASE = CFG("project_root", r"D:\mcp-servers\ec-api\QR-V23_EC")
ALL = CFG("files.temp_all", os.path.join(BASE, "temp_all"))
IMG = CFG("files.report_img", os.path.join(BASE, "report_img"))

pts = []  # (x, y, z, T)
for fn in os.listdir(ALL):
    if not fn.lower().endswith(".csv"):
        continue
    with open(os.path.join(ALL, fn), encoding="utf-8", errors="replace") as fp:
        rd = csv.reader(fp)
        started = False
        for r in rd:
            if not r:
                continue
            if r[0].strip().startswith("Point No."):
                started = True
                continue
            if not started or len(r) < 5:
                continue
            try:
                x, y, z, t = float(r[1]), float(r[2]), float(r[3]), float(r[4])
            except Exception:
                continue
            pts.append((x, y, z, t))
print("点数:", len(pts))

xmin = min(p[0] for p in pts); xmax = max(p[0] for p in pts)
ymin = min(p[1] for p in pts); ymax = max(p[1] for p in pts)
tmin = min(p[3] for p in pts); tmax = max(p[3] for p in pts)
print("范围 X %.1f..%.1f  Y %.1f..%.1f  T %.1f..%.1f K" % (xmin, xmax, ymin, ymax, tmin, tmax))

CELL = 1.5
nx = int(math.ceil((xmax - xmin) / CELL))
ny = int(math.ceil((ymax - ymin) / CELL))
grid = [[None] * nx for _ in range(ny)]
for x, y, z, t in pts:
    i = min(nx - 1, int((x - xmin) / CELL))
    j = min(ny - 1, int((y - ymin) / CELL))
    cur = grid[j][i]
    if cur is None or t > cur:
        grid[j][i] = t

def col(t):
    """简单 jet 色标，输入归一化 0..1"""
    t = max(0.0, min(1.0, t))
    r = min(1.0, max(0.0, 1.5 - abs(4 * t - 3)))
    g = min(1.0, max(0.0, 1.5 - abs(4 * t - 2)))
    b = min(1.0, max(0.0, 1.5 - abs(4 * t - 1)))
    return (r, g, b)

# ---- 图1 俯视温度分布 ----
PW, PH = 780, 620
ML, MR, MT, MB = 70, 150, 50, 70
doc = fitz.open()
pg = doc.new_page(width=PW, height=PH)
sx = (PW - ML - MR) / (xmax - xmin)
sy = (PH - MT - MB) / (ymax - ymin)
sc = min(sx, sy)
ox = ML + ((PW - ML - MR) - (xmax - xmin) * sc) / 2
oy = MT + ((PH - MT - MB) - (ymax - ymin) * sc) / 2
span = 103.0 - 25.0  # 以 ℃ 计色标范围 25..103
for j in range(ny):
    for i in range(nx):
        v = grid[j][i]
        if v is None:
            continue
        yc = ymin + j * CELL
        x0 = ox + (xmin + i * CELL - xmin) * sc
        y0 = PH - (oy + (yc - ymin) * sc)
        pg.draw_rect(fitz.Rect(x0, y0 - CELL * sc * 1.02, x0 + CELL * sc * 1.02, y0),
                     color=None, fill=col((v - 273.15 - 25.0) / span))
# 色标
cbx = PW - MR + 40
cbt, cbb = MT, PH - MB
for k in range(100):
    t = 1 - k / 99
    pg.draw_rect(fitz.Rect(cbx, cbt + k * (cbb - cbt) / 100, cbx + 18, cbt + (k + 1) * (cbb - cbt) / 100),
                 color=None, fill=col(t))
for k in range(6):
    v = 25 + span * k / 5
    yy = cbb - (v - 25) * (cbb - cbt) / span
    pg.insert_text((cbx + 24, yy + 4), "%.0f" % v, fontsize=8)
pg.insert_text((cbx + 4, cbt - 8), "degC", fontsize=8)
pg.insert_text((ML, MT - 22), "QR-V23 module: max solid temperature per 1.5mm cell (top view, X-Y)", fontsize=10)
pg.insert_text((ML, PH - 40), "X: %.0f .. %.0f mm    Y: %.0f .. %.0f mm" % (xmin, xmax, ymin, ymax), fontsize=8)
doc.save(os.path.join(IMG, "map_top.pdf"))
doc[0].get_pixmap(matrix=fitz.Matrix(2, 2)).save(os.path.join(IMG, "map_top.png"))
doc.close()

# ---- 图2 LED 条带沿线温度（x 方向，y 在 ±2mm 内、FPC 附近）----
strip = [p for p in pts if abs(p[1] + 108.96) < 2.0]
strip.sort(key=lambda p: p[0])
# 按 2mm 分箱取最大
bins = {}
for x, y, z, t in strip:
    k = int(round(x / 2.0) * 2)
    bins[k] = max(bins.get(k, 0.0), t)
xs = sorted(bins.keys())
print("条带点数:", len(strip), "x 分箱:", len(xs))

W2, H2 = 780, 380
M2L, M2R, M2T, M2B = 70, 40, 44, 60
doc = fitz.open()
pg = doc.new_page(width=W2, height=H2)
x0, x1 = min(xs), max(xs)
t0, t1 = min(bins.values()) - 273.15, max(bins.values()) - 273.15
def X(v): return M2L + (v - x0) / (x1 - x0) * (W2 - M2L - M2R)
def Y(v): return H2 - M2B - (v - (t0 - 2)) / ((t1 + 4) - (t0 - 2)) * (H2 - M2T - M2B)
pg.draw_line((M2L, H2 - M2B), (W2 - M2R, H2 - M2B), color=(0, 0, 0), width=1)
pg.draw_line((M2L, M2T), (M2L, H2 - M2B), color=(0, 0, 0), width=1)
for k in range(5):
    v = (t0 - 2) + ((t1 + 4) - (t0 - 2)) * k / 4
    yy = Y(v)
    pg.draw_line((M2L, yy), (W2 - M2R, yy), color=(0.85, 0.85, 0.85), width=0.5)
    pg.insert_text((M2L - 44, yy + 4), "%.0f" % v, fontsize=8)
for k in range(6):
    v = x0 + (x1 - x0) * k / 5
    pg.insert_text((X(v) - 10, H2 - M2B + 16), "%.0f" % v, fontsize=8)
pg.insert_text((W2 / 2 - 60, H2 - 22), "X position along LED strip (mm)", fontsize=9)
pg.insert_text((10, M2T - 22), "Max temperature along LED strip (degC)", fontsize=9)
seq = [(X(x), Y(bins[x] - 273.15)) for x in xs]
for a, b in zip(seq[:-1], seq[1:]):
    pg.draw_line(a, b, color=(0.8, 0.15, 0.1), width=1.2)
doc.save(os.path.join(IMG, "chart_strip.pdf"))
doc[0].get_pixmap(matrix=fitz.Matrix(2, 2)).save(os.path.join(IMG, "chart_strip.png"))
doc.close()

# ---- 图3 导光板板面温度（4 mm 网格，取单元最大值）----
lgp_files = [fn for fn in os.listdir(ALL)
             if fn.lower().endswith(".csv") and "LGP" in fn.upper()]
lgp_pts = []
for fn in lgp_files:
    with open(os.path.join(ALL, fn), encoding="utf-8", errors="replace") as fp:
        rd = csv.reader(fp)
        started = False
        for r in rd:
            if not r:
                continue
            if r[0].strip().startswith("Point No."):
                started = True
                continue
            if not started or len(r) < 5:
                continue
            try:
                lgp_pts.append((float(r[1]), float(r[2]), float(r[3]), float(r[4])))
            except Exception:
                continue
print("LGP 点数:", len(lgp_pts), "来源:", lgp_files)

if not lgp_pts:
    print("WARN: 未找到 LGP 体数据，跳过 map_lgp.png")
else:
    LCELL = 4.0
    lx0, lx1 = min(p[0] for p in lgp_pts), max(p[0] for p in lgp_pts)
    ly0, ly1 = min(p[1] for p in lgp_pts), max(p[1] for p in lgp_pts)
    lt0, lt1 = min(p[3] for p in lgp_pts), max(p[3] for p in lgp_pts)
    lnx = max(1, int(math.ceil((lx1 - lx0) / LCELL)))
    lny = max(1, int(math.ceil((ly1 - ly0) / LCELL)))
    lgrid = [[None] * lnx for _ in range(lny)]
    for x, y, z, t in lgp_pts:
        i = min(lnx - 1, int((x - lx0) / LCELL))
        j = min(lny - 1, int((y - ly0) / LCELL))
        cur = lgrid[j][i]
        if cur is None or t > cur:
            lgrid[j][i] = t

    LPW, LPH = 780, 620
    LML, LMR, LMT, LMB = 70, 150, 50, 70
    ldoc = fitz.open()
    lpg = ldoc.new_page(width=LPW, height=LPH)
    lsx = (LPW - LML - LMR) / max(lx1 - lx0, 1e-9)
    lsy = (LPH - LMT - LMB) / max(ly1 - ly0, 1e-9)
    lsc = min(lsx, lsy)
    lox = LML + ((LPW - LML - LMR) - (lx1 - lx0) * lsc) / 2
    loy = LMT + ((LPH - LMT - LMB) - (ly1 - ly0) * lsc) / 2
    lspan = max(lt1 - lt0, 1e-9)
    for j in range(lny):
        for i in range(lnx):
            v = lgrid[j][i]
            if v is None:
                continue
            yc = ly0 + j * LCELL
            x0 = lox + (lx0 + i * LCELL - lx0) * lsc
            y0 = LPH - (loy + (yc - ly0) * lsc)
            lpg.draw_rect(fitz.Rect(x0, y0 - LCELL * lsc * 1.02, x0 + LCELL * lsc * 1.02, y0),
                          color=None, fill=col((v - lt0) / lspan))
    lcbx = LPW - LMR + 40
    lcbt, lcbb = LMT, LPH - LMB
    for k in range(100):
        t = 1 - k / 99
        lpg.draw_rect(fitz.Rect(lcbx, lcbt + k * (lcbb - lcbt) / 100,
                                lcbx + 18, lcbt + (k + 1) * (lcbb - lcbt) / 100),
                      color=None, fill=col(t))
    for k in range(6):
        v = lt0 + lspan * k / 5
        yy = lcbb - (v - lt0) * (lcbb - lcbt) / lspan
        lpg.insert_text((lcbx + 24, yy + 4), "%.0f" % (v - 273.15), fontsize=8)
    lpg.insert_text((lcbx + 4, lcbt - 8), "degC", fontsize=8)
    lpg.insert_text((LML, LMT - 22), "Light guide plate surface temperature (4mm cell, max in cell)", fontsize=10)
    lpg.insert_text((LML, LPH - 40),
                    "X: %.0f .. %.0f mm    Y: %.0f .. %.0f mm    max=%.1f C  min=%.1f C" %
                    (lx0, lx1, ly0, ly1, lt1 - 273.15, lt0 - 273.15), fontsize=8)
    ldoc.save(os.path.join(IMG, "map_lgp.pdf"))
    ldoc[0].get_pixmap(matrix=fitz.Matrix(2, 2)).save(os.path.join(IMG, "map_lgp.png"))
    ldoc.close()
    print("生成:", "map_lgp.png")

print("生成:", "map_top.png", "chart_strip.png", "map_lgp.png")
