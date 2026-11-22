import json
import os

DEFAULTS = {
    "install_root": r"D:\Simdroid Electronic Cooling V2026.7.3",
    "project_root": r"D:\mcp-servers\ec-api\QR-V23_EC",
    "files.ec": r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_EC.simec",
    "files.tree": r"D:\mcp-servers\ec-api\QR-V23_EC\tree_after_import.json",
    "files.bbox": r"D:\mcp-servers\ec-api\QR-V23_EC\bbox.csv",
    "files.v2": r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v2.simec",
    "files.v3": r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v3.simec",
    "files.v4": r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v4.simec",
    "files.v5": r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v5.simec",
    "files.temp_extract": r"D:\mcp-servers\ec-api\QR-V23_EC\temp_extract",
    "files.temp_all": r"D:\mcp-servers\ec-api\QR-V23_EC\temp_all",
    "files.summary_csv": r"D:\mcp-servers\ec-api\QR-V23_EC\温度结果汇总.csv",
    "files.report_img": r"D:\mcp-servers\ec-api\QR-V23_EC\report_img",
    "files.result_t": r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_v5\Solving\result\T.txt",
    "files.report_docx": r"D:\mcp-servers\ec-api\QR-V23_EC\QR-V23-15.4_稳态热仿真报告.docx",
}

DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "assets", "project_config.json")


def _expand(value, project_root):
    if not isinstance(value, str):
        return value
    value = value.replace("{project_root}", project_root)
    return os.path.expandvars(os.path.expanduser(value))


def load(path=None):
    path = path or os.environ.get("EC_CONFIG") or DEFAULT_CONFIG
    data = {}
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    else:
        print("ec_paths: 未找到配置文件，使用默认 QR-V23 路径:", path)

    root = data.get("project_root", DEFAULTS["project_root"])
    out = dict(DEFAULTS)
    out.update(data.get("files", {}) or {})
    if "install_root" in data:
        out["install_root"] = data["install_root"]
    if "project_root" in data:
        out["project_root"] = data["project_root"]
    if "step_file" in data:
        out["step_file"] = data["step_file"]
    for k in list(out.keys()):
        out[k] = _expand(out[k], root)
    return out


def P(key, default=None):
    cfg = load()
    return cfg.get(key, default)

if __name__ == "__main__":
    cfg = load()
    for k in sorted(cfg):
        print("%-22s %s" % (k, cfg[k]))
