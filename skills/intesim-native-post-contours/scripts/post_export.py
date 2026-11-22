# -*- coding: utf-8 -*-
"""Batch-export native INTESIM Post contour PNGs.

Run inside the INTESIM 8.0 main GUI script console, not as a standalone Python file:

    POST_EXPORT_CONFIG = r"D:\\path\\to\\post_export_config.json"
    exec(open(r"D:\\path\\to\\scripts\\post_export.py", encoding="utf-8").read())

The console injects Post, Window and Mesh as globals. The model XML must be loaded
before Post.openPostWindow; the script does that in the documented order.
"""
import json
import os
import time
import traceback

CONFIG_PATH = globals().get("POST_EXPORT_CONFIG")
if not CONFIG_PATH:
    raise RuntimeError(
        "Set POST_EXPORT_CONFIG = r'...post_export_config.json' in the INTESIM "
        "console before exec(open(...).read())."
    )

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

LOG_PATH = CFG.get("log") or os.path.join(os.path.dirname(os.path.abspath(CONFIG_PATH)), "post_export.log")


def log(msg):
    line = "%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def close_post():
    try:
        Window.closePostWindow()
        time.sleep(float(CFG.get("close_wait_sec", 2)))
    except Exception:
        log("CLOSE_POST_WARN " + traceback.format_exc().strip().splitlines()[-1])


def ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)


def figure_ids(fig):
    ids = fig.get("component_ids")
    if ids:
        return [int(v) for v in ids]
    n = int(fig.get("component_count", 0))
    if n <= 0:
        raise ValueError("figure needs component_ids or component_count: %s" % fig.get("out"))
    return list(range(1, n + 1))


def render_figure(model_name, fig):
    if "min" not in fig or "max" not in fig:
        raise ValueError("figure needs explicit min/max: %s" % fig.get("out"))

    sp = Post.newScalar(model_name)
    sp.name = str(fig["scalar"])
    sp.dataAdapterID = int(fig["adapter"])
    for cid in figure_ids(fig):
        sp.appendCompId(cid)

    sp.setDraw(True)
    sp.setDrawContour(True)
    sp.setShowIsoLine(False)
    sp.min = float(fig["min"])
    sp.max = float(fig["max"])
    sp.length = int(fig.get("length", 400))
    sp.dataCount = int(fig.get("data_count", 10))
    sp.location = int(fig.get("location", 0))
    sp.setAutoPosition(True)
    sp.hideoutrange = False
    sp.showmaxlabel = False
    sp.showminlabel = False
    sp.showminmaxid = False
    try:
        sp.setShowLabel(False)
        sp.setShowLabelByValue(False)
        sp.setShowLabelBack(False)
    except Exception:
        pass
    sp.drawMethod = "Default"
    sp.drawRangeSetting = False
    sp.show()
    log("SCALAR %s %s adapter=%s" % (model_name, sp.name, sp.dataAdapterID))

    Post.setView("SolidView")
    view = fig.get("view_direction", CFG.get("view_direction", [0, 0, 1, 0, 1, 0]))
    if len(view) != 6:
        raise ValueError("view_direction needs 6 numbers: %s" % view)
    factor = float(fig.get("fit_factor", CFG.get("fit_factor", 1.0)))
    Post.fitDirectionView(float(view[0]), float(view[1]), float(view[2]),
                          float(view[3]), float(view[4]), float(view[5]), factor)

    ps = Post.PlotSetting()
    ps.showLogo = False
    ps.showDescription = bool(CFG.get("show_description", True))
    ps.showDate = False
    ps.showLegendBar = True
    ps.legendFontSize = int(fig.get("legend_font_size", CFG.get("legend_font_size", 20)))
    ps.legendPrecision = int(fig.get("legend_precision", CFG.get("legend_precision", 1)))
    ps.legendSplitNumber = int(fig.get("legend_split_number", CFG.get("legend_split_number", 8)))
    ps.showCoordinateSystem = False
    ps.apply()

    out = os.path.abspath(os.path.expanduser(fig["out"]))
    ensure_parent(out)
    width = int(fig.get("width", CFG.get("width", 1600)))
    height = int(fig.get("height", CFG.get("height", 900)))
    quality = int(fig.get("quality", CFG.get("quality", 100)))
    Post.savePicture(width, height, quality, out)
    time.sleep(float(CFG.get("save_wait_sec", 2)))
    if os.path.exists(out):
        log("SAVED %s bytes=%d" % (out, os.path.getsize(out)))
    else:
        log("WARN output not found after savePicture: %s" % out)


def run_case(case):
    model_xml = os.path.abspath(os.path.expanduser(case["model_xml"]))
    result_inp = os.path.abspath(os.path.expanduser(case["result_inp"]))
    model_name = case["model_name"]
    if not os.path.exists(model_xml):
        raise FileNotFoundError(model_xml)
    if not os.path.exists(result_inp):
        raise FileNotFoundError(result_inp)

    close_post()
    log("OPEN_MODEL %s" % model_xml)
    Mesh.openFile(model_xml)
    time.sleep(float(case.get("load_wait_sec", CFG.get("load_wait_sec", 12))))
    log("OPEN_POST %s model=%s" % (result_inp, model_name))
    Post.openPostWindow(result_inp, model_name)
    time.sleep(float(case.get("open_wait_sec", CFG.get("open_wait_sec", 4))))

    Post.setBeamAndShell3DView(bool(case.get("beam_shell_3d", True)))
    for fig in case.get("figures", []):
        render_figure(model_name, fig)


def main():
    log("START %s" % os.path.abspath(CONFIG_PATH))
    for case in CFG.get("cases", []):
        try:
            run_case(case)
        except Exception:
            log("ERR_CASE %s\n%s" % (case.get("model_name", "?"), traceback.format_exc()))
    log("END")


main()
