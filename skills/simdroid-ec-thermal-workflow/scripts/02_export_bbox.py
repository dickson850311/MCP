import IBE
import csv
import SimDocApi
import SimPropApi
from ec_paths import P

PROJ = P("files.ec", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_EC.simec")
BBOX = P("files.bbox", r"D:\mcp-servers\ec-api\QR-V23_EC\bbox.csv")

SimDocApi.Open(PROJ)
SimDocApi.SetRunMode("Cmd")
parts = SimDocApi.GetFlexPartsByType("ImportPart")

rows = []
for p in parts:
    label = p.getPropertyValue(["Label"])[0]
    gb = p.getGlobalBoundingBox()
    gb = [float(str(v).replace("mm", "").strip()) for v in gb]

    def f(v):
        return str(round(v, 4))

    xmin, ymin, zmin, xmax, ymax, zmax = gb
    rows.append({"Object": p.Object,
                 "Label": label,
                 "xmin": f(xmin), "ymin": f(ymin), "zmin": f(zmin),
                 "xmax": f(xmax), "ymax": f(ymax), "zmax": f(zmax),
                 "dx": f(xmax - xmin), "dy": f(ymax - ymin), "dz": f(zmax - zmin)})

with open(BBOX, 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=['Object', 'Label', 'xmin', 'ymin', 'zmin',
                                       'xmax', 'ymax', 'zmax', 'dx', 'dy', 'dz'])
    w.writeheader()
    w.writerows(rows)

sd = SimPropApi.SolutionDomain.get()
print("域:", sd.getValue(["X", "Y", "Z", "SizeX", "SizeY", "SizeZ", "AmbientTemperature"]))

print("整体 bbox:", min(float(r['xmin']) for r in rows), max(float(r['xmax']) for r in rows),
      min(float(r['ymin']) for r in rows), max(float(r['ymax']) for r in rows),
      min(float(r['zmin']) for r in rows), max(float(r['zmax']) for r in rows))
print("DONE 02 ->", BBOX)
