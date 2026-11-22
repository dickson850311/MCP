import IBE
import SimDocApi
from ec_paths import P

STP = P("step_file", r"D:\二维码\QR-V23-15.4 2024-6-12.stp")
PROJ = P("files.ec", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_EC.simec")
TREE = P("files.tree", r"D:\mcp-servers\ec-api\QR-V23_EC\tree_after_import.json")

SimDocApi.NewDocument(PROJ)
SimDocApi.SetRunMode("Cmd")
SimDocApi.ImportProject(SimDocApi.ExportType.STEP_STP, STP)
SimDocApi.Save()

parts = SimDocApi.GetFlexPartsByType("ImportPart")
print("导入体数量:", len(parts))
for i, p in enumerate(parts, 1):
    label = p.getPropertyValue(["Label"])[0]
    print(i, p.Object, "|", label)

try:
    import FlexPartApi
    FlexPartApi.exportProjectTree(TREE, "0,1,2,3,4,5,6,7")
    print("项目树 ->", TREE)
except Exception as e:
    print("项目树导出失败:", e)

print("DONE 01")
