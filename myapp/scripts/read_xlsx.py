"""Minimal stdlib-only .xlsx reader (no openpyxl/pandas installed in this
environment, and not worth adding a dependency for a one-off read) - xlsx
is just a zip of XML, fully readable with zipfile + xml.etree. Handles the
flat single-sheet, no-merged-cells case, which is all for_review.xlsx is."""
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def col_letters_to_index(ref):
    letters = re.match(r"[A-Z]+", ref).group()
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def read_xlsx(path, sheet_index=1):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                texts = si.findall(".//m:t", NS)
                shared.append("".join(t.text or "" for t in texts))

        sheet_path = f"xl/worksheets/sheet{sheet_index}.xml"
        root = ET.fromstring(z.read(sheet_path))
        sheet_data = root.find("m:sheetData", NS)

        rows = []
        for row_el in sheet_data.findall("m:row", NS):
            cells = {}
            max_col = -1
            for c in row_el.findall("m:c", NS):
                ref = c.get("r")
                col_idx = col_letters_to_index(ref)
                max_col = max(max_col, col_idx)
                cell_type = c.get("t")
                v_el = c.find("m:v", NS)
                is_el = c.find("m:is", NS)
                if is_el is not None:
                    texts = is_el.findall(".//m:t", NS)
                    value = "".join(t.text or "" for t in texts)
                elif v_el is None:
                    value = ""
                elif cell_type == "s":
                    value = shared[int(v_el.text)]
                else:
                    value = v_el.text or ""
                cells[col_idx] = value
            row_list = [cells.get(i, "") for i in range(max_col + 1)]
            rows.append(row_list)
        return rows


if __name__ == "__main__":
    rows = read_xlsx(sys.argv[1])
    print(f"read {len(rows)} rows, {len(rows[0]) if rows else 0} columns")
    print("header:", rows[0])
