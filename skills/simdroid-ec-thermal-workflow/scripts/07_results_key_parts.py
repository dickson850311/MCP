import IBE
import os
import SimDocApi
import SimResultApi
from ec_paths import P

PROJ = P("files.v5", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v5.simec")
DST = P("files.temp_extract", r"D:\mcp-servers\ec-api\QR-V23_EC\temp_extract")

os.makedirs(DST, exist_ok=True)
SimDocApi.Open(PROJ)
SimDocApi.SetRunMode("Cmd")

TARGETS = [
    "FPC tape_1",
    "LGP_1",
    "DBEF",
    "PRT0029_tiekuang",
    "Frame 01",
]
parts = SimDocApi.GetFlexPartsByType("ImportPart") + SimDocApi.GetFlexPartsByType("Cube")
matched = {}
for t in TARGETS:
    matched[t] = [p for p in parts if p.getPropertyValue(["Label"])[0].startswith(t)]
    print("匹配:", t, len(matched[t]))

for t in TARGETS:
    for p in matched[t]:
        label = p.getPropertyValue(["Label"])[0]
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)
        f = os.path.join(DST, safe + ".csv")
        try:
            SimResultApi.SimResult.ExportResult(f, p.Object, "Volume", "Scalar Solid T")
            print("导出:", label, "->", f)
        except Exception as e:
            print("导出失败:", label, e)

print("DONE 07")
