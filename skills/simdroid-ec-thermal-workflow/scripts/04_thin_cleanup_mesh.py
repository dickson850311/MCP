import IBE
import shutil
import SimDocApi
import SimFPartApi
import SimMeshApi
import SimPropApi
from ec_paths import P

BASE = P("files.v2", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v2.simec")
PROJ = P("files.v3", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v3.simec")
THIN = 0.1

shutil.copyfile(BASE, PROJ)
SimDocApi.Open(PROJ)
SimDocApi.SetRunMode("Cmd")

parts = SimDocApi.GetFlexPartsByType("ImportPart")
subs = SimDocApi.GetFlexPartsByType("Cube")
print("导入体:", len(parts), "方块:", len(subs))

for p in parts + subs:
    label = p.getPropertyValue(["Label"])[0]
    gb = p.getGlobalBoundingBox()
    gb = [float(str(v).replace("mm", "").strip()) for v in gb]
    dx, dy, dz = gb[3] - gb[0], gb[4] - gb[1], gb[5] - gb[2]
    mn = min(dx, dy, dz)
    if mn < THIN:
        print("删薄件:", p.Object, label, round(mn, 3))
        SimDocApi.delete(p.Object)

left = SimDocApi.GetFlexPartsByType("ImportPart") + SimDocApi.GetFlexPartsByType("Cube")
print("剩余:", len(left))

# 网格全局
SimPropApi.GlobalMeshControl.setValue(
    ["0.05 mm", "6 mm", "100"],
    ["MinimumSize", "MaximumSize", "MaxAspectRatio"])
SimMeshApi.Mesh.Mesh()
print("网格:", SimMeshApi.Mesh.getMeshStats())

SimDocApi.Save()
print("DONE 04 ->", PROJ)
