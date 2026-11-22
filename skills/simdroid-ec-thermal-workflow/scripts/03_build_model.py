import IBE
import csv
import json
import shutil
import SimDocApi
import SimFPartApi
import SimPropApi
from ec_paths import P

BASE = P("files.ec", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_EC.simec")
BBOX = P("files.bbox", r"D:\mcp-servers\ec-api\QR-V23_EC\bbox.csv")
PROJ = P("files.v2", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v2.simec")

shutil.copyfile(BASE, PROJ)
SimDocApi.Open(PROJ)
SimDocApi.SetRunMode("Cmd")

def mm(v):
    return "%g mm" % v

def setv(obj, values, names):
    obj.setValue(list(values), list(names))

# ---------- 读 bbox ----------
with open(BBOX, newline='', encoding='utf-8-sig') as fh:
    bb = list(csv.DictReader(fh))
def B(i):
    r = bb[i]
    return [float(r[k]) for k in ('xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax', 'dx', 'dy', 'dz')]

# ---------- 材料 ----------
MATS = [
    ("PC", 0.3, 0.8),
    ("PET", 0.3, 0.8),
    ("TAPE", 0.5, 0.8),
    ("FOAM", 0.15, 0.8),
    ("MG", 72, 0.5),
    ("SUS", 16.3, 0.3),
    ("SIL", 0.3, 0.9),
    ("FPC", 25, 0.8),
]
matobj = {}
for name, k, _eps in MATS:
    m = SimPropApi.SolidMaterial.create("MAT_" + name)
    setv(m, ["Isotropic"], ["ThermalConductivityType"])
    setv(m, ["Constant"], ["ConductivityType"])
    setv(["%g W/(m*K)" % k], ["ConstantConductivity"])
    matobj[name] = m
    print("材料:", name, m.Object)

surfobj = {}
for name, _k, eps in MATS:
    s = SimPropApi.Surface.create("SUR_" + name)
    setv(s, [str(eps)], ["Emissivity"])
    surfobj[name] = s
    print("表面:", name, s.Object)

rad = SimPropApi.Radiation.create("RAD_Agg")
setv(rad, ["Agglomeration Radiating"], ["SurfaceType"])
print("辐射面类型:", rad.Object)

# ---------- 导入体 ----------
parts = SimDocApi.GetFlexPartsByType("ImportPart")
print("导入体:", len(parts))
for i, p in enumerate(parts, 1):
    print(i, p.Object, p.getPropertyValue(["Label"])[0])

# 要换成等效方块的导入序号 1-based（本案例 22 件）
OFFEND = [3] + list(range(11, 24)) + list(range(37, 45))

# 删除这些导入体
obox = {}
for i in OFFEND:
    b = B(i - 1)
    label = bb[i - 1]['Label']
    obox[i] = (label, b)
    print("删:", i, parts[i - 1].Object, label)
    SimDocApi.delete(parts[i - 1].Object)

# 剩余导入体：按序号赋类
MAP = {1: "SUS", 2: "FPC", 4: "SIL", 5: "PET", 6: "PET", 7: "PET", 8: "PC", 9: "PC",
       10: "FOAM", 24: "PC", 25: "PC", 26: "PC", 27: "PC", 28: "PC", 29: "PC", 30: "PC", 31: "PC",
       32: "MG", 33: "MG", 34: "SUS", 35: "TAPE", 36: "TAPE"}

left = SimDocApi.GetFlexPartsByType("ImportPart")
print("剩余导入体:", len(left))
for i, p in enumerate(left, 1):
    cls = MAP.get(i, "PC")
    p.setSolidMaterial(matobj[cls])
    p.setSurface([surfobj[cls]])
    p.setRadiation([rad])
    print("材料:", i, p.getPropertyValue(["Label"])[0], "->", cls)

# ---------- 等效方块 ----------
for i in OFFEND:
    label, b = obox[i]
    xmin, ymin, zmin, xmax, ymax, zmax, dx, dy, dz = b
    c = SimFPartApi.Cube.create("BOX_" + label[:24])
    setv(c, [mm(xmin), mm(ymin), mm(zmin)], ["XLocation", "YLocation", "ZLocation"])
    setv(c, [mm(dx), mm(dy), mm(dz)], ["XLocalSize", "YLocalSize", "ZLocalSize"])
    cls = MAP.get(i, "PC")
    c.setSolidMaterial(matobj[cls])
    c.setSurface([surfobj[cls]])
    c.setRadiation([rad])
    print("BOX:", i, label, "->", c.Object, cls, mm(dx), mm(dy), mm(dz))

# ---------- 热源 ----------
bt = SimPropApi.BodyThermal.create("BT_LED_total")
setv(bt, ["Total Source"], ["Type"])
setv(bt, ["9.096 W"], ["OverallValue"])

fpc = SimDocApi.GetFlexPartsByType("ImportPart")[1]
print("热源对象:", fpc.Object, fpc.getPropertyValue(["Label"])[0])
fpc.setBodyThermal(bt)

# ---------- 监控点 ----------
for name, (x, y, z) in [
        ("MP_LED_C", (0, -108.9, 1.2)),
        ("MP_LED_L", (-150, -108.9, 1.2)),
        ("MP_LED_R", (150, -108.9, 1.2)),
        ("MP_LGP", (0, 0, 1.8)),
        ("MP_PANEL", (0, 0, 3.3))]:
    mp = SimFPartApi.MonitorPoint.create(name)
    setv(mp, [mm(x), mm(y), mm(z)], ["XLocation", "YLocation", "ZLocation"])
    print("监控点:", name, mp.Object)

# ---------- 求解域 ----------
sd = SimPropApi.SolutionDomain.get()
setv(sd, ["Input ratio"], ["ExpansionOfCalculationArea"])
setv(sd, ["30 %"], ["ProportionXPos"])
setv(sd, ["30 %"], ["ProportionXNeg"])
setv(sd, ["200 %"], ["ProportionYPos"])
setv(sd, ["50 %"], ["ProportionYNeg"])
setv(sd, ["300 %"], ["ProportionZPos"])
setv(sd, ["300 %"], ["ProportionZNeg"])
setv(sd, ["25 ℃"], ["AmbientTemperature"])
setv(sd, ["25 ℃"], ["RadiationTemperature"])
SimPropApi.SolutionDomain.ResizeDomain()
print("域:", sd.getValue(["SizeX", "SizeY", "SizeZ"]))

# ---------- 模型 / 求解器 / 网格 ----------
ms = SimPropApi.ModelSetup.get()
setv(ms, [1], ["EnableGravity"])
setv(ms, [1], ["EnableRadiation"])
setv(ms, ["DO"], ["RadiationModel"])

sc = SimPropApi.SolverControl.get()
setv(sc, [1], ["EnableMonitorPointConvergence"])
setv(sc, ["0.1 ℃"], ["RequiredAccuracy"])
setv(sc, ["30"], ["ResidualThreshold"])
setv(sc, ["500"], ["MaxIteration"])

gm = SimPropApi.GlobalMeshControl.get()
setv(gm, ["0.05 mm"], ["MinimumSize"])
setv(gm, ["3 mm"], ["MaximumSize"])
setv(gm, ["100"], ["MaxAspectRatio"])

SimDocApi.Save()
print("DONE 03 ->", PROJ)
