import IBE
import csv
import os
import SimDocApi
import SimResultApi
import SimPropApi
from ec_paths import P

PROJ = P("files.v5", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v5.simec")
DST = P("files.temp_all", r"D:\mcp-servers\ec-api\QR-V23_EC\temp_all")
SUM = P("files.summary_csv", r"D:\mcp-servers\ec-api\QR-V23_EC\温度结果汇总.csv")

os.makedirs(DST, exist_ok=True)
SimDocApi.Open(PROJ)
SimDocApi.SetRunMode("Cmd")

parts = SimDocApi.GetFlexPartsByType("ImportPart") + SimDocApi.GetFlexPartsByType("Cube")
print("零件数:", len(parts))

rows = []
for idx, p in enumerate(parts, 1):
    label = p.getPropertyValue(["Label"])[0]
    cls = "导入体" if "ImportPart" in str(p) else "方块"
    safe = "%02d_" % idx + "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)
    f = os.path.join(DST, safe + ".csv")
    try:
        SimResultApi.SimResult.ExportResult(f, p.Object, "Volume", "Scalar Solid T")
    except Exception as e:
        print("导出失败:", label, e)
        continue

    data = []
    with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts2 = line.split(',')
            if len(parts2) < 5:
                continue
            try:
                data.append(float(parts2[4]))
            except ValueError:
                continue
    if not data:
        print("无数据:", label)
        continue

    mn, mx = min(data), max(data)
    avg = sum(data) / len(data)
    rows.append({"零件标签": label, "类型": cls, "对象名": p.Object,
                 "单元数": len(data),
                 "最低温_K": "%.2f" % mn, "最高温_K": "%.2f" % mx, "平均温_K": "%.2f" % avg,
                 "最低温_C": "%.2f" % (mn - 273.15), "最高温_C": "%.2f" % (mx - 273.15),
                 "平均温_C": "%.2f" % (avg - 273.15)})
    print("统计:", label, mx - 273.15)

with open(SUM, 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=["零件标签", "类型", "对象名", "单元数",
                                       "最低温_K", "最高温_K", "平均温_K",
                                       "最低温_C", "最高温_C", "平均温_C"])
    w.writeheader()
    w.writerows(rows)
print("汇总:", len(rows), "->", SUM)
print("DONE 08")
