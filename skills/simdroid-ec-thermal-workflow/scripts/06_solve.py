import IBE
import SimDocApi
import SimAnalysisApi
import SimPropApi
from ec_paths import P

PROJ = P("files.v5", r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v5.simec")

SimDocApi.Open(PROJ)
SimDocApi.SetRunMode("Cmd")

sc = SimPropApi.SolverControl.get()
print("冻结流动:", sc.getValue(["FrozenFlowField"]))
print("最大迭代:", sc.getValue(["MaxIteration"]))
print("收敛精度:", sc.getValue(["EnableMonitorPointConvergence", "RequiredAccuracy", "ResidualThreshold"]))

SimAnalysisApi.Analysis.reinitializeAndCompute()
SimDocApi.Save()
print("DONE 06")
