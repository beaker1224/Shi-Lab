from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

_CELL_REF_PATTERN = re.compile(r"([A-Z]+)(\d+)")
_XLSX_NS = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
_PACKAGE_NS = {"p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def read_excel_numeric(path: Path | str, sheet: int = 0) -> np.ndarray:
    excel_path = Path(path)
    try:
        dataframe = pd.read_excel(excel_path, sheet_name=sheet, header=None)
        return dataframe.to_numpy(dtype=float)
    except Exception:
        return _read_excel_numeric_fallback(excel_path, sheet=sheet)


def _read_excel_numeric_fallback(path: Path, sheet: int = 0) -> np.ndarray:
    with ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relationship_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in relationships.findall("p:Relationship", _PACKAGE_NS)
        }
        sheets = workbook.find("x:sheets", _XLSX_NS)
        if sheets is None:
            raise ValueError(f"No sheets found in workbook: {path}")
        sheet_nodes = list(sheets)
        if sheet >= len(sheet_nodes):
            raise IndexError(f"Sheet index {sheet} out of range for {path}")
        relation_id = sheet_nodes[sheet].attrib[f"{{{_XLSX_NS['r']}}}id"]
        target = relationship_map[relation_id].lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"

        shared_strings = _read_shared_strings(archive)
        worksheet = ET.fromstring(archive.read(target))

    values: dict[tuple[int, int], float] = {}
    max_row = 0
    max_col = 0
    for cell in worksheet.findall(".//x:sheetData/x:row/x:c", _XLSX_NS):
        ref = cell.attrib.get("r")
        if not ref:
            continue
        col_idx, row_idx = _cell_reference_to_indices(ref)
        numeric_value = _cell_to_float(cell, shared_strings)
        values[(row_idx, col_idx)] = numeric_value
        max_row = max(max_row, row_idx + 1)
        max_col = max(max_col, col_idx + 1)

    if max_row == 0 or max_col == 0:
        return np.empty((0, 0), dtype=float)

    matrix = np.full((max_row, max_col), np.nan, dtype=float)
    for (row_idx, col_idx), numeric_value in values.items():
        matrix[row_idx, col_idx] = numeric_value
    return matrix


def _read_shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []

    tree = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in tree.findall("x:si", _XLSX_NS):
        text_parts = [node.text or "" for node in item.findall(".//x:t", _XLSX_NS)]
        values.append("".join(text_parts))
    return values


def _cell_to_float(cell: ET.Element, shared_strings: list[str]) -> float:
    cell_type = cell.attrib.get("t")
    value_node = cell.find("x:v", _XLSX_NS)
    if cell_type == "inlineStr":
        text = "".join(
            node.text or "" for node in cell.findall(".//x:is//x:t", _XLSX_NS)
        )
        return _safe_float(text)
    if value_node is None or value_node.text is None:
        return np.nan
    raw_value = value_node.text
    if cell_type == "s":
        index = int(raw_value)
        return _safe_float(shared_strings[index])
    return _safe_float(raw_value)


def _cell_reference_to_indices(cell_reference: str) -> tuple[int, int]:
    match = _CELL_REF_PATTERN.fullmatch(cell_reference)
    if match is None:
        raise ValueError(f"Unsupported cell reference: {cell_reference}")
    column_label, row_label = match.groups()
    col_idx = 0
    for char in column_label:
        col_idx = col_idx * 26 + (ord(char) - ord("A") + 1)
    return col_idx - 1, int(row_label) - 1


def _safe_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan
