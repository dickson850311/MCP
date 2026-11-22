import IBE
import shutil
import SimDocApi
import SimMeshApi
import SimPropApi
from ec_paths import P

BASE = P("files.v3", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v3.simec")
PROJ = P("files.v5", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v5.simec")

shutil.copyfile(BASE, PROJ)
SimDocApi.Open(PROJ)
SimDocApi.SetRunMode("Cmd")

SimPropApi.SolverControl.setValue(
    ["1", "300", "0.3", "0.5", "0.5"],
    ["FrozenFlowField", "MaxIteration", "T_Factor", "U_Factor", "P_Factor"])

SimPropApi.ModelSetup.setValue(
    ["1", "DO"],
    ["EnableRadiation", "RadiationModel"])

SimPropApi.GlobalMeshControl.setValue(
    ["0.1 mm", "6 mm", "100"],
    ["MinimumSize", "MaximumSize", "MaxAspectRatio"])

SimMeshApi.Mesh.Mesh()
print("网格:", SimMeshApi.Mesh.getMeshStats())
SimDocApi.Save()
print("DONE 05 ->", PROJ)
