from __future__ import annotations

import re
import sys
import time
import traceback
from pathlib import Path

import win32com.client


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper" / "kcgsa_2026_template_compliant_draft.md"
OUT_DIR = ROOT / "output" / "doc"
LOG = OUT_DIR / "kcgsa_hwp_background.log"
TEXT_OUT = OUT_DIR / "kcgsa_2026_template_compliant_text_only.hwp"
TABLE_OUT = OUT_DIR / "kcgsa_2026_template_compliant_table.hwp"


def log(msg: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {msg}\n")
        f.flush()


def clean(line: str) -> str:
    s = line.strip()
    if s.startswith("# "):
        s = s[2:].strip()
    elif s.startswith("## "):
        s = s[3:].strip()
    elif s.startswith("### "):
        s = s[4:].strip()
    return s.replace("  ", " ")


def parse_blocks(text: str):
    lines = text.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            table = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[:\-\s]+", c or "") for c in row):
                    table.append(row)
                i += 1
            blocks.append(("table", table))
            continue
        blocks.append(("text", clean(line)))
        i += 1
    return blocks


def template_path() -> Path:
    matches = list((Path.home() / "Downloads").glob("*Template(2026).hwp"))
    if not matches:
        raise FileNotFoundError("Could not find KCGSA HWP template in Downloads")
    return matches[0]


def hwp_instance():
    hwp = win32com.client.DispatchEx("HWPFrame.HwpObject")
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    except Exception as exc:
        log(f"RegisterModule failed or unavailable: {exc}")
    try:
        hwp.XHwpWindows.Item(0).Visible = False
    except Exception:
        pass
    return hwp


def insert_text(hwp, text: str) -> bool:
    hwp.HAction.GetDefault("InsertText", hwp.HParameterSet.HInsertText.HSet)
    hwp.HParameterSet.HInsertText.Text = text
    return bool(hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet))


def create_table(hwp, rows: list[list[str]]) -> None:
    nrows = len(rows)
    ncols = max(len(r) for r in rows)
    log(f"Creating HWP table rows={nrows} cols={ncols}")
    hwp.HAction.GetDefault("TableCreate", hwp.HParameterSet.HTableCreation.HSet)
    ps = hwp.HParameterSet.HTableCreation
    ps.Rows = nrows
    ps.Cols = ncols
    try:
        ps.WidthType = 2
    except Exception:
        pass
    try:
        ps.HeightType = 0
    except Exception:
        pass
    hwp.HAction.Execute("TableCreate", ps.HSet)
    for r, row in enumerate(rows):
        for c in range(ncols):
            insert_text(hwp, row[c] if c < len(row) else "")
            if not (r == nrows - 1 and c == ncols - 1):
                hwp.HAction.Run("TableRightCell")
    hwp.HAction.Run("MoveDocEnd")
    insert_text(hwp, "\r\n")


def open_template_and_clear(hwp) -> None:
    tmpl = template_path()
    log(f"Opening template: {tmpl}")
    ok = hwp.Open(str(tmpl), "HWP", "forceopen:true")
    log(f"Template opened: {ok}")
    hwp.HAction.Run("SelectAll")
    hwp.HAction.Run("Delete")


def make_text_only(blocks) -> None:
    log("Starting text-only HWP generation")
    hwp = None
    try:
        hwp = hwp_instance()
        open_template_and_clear(hwp)
        for i, (kind, payload) in enumerate(blocks, 1):
            if kind == "table":
                for row in payload:
                    insert_text(hwp, "\t".join(row) + "\r\n")
            else:
                insert_text(hwp, "\r\n" if payload == "" else payload + "\r\n")
            if i % 25 == 0:
                log(f"text-only inserted block {i}/{len(blocks)}")
        ok = hwp.SaveAs(str(TEXT_OUT), "HWP", "")
        log(f"text-only saved={ok}: {TEXT_OUT}")
    finally:
        if hwp is not None:
            try:
                hwp.Quit()
            except Exception:
                pass


def make_table_version(blocks) -> None:
    log("Starting table HWP generation")
    hwp = None
    try:
        hwp = hwp_instance()
        open_template_and_clear(hwp)
        for i, (kind, payload) in enumerate(blocks, 1):
            if kind == "table":
                create_table(hwp, payload)
            else:
                insert_text(hwp, "\r\n" if payload == "" else payload + "\r\n")
            if i % 25 == 0:
                log(f"table-version inserted block {i}/{len(blocks)}")
        ok = hwp.SaveAs(str(TABLE_OUT), "HWP", "")
        log(f"table-version saved={ok}: {TABLE_OUT}")
    finally:
        if hwp is not None:
            try:
                hwp.Quit()
            except Exception:
                pass


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    log("Background HWP generation started")
    text = SRC.read_text(encoding="utf-8")
    blocks = parse_blocks(text)
    log(f"Parsed blocks={len(blocks)}, tables={sum(1 for k, _ in blocks if k == 'table')}")
    try:
        make_text_only(blocks)
    except Exception:
        log("text-only generation failed")
        log(traceback.format_exc())
    try:
        make_table_version(blocks)
    except Exception:
        log("table generation failed")
        log(traceback.format_exc())
    log("Background HWP generation finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
