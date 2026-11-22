# -*- coding: utf-8 -*-
"""Replace DOCX inline-shape images with native INTESIM Post PNGs.

Standalone script; requires python-docx:

    python replace_docx_figures.py --config report_replace_config.json

The config replaces the first N inline shapes in document order, then applies
paragraph and table-cell text rules. It never crops or distorts the image:
height is derived from the PNG pixel aspect ratio and the requested width.
"""
import argparse
import json
import os
import shutil
import sys

from docx import Document
from docx.shared import Cm


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file: %s" % path)
    width = int.from_bytes(head[16:20], "big")
    height = int.from_bytes(head[20:24], "big")
    return width, height


def set_para_text(paragraph, text):
    if not paragraph.runs:
        paragraph.add_run(text)
        return
    paragraph.runs[0].text = text
    for run in paragraph.runs[1:]:
        run.text = ""


def find_paragraph(doc, rule):
    index = rule.get("index")
    if index is not None:
        if 0 <= int(index) < len(doc.paragraphs):
            paragraph = doc.paragraphs[int(index)]
            expect = rule.get("expect_prefix")
            if not expect or paragraph.text.strip().startswith(expect):
                return paragraph
    prefix = rule.get("find") or rule.get("expect_prefix")
    if prefix:
        for paragraph in doc.paragraphs:
            if paragraph.text.strip().startswith(prefix):
                return paragraph
    return None


def replace_images(doc, rules):
    for index, rule in enumerate(rules):
        path = os.path.abspath(os.path.expanduser(rule["file"]))
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        if index >= len(doc.inline_shapes):
            raise IndexError(
                "DOCX has only %d inline shapes, requested index %d"
                % (len(doc.inline_shapes), index)
            )
        shape = doc.inline_shapes[index]
        rel_id = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
        part = doc.part.related_parts[rel_id]
        with open(path, "rb") as f:
            part._blob = f.read()

        png_width, png_height = png_size(path)
        width_cm = float(rule.get("width_cm", shape.width.cm))
        shape.width = Cm(width_cm)
        shape.height = Cm(width_cm * float(png_height) / float(png_width))
        print("image %d <- %s  (%dx%d, %.2f cm wide)" % (index, path, png_width, png_height, width_cm))


def replace_paragraphs(doc, rules):
    for rule in rules:
        paragraph = find_paragraph(doc, rule)
        if paragraph is None:
            print("WARN paragraph not found: %s" % (rule.get("find") or rule.get("index")))
            continue
        set_para_text(paragraph, rule["text"])
        print("paragraph <- %s" % (rule.get("find") or rule.get("index")))


def replace_table_cells(doc, rules):
    for rule in rules:
        old = rule["old"]
        new = rule["new"]
        count = 0
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip() == old:
                        set_para_text(cell.paragraphs[0], new)
                        count += 1
        print("table cell %r -> %r  x%d" % (old, new, count))


def save_doc(doc, output, fallback_suffix):
    output = os.path.abspath(output)
    parent = os.path.dirname(output)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    try:
        doc.save(output)
        print("SAVED %s bytes=%d" % (output, os.path.getsize(output)))
        return output
    except PermissionError:
        base, ext = os.path.splitext(output)
        fallback = base + fallback_suffix + ext
        doc.save(fallback)
        print("LOCKED: %s" % output)
        print("SAVED_FALLBACK %s bytes=%d" % (fallback, os.path.getsize(fallback)))
        return fallback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    source = os.path.abspath(os.path.expanduser(cfg["source_docx"]))
    output = os.path.abspath(os.path.expanduser(cfg.get("output_docx") or source))
    backup = cfg.get("backup_docx")
    if backup:
        backup = os.path.abspath(os.path.expanduser(backup))
        parent = os.path.dirname(backup)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        shutil.copy2(source, backup)
        print("BACKUP %s" % backup)

    doc = Document(source)
    replace_images(doc, cfg.get("images", []))
    replace_paragraphs(doc, cfg.get("paragraph_replacements", []))
    replace_table_cells(doc, cfg.get("table_cell_replacements", []))
    save_doc(doc, output, cfg.get("fallback_suffix", "_nativePost"))


if __name__ == "__main__":
    main()
