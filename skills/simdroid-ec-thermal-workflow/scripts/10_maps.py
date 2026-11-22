import csv
import glob
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from ec_paths import P

ALL = P("files.temp_all", r"D:\mcp-servers\ec-api\QR-V23_EC\temp_all")
IMG = P("files.report_img", r"D:\mcp-servers\ec-api\QR-V23_EC\report_img")

os.makedirs(IMG, exist_ok=True)

# EC 常用彩虹色：蓝-青-绿-黄-红
cmap = LinearSegmentedColormap.from_list(
    "ec_rainbow", ["#0000ff", "#00ffff", "#00ff00", "#ffff00", "#ff0000"])

def load_all():
    pts = []
    files = sorted(glob.glob(os.path.join(ALL, "*.csv")))
    print("CSV 数:", len(files))
    for f in files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('"Point No.'):
                    continue
                cols = line.split(',')
                if len(cols) < 5:
                    continue
                try:
                    x, y, z, t = float(cols[1]), float(cols[2]), float(cols[3]), float(cols[4])
                except ValueError:
                    continue
                pts.append((x, y, z, t, os.path.basename(f)))
    return pts

pts = load_all()
print("点数:", len(pts))
if not pts:
    raise SystemExit("没有温度点")

xs = np.array([p[0] for p in pts])
ys = np.array([p[1] for p in pts])
zs = np.array([p[2] for p in pts])
ts = np.array([p[3] for p in pts])
print("范围 X %.1f..%.1f Y %.1f..%.1f T %.1f..%.1f K" %
      (xs.min(), xs.max(), ys.min(), ys.max(), ts.min(), ts.max()))

# ---------- 全局俯视 ----------
step = 1.5
nx = int((xs.max() - xs.min()) / step) + 1
ny = int((ys.max() - ys.min()) / step) + 1
grid = np.full((ny, nx), np.nan)
for x, y, _z, t, _f in pts:
    ix = int((x - xs.min()) / step)
    iy = int((y - ys.min()) / step)
    if 0 <= ix < nx and 0 <= iy < ny:
        if np.isnan(grid[iy, ix]) or t > grid[iy, ix]:
            grid[iy, ix] = t

fig, ax = plt.subplots(figsize=(12, 8))
im = ax.imshow(grid, origin='lower', cmap=cmap, vmin=298.15, vmax=376.15,
               extent=[xs.min(), xs.max(), ys.min(), ys.max()], aspect='equal')
ax.set_xlabel("X (mm)")
ax.set_ylabel("Y (mm)")
ax.set_title("QR-V23 背光模组温度分布（俯视，取体数据单元最大值）")
cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
cbar.set_label("温度 (℃)")
plt.tight_layout()
p_top = os.path.join(IMG, "map_top.png")
plt.savefig(p_top, dpi=200)
plt.close()
print("俯视图:", p_top)

# ---------- LED 条带 ----------
y0 = -108.96
band = [p for p in pts if abs(p[1] - y0) < 2.0]
print("条带点:", len(band))
if band:
    bx = np.array([p[0] for p in band])
    bt = np.array([p[3] for p in band])
    bins = np.arange(bx.min(), bx.max() + 2.0, 2.0)
    idx = np.digitize(bx, bins)
    cx, cmax = [], []
    for i in range(1, len(bins)):
        m = idx == i
        if m.any():
            cx.append((bins[i - 1] + bins[i]) / 2)
            cmax.append(bt[m].max() - 273.15)
    plt.figure(figsize=(12, 4))
    plt.plot(cx, cmax, 'r.-', ms=3)
    plt.xlabel("X (mm)")
    plt.ylabel("最高温度 (℃)")
    plt.title("LED 条带沿线最高温度（y≈%.1f mm）" % y0)
    plt.grid(True, ls=':', alpha=0.4)
    plt.tight_layout()
    p_strip = os.path.join(IMG, "chart_strip.png")
    plt.savefig(p_strip, dpi=200)
    plt.close()
    print("条带图:", p_strip, "max %.1f ℃" % max(cmax))

# ---------- LGP 板面 ----------
lgp = [p for p in pts if "LGP" in p[4].upper()]
print("LGP 点:", len(lgp))
if lgp:
    lx = np.array([p[0] for p in lgp])
    ly = np.array([p[1] for p in lgp])
    lt = np.array([p[3] for p in lgp])
    lstep = 4.0
    lnx = int((lx.max() - lx.min()) / lstep) + 1
    lny = int((ly.max() - ly.min()) / lstep) + 1
    lgrid = np.full((lny, lnx), np.nan)
    for x, y, _z, t, _f in lgp:
        ix = int((x - lx.min()) / lstep)
        iy = int((y - ly.min()) / lstep)
        if 0 <= ix < lnx and 0 <= iy < lny:
            if np.isnan(lgrid[iy, ix]) or t > lgrid[iy, ix]:
                lgrid[iy, ix] = t
    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(lgrid, origin='lower', cmap=cmap,
                   vmin=lt.min(), vmax=lt.max(),
                   extent=[lx.min(), lx.max(), ly.min(), ly.max()], aspect='equal')
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title("LGP 导光板温度分布（4 mm 网格，取单元最大值）")
    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("温度 (℃)")
    plt.tight_layout()
    p_lgp = os.path.join(IMG, "map_lgp.png")
    plt.savefig(p_lgp, dpi=200)
    plt.close()
    print("LGP 图:", p_lgp, "max %.1f ℃" % (lt.max() - 273.15), "min %.1f ℃" % (lt.min() - 273.15))
else:
    print("警告: temp_all 中没有匹配到 LGP 文件，map_lgp.png 不会生成；11_report.py 会报 add_picture 缺失")

print("DONE 10")
