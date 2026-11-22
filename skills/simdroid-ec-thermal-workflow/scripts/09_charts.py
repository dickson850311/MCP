import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ec_paths import P

TXT = P("files.result_t", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v5\Solving\result\T.txt")
SUM = P("files.summary_csv", r"D:\mcp-servers\ec-api\QR-V23_EC\温度结果汇总.csv")
IMG = P("files.report_img", r"D:\mcp-servers\ec-api\QR-V23_EC\report_img")

os.makedirs(IMG, exist_ok=True)

it, series = [], {}
with open(TXT, 'r', encoding='utf-8', errors='ignore') as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        cols = [c.strip() for c in line.split(',')]
        if len(cols) < 7:
            continue
        try:
            i = int(float(cols[1]))
            vals = [float(c) for c in cols[2:7]]
        except ValueError:
            continue
        it.append(i)
        for k, v in enumerate(vals):
            series.setdefault(k, []).append(v)

names = ["MP_LED_C", "MP_LED_L", "MP_LED_R", "MP_LGP", "MP_PANEL"]
plt.figure(figsize=(10, 5))
for k in range(len(names)):
    if k in series and len(series[k]) == len(it):
        plt.plot(it, [x - 273.15 for x in series[k]], lw=1.0, label=names[k])
plt.xlabel("迭代步")
plt.ylabel("温度 (℃)")
plt.title("监控点温度随迭代变化")
plt.grid(True, ls=':', alpha=0.5)
plt.legend(fontsize=8)
plt.tight_layout()
p_mon = os.path.join(IMG, "chart_monitor.png")
plt.savefig(p_mon, dpi=200)
plt.close()
print("图1:", p_mon)

if it:
    tail = it[-10:]
    print("末10步:", tail[0], "->", tail[-1])
    for k in series:
        if k < len(names):
            print(names[k], "末10步变化 %.3f K" % (max(series[k][-10:]) - min(series[k][-10:])))

rows = list(csv.DictReader(open(SUM, encoding='utf-8-sig')))
rows = [r for r in rows if r.get("最高温_C")]
rows.sort(key=lambda r: float(r["最高温_C"]), reverse=True)
rows = rows[:18]
labels = [r["零件标签"][:22] for r in rows]
hi = [float(r["最高温_C"]) for r in rows]
av = [float(r["平均温_C"] or 0) for r in rows]

plt.figure(figsize=(9, 7))
y = range(len(rows))
plt.barh(y, hi, color='#c0504d', label='最高温')
plt.barh(y, av, color='#4f81bd', label='平均温')
plt.yticks(y, labels, fontsize=8)
plt.gca().invert_yaxis()
plt.xlabel("温度 (℃)")
plt.title("关键零件最高温 / 平均温")
plt.legend()
plt.tight_layout()
p_parts = os.path.join(IMG, "chart_parts.png")
plt.savefig(p_parts, dpi=200)
plt.close()
print("图2:", p_parts)
print("DONE 09")
