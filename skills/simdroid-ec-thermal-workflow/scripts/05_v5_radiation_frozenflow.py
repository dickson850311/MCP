# -*- coding: utf-8 -*-
"""v5：冻结流动 + 开 DO 辐射 + 最小网格 0.1mm，重划网格
输出 QR-V23_v5.simec
"""
import sys, io, os, shutil, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ec_paths import P
import IBE, SimDocApi, SimPropApi, SimMeshApi

SRC = P("files.v3", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23_v3.simec")
DST = P("files.v5", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23_v5.simec")
V4  = P("files.v4", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23_v4.simec")

try:
    print("v4 状态检查:", os.path.exists(V4),
          os.path.getsize(V4) if os.path.exists(V4) else "-")
    shutil.copyfile(SRC, DST)
    SimDocApi.Open(DST)
    SimDocApi.SetRunMode("Cmd")

    sc = SimPropApi.SolverControl.get()
    for k, v in [(["1"], ["FrozenFlowField"]), (["300"], ["MaxIteration"]),
                 (["0.3"], ["T_Factor"]), (["0.5"], ["U_Factor"]),
                 (["0.5"], ["P_Factor"])]:
        try:
            sc.setValue(v, k)
        except Exception as e:
            print("设置", k, "失败:", str(e)[:60])
    print("FrozenFlowField =", sc.getValue(["FrozenFlowField"]),
          " MaxIteration =", sc.getValue(["MaxIteration"]),
          " T_Factor =", sc.getValue(["T_Factor"]))

    ms = SimPropApi.ModelSetup.get()
    ms.setValue([1], ["EnableRadiation"])
    ms.setValue(["DO"], ["RadiationModel"])
    print("EnableRadiation =", ms.getValue(["EnableRadiation"]),
          " RadiationModel =", ms.getValue(["RadiationModel"]),
          " SolutionType =", ms.getValue(["SolutionType"]))

    gm = SimPropApi.GlobalMeshControl.get()
    gm.setValue(["0.1 mm"], ["MinimumSize"])
    gm.setValue(["6 mm"], ["MaximumSize"])
    gm.setValue(["100"], ["MaxAspectRatio"])
    print("网格:", gm.getValue(["MinimumSize", "MaximumSize"]), flush=True)

    print("开始剖分 ...", flush=True)
    SimMeshApi.Mesh.Mesh()
    print("MESH:", (SimMeshApi.Mesh.getMeshStats() or "无").replace("\n", " | "))
    SimDocApi.Save()
    print("已保存:", DST)
except Exception:
    traceback.print_exc()
print("DONE")
