import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from ec_paths import load

CFG = load()
IMG = CFG.get("files.report_img", "")
DOC = CFG.get("files.report_docx", "")
SUM = CFG.get("files.summary_csv", "")
TXT = CFG.get("files.result_t", "")
ALL = CFG.get("files.temp_all", "")


def ok(p):
    return os.path.isfile(p) and os.path.getsize(p) > 0


def main():
    checks = []
    checks.append(("v2 工程", CFG.get("files.v2")))
    checks.append(("v3 工程", CFG.get("files.v3")))
    checks.append(("v5 工程", CFG.get("files.v5")))
    checks.append(("T.txt", TXT))
    checks.append(("温度汇总 CSV", SUM))
    checks.append(("temp_all 目录", ALL))
    for name in ("chart_monitor.png", "chart_parts.png", "chart_strip.png", "map_lgp.png"):
        checks.append((name, os.path.join(IMG, name)))
    checks.append(("Word 报告", DOC))

    missing = []
    print("配置:", CFG.get("project_root"))
    for name, p in checks:
        if p and os.path.exists(p):
            size = os.path.getsize(p) if os.path.isfile(p) else "dir"
            print("OK   %-18s %s (%s B)" % (name, p, size))
        else:
            print("MISS %-18s %s" % (name, p))
            missing.append(name)

    if ok(DOC):
        try:
            from docx import Document
            d = Document(DOC)
            n = len(d.inline_shapes)
            print("DOCX 嵌入图:", n)
            if n < 4:
                missing.append("DOCX 图片少于 4 张")
        except Exception as e:
            print("DOCX 读取失败:", e)
            missing.append("DOCX 无法读取")

    if missing:
        print("\n缺项:", ", ".join(missing))
        return 1
    print("\n全部检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
