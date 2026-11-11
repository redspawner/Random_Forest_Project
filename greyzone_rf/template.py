"""Excel template with the expected file layout (one row per patient)."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .config import feature_specs

HEADER_FILL = PatternFill("solid", fgColor="DCE8F8")
REQUIRED_FILL = PatternFill("solid", fgColor="FBE1D6")


def template_columns(cfg: dict) -> list[dict]:
    cols = cfg["columns"]
    out = [{"column": cols["patient_id"], "description": "Unique patient identifier (pseudonymised!)",
            "unit": "text", "required": "yes", "example": "P-0001", "limits": ""}]
    for spec in feature_specs(cfg):
        if not spec.in_template:
            continue
        limits = ""
        if spec.min is not None or spec.max is not None:
            limits = f"{'' if spec.min is None else spec.min} - {'' if spec.max is None else spec.max}"
        out.append({
            "column": spec.name,
            "description": spec.description,
            "unit": spec.unit,
            "required": "yes" if spec.name == "ptau217" else "no (blank = missing)",
            "example": "" if spec.example is None else spec.example,
            "limits": limits,
        })
    out.append({"column": cols["label"],
                "description": "Lumbar-puncture (CSF) result. Fill for the TRAINING file; leave blank or delete "
                               "the column for new patients.",
                "unit": "Positive/Negative", "required": "training only", "example": "Positive", "limits": ""})
    return out


def dictionary_frame(cfg: dict) -> pd.DataFrame:
    return pd.DataFrame(template_columns(cfg)).astype(str)


def build_template(cfg: dict) -> bytes:
    cols = template_columns(cfg)
    wb = Workbook()
    ws = wb.active
    ws.title = "Patients"
    for j, col in enumerate(cols, start=1):
        header = f"{col['column']} ({col['unit']})" if col["unit"] and col["unit"] != "text" else col["column"]
        cell = ws.cell(row=1, column=j, value=header)
        cell.font = Font(bold=True)
        cell.fill = REQUIRED_FILL if col["required"] == "yes" else HEADER_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.cell(row=2, column=j, value=col["example"] if col["example"] != "" else None)
        ws.column_dimensions[get_column_letter(j)].width = max(12, min(24, len(header) + 2))
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "B2"

    names = [c["column"] for c in cols]
    validations = {
        "sex": ('"M,F"', "Use M (male) or F (female)"),
        cfg["columns"]["label"]: ('"Positive,Negative"', "Positive or Negative"),
    }
    for name, (formula, prompt) in validations.items():
        if name in names:
            letter = get_column_letter(names.index(name) + 1)
            dv = DataValidation(type="list", formula1=formula, allow_blank=True, showErrorMessage=True,
                                error=prompt, errorTitle="Invalid value")
            ws.add_data_validation(dv)
            dv.add(f"{letter}2:{letter}5000")

    info = wb.create_sheet("Dictionary")
    head = ["column", "description", "unit", "required", "limits", "example"]
    for j, h in enumerate(head, start=1):
        c = info.cell(row=1, column=j, value=h)
        c.font = Font(bold=True)
        c.fill = HEADER_FILL
    for i, col in enumerate(cols, start=2):
        for j, h in enumerate(head, start=1):
            info.cell(row=i, column=j, value=col[h] if col[h] != "" else None)
    for letter, width in zip("ABCDEF", (20, 80, 18, 20, 14, 12)):
        info.column_dimensions[letter].width = width

    gz = cfg["grey_zone"]
    notes = wb.create_sheet("Instructions")
    text = [
        "HOW TO FILL THIS FILE",
        "1. One row per patient in the sheet 'Patients'. Do not rename that sheet. Delete the example row.",
        "2. Keep the column names. Units in brackets are optional. Extra columns are ignored.",
        "3. Leave a cell blank when a value is not available (the model handles missing values).",
        "4. Use the units shown. Decimal comma (0,25) or point (0.25) are both accepted.",
        f"5. The model is only applied to patients with plasma p-tau217 between {gz['ptau217_lower']} and "
        f"{gz['ptau217_upper']} pg/mL (grey zone).",
        "6. Training file: fill 'lp_result' (Positive/Negative) for every patient.",
        "   New patients: leave 'lp_result' blank or delete the column.",
        "7. Use pseudonymised identifiers only - never names or hospital record numbers.",
        "8. eGFR may be left blank if serum creatinine is given (computed with CKD-EPI 2021).",
    ]
    for i, line in enumerate(text, start=1):
        cell = notes.cell(row=i, column=1, value=line)
        if i == 1:
            cell.font = Font(bold=True, size=13)
    notes.column_dimensions["A"].width = 110

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def write_template(cfg: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_template(cfg))
    return path
