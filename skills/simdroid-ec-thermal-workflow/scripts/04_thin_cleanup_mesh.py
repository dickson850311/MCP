# -*- coding: utf-8 -*-
"""v3：剔除最小尺寸 <0.1mm 的超薄辅料，最小网格尺寸 0.05mm，重划网格
输出 QR-V23_v3.simec
"""
import sys, io, os, shutil, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ec_paths import P
import IBE, SimDocApi, SimPropApi, SimMeshApi

SRC = P("files.v2", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23_v2.simec")
DST = P("files.v3", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23_v3.simec")
THIN = 0.1   # mm

try:
    shutil.copyfile(SRC, DST)
    SimDocApi.Open(DST)
    SimDocApi.SetRunMode("Cmd")

    removed, kept = [], 0
    for t in ("ImportPart", "Cube"):
        for p in list(SimDocApi.GetFlexPartsByType(t)):
            try:
                bb = p.getGlobalBoundingBox()
                dx, dy, dz = bb[3]-bb[0], bb[4]-bb[1], bb[5]-bb[2]
                thin = min(dx, dy, dz)
                lab = p.getPropertyValue(["Label"])[0]
            except Exception:
                continue
            if thin < THIN:
                try:
                    SimDocApi.delete(p.Object)
                    removed.append((t, lab[:34], round(thin, 3)))
                except Exception as e:
                    print("删除失败", lab, str(e)[:60])
            else:
                kept += 1
    print("剔除薄片:", len(removed), " 保留:", kept)
    for r in removed:
        print("   -", r[1], r[2], "mm")

    gm = SimPropApi.GlobalMeshControl.get()
    gm.setValue(["0.05 mm"], ["MinimumSize"])
    gm.setValue(["6 mm"], ["MaximumSize"])
    gm.setValue(["100"], ["MaxAspectRatio"])
    print("网格参数:", gm.getValue(["MinimumSize", "MaximumSize"]), flush=True)
    print("开始剖分 ...", flush=True)
    SimMeshApi.Mesh.Mesh()
    print("MESH:", (SimMeshApi.Mesh.getMeshStats() or "无").replace("\n", " | "))
    SimDocApi.Save()
    print("已保存:", DST)
except Exception:
    traceback.print_exc()
print("DONE")
