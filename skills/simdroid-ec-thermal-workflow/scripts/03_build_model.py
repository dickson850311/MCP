# -*- coding: utf-8 -*-
r"""v2 构建：把 22 个"壳体类"薄膜零件替换为等效正交方块，其余 37 件保留原始 CAD
   输出 D:\mcp-servers\ec-api\QR-V23_EC\QR-V23_v2.simec
"""
import sys, io, os, csv, shutil, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ec_paths import P
import IBE
import SimDocApi, SimFPartApi, SimPropApi, SimMeshApi, SimAnalysisApi

BASE = P("files.ec", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23_EC.simec")
PROJ = P("files.v2", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23_v2.simec")
BBOX = P("files.bbox", r"D:\mcp-servers\ec-api\QR-V23_EC\bbox.csv")

# 换成方块的正交化对象（1-based 导入序号）
OFFEND = [3] + list(range(11, 24)) + list(range(37, 45))

MATS = {
    "PC":   ("0.3",  "0.8"),
    "PET":  ("0.3",  "0.8"),
    "TAPE": ("0.5",  "0.8"),
    "FOAM": ("0.15", "0.8"),
    "MG":   ("72",   "0.5"),
    "SUS":  ("16.3", "0.3"),
    "SIL":  ("0.3",  "0.9"),
    "FPC":  ("25",   "0.8"),
}

MAP = {}
MAP[1] = "PC"; MAP[2] = "FPC"; MAP[3] = "PC"; MAP[4] = "TAPE"
for i in (5, 6, 7, 8, 9): MAP[i] = "TAPE"
MAP[10] = "PC"
for i in (11, 12, 13, 14, 15, 16, 17): MAP[i] = "PET"
for i in (18, 19, 20, 21, 22, 23): MAP[i] = "TAPE"
for i in range(24, 37): MAP[i] = "PC"
for i in (37, 38, 39, 40, 41, 42, 43, 44): MAP[i] = "FOAM"
MAP[45] = "MG"; MAP[46] = "TAPE"; MAP[47] = "TAPE"
for i in (48, 49, 50, 51, 52): MAP[i] = "TAPE"
MAP[53] = "SUS"; MAP[54] = "TAPE"
for i in (55, 56, 57): MAP[i] = "TAPE"
for i in (58, 59): MAP[i] = "SIL"

P_HEAT = 9.096
errors = []
def log(*a): print(*a)

try:
    shutil.copyfile(BASE, PROJ)
    SimDocApi.Open(PROJ)
    SimDocApi.SetRunMode("Cmd")
    log("工程副本:", PROJ)

    matobj, surfobj = {}, {}
    for name, (k, eps) in MATS.items():
        m = SimPropApi.SolidMaterial.create("MAT_" + name)
        m.setValue(["Isotropic"], ["ThermalConductivityType"])
        m.setValue(["Constant"], ["ConductivityType"])
        m.setValue([k + " W/(m*K)"], ["ConstantConductivity"])
        matobj[name] = m
        s = SimPropApi.Surface.create("SUR_" + name)
        s.setValue([eps], ["Emissivity"])
        surfobj[name] = s
    rad = SimPropApi.Radiation.create("RAD_Agg")
    rad.setValue(["Agglomeration Radiating"], ["SurfaceType"])
    log("材料/表面/辐射 建立完成")

    rows = list(csv.DictReader(open(BBOX, encoding="utf-8-sig")))
    parts = SimDocApi.GetFlexPartsByType("ImportPart")
    log("CSV 行数:", len(rows), " 导入体:", len(parts))
    if len(rows) != len(parts):
        raise RuntimeError("行数与导入体数不一致，停止")

    # 1) 先记住每个零件的序号->对象 与 材料类
    idx_obj = {i + 1: parts[i] for i in range(len(parts))}

    # 2) 删除需要正交化的导入体，并记录其几何
    swapped = []
    for i in OFFEND:
        r = rows[i - 1]
        lab = r["Label"]
        box = (float(r["xmin"]), float(r["ymin"]), float(r["zmin"]),
               float(r["dx"]), float(r["dy"]), float(r["dz"]))
        try:
            SimDocApi.delete(idx_obj[i].Object)
        except Exception as e:
            errors.append("删除失败 %d %s: %s" % (i, lab, e))
        swapped.append((i, lab, box, MAP.get(i, "PC")))
    log("已删除待替换件:", len(swapped))

    # 3) 建等效方块
    for i, lab, box, cls in swapped:
        try:
            c = SimFPartApi.Cube.create("BOX_" + lab[:24])
            c.setPosition(["%g mm" % v for v in box[:3]], ["XLocation", "YLocation", "ZLocation"])
            c.setPropertyValue(["%g mm" % v for v in box[3:6]], ["XLocalSize", "YLocalSize", "ZLocalSize"])
            c.setSolidMaterial(matobj[cls])
            c.setSurface([surfobj[cls]])
            c.setRadiation([rad])
        except Exception as e:
            errors.append("建方块失败 %d %s: %s" % (i, lab, e))
    log("等效方块创建完成，失败:", len(errors))

    # 4) 剩余导入体赋材料
    left = SimDocApi.GetFlexPartsByType("ImportPart")
    log("剩余导入体:", len(left))
    for i in range(1, len(parts) + 1):
        if i in OFFEND:
            continue
        try:
            p = idx_obj[i]
            cls = MAP.get(i)
            p.setSolidMaterial(matobj[cls])
            p.setSurface([surfobj[cls]])
            p.setRadiation([rad])
        except Exception as e:
            errors.append("赋材料失败 %d: %s" % (i, e))

    # 5) 热源落在 FPC
    fpc = idx_obj[2]
    bt = SimPropApi.BodyThermal.create("BT_LED_total")
    bt.setValue(["Total Source"], ["Type"])
    bt.setValue(["%.3f W" % P_HEAT], ["OverallValue"])
    fpc.setBodyThermal(bt)
    log("热源 %.3f W -> %s" % (P_HEAT, fpc.getPropertyValue(["Label"])[0]))

    # 6) 监控点
    for nm, pos in [("MP_LED_C", ["0 mm", "-108.9 mm", "1.2 mm"]),
                    ("MP_LED_L", ["-150 mm", "-108.9 mm", "1.2 mm"]),
                    ("MP_LED_R", ["150 mm", "-108.9 mm", "1.2 mm"]),
                    ("MP_LGP",   ["0 mm", "0 mm", "1.8 mm"]),
                    ("MP_PANEL", ["0 mm", "0 mm", "3.3 mm"])]:
        mp = SimFPartApi.MonitorPoint.create(nm)
        mp.setPosition(pos)

    # 7) 求解域
    sd = SimPropApi.SolutionDomain.get()
    sd.setValue(["Input ratio"], ["ExpansionOfCalculationArea"])
    sd.setValue(["30 %"], ["ProportionXPos"]); sd.setValue(["30 %"], ["ProportionXNeg"])
    sd.setValue(["200 %"], ["ProportionYPos"]); sd.setValue(["50 %"], ["ProportionYNeg"])
    sd.setValue(["300 %"], ["ProportionZPos"]); sd.setValue(["300 %"], ["ProportionZNeg"])
    sd.setValue(["25 ℃"], ["AmbientTemperature"]); sd.setValue(["25 ℃"], ["RadiationTemperature"])
    SimPropApi.SolutionDomain.ResizeDomain()
    log("求解域:", SimPropApi.SolutionDomain.get().getValue(["SizeX", "SizeY", "SizeZ"]))

    # 8) 模型设置 + 求解器 + 网格
    ms = SimPropApi.ModelSetup.get()
    ms.setValue([1], ["EnableGravity"]); ms.setValue([1], ["EnableRadiation"])
    try:
        ms.setValue(["DO"], ["RadiationModel"])
    except Exception as e:
        log("DO 设置失败:", str(e)[:60])
    sc = SimPropApi.SolverControl.get()
    sc.setValue([1], ["EnableMonitorPointConvergence"])
    sc.setValue(["0.1 ℃"], ["RequiredAccuracy"])
    sc.setValue(["30"], ["ResidualThreshold"])
    sc.setValue(["500"], ["MaxIteration"])
    gm = SimPropApi.GlobalMeshControl.get()
    gm.setValue(["0.05 mm"], ["MinimumSize"])
    gm.setValue(["3 mm"], ["MaximumSize"])
    gm.setValue(["100"], ["MaxAspectRatio"])

    SimDocApi.Save()
    log("已保存:", PROJ)

except Exception:
    traceback.print_exc(); errors.append("BUILD_CRASH")

log("=== 错误 ===")
for e in errors[:20]: log(" ", e)
log("DONE")
