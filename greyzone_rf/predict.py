"""Apply a trained model to new patients and build the results table."""

from __future__ import annotations

import io

import numpy as np
import pandas as pd

from .data import PreparedData, in_grey_zone
from .i18n import column_name, tr
from .model import missing_fraction
from .stats import INCONCLUSIVE, NEGATIVE, POSITIVE, apply_thresholds

POSITIVE_TXT = tr("POSITIVE")
NEGATIVE_TXT = tr("NEGATIVE")
INCONCLUSIVE_TXT = tr("INCONCLUSIVE - refer to LP")
NOT_APPLICABLE_TXT = tr("NOT APPLICABLE - outside grey zone")
CHECK_DATA_TXT = tr("CHECK DATA")
DECISION_ORDER = [POSITIVE_TXT, NEGATIVE_TXT, INCONCLUSIVE_TXT, NOT_APPLICABLE_TXT, CHECK_DATA_TXT]

DISCLAIMER = tr("Research prototype for teaching purposes - not a medical device. Results must not be "
                "used for clinical decisions without validation in an independent cohort and "
                "regulatory/ethical approval.")


def _pv_text(detail: dict | None, kind: str, confidence: float) -> str:
    if not detail:
        return ""
    return tr("cross-validated {kind} {pv:.1%} (one-sided {conf:.0%} lower bound {lb:.1%}; "
              "{k}/{n} training calls correct)", kind=tr(kind), pv=detail["predictive_value"], conf=confidence,
              lb=detail["lower_bound"], k=detail["n_correct"], n=detail["n_called"])


def predict_prepared(bundle: dict, prepared: PreparedData) -> pd.DataFrame:
    """Return one row per patient with the decision and its justification."""
    cfg = bundle["config"]
    gz = cfg["grey_zone"]
    max_missing = float(cfg["decision"]["max_missing_fraction"])
    thresholds = bundle["thresholds"]
    details = bundle["report"]["threshold_details"]
    features = bundle["features"]
    conf = float(cfg["decision"]["confidence_level"])

    X = prepared.table.reindex(columns=features)
    ptau = prepared.table["ptau217"].to_numpy(float)
    grey = in_grey_zone(ptau, cfg)
    miss = missing_fraction(X)
    scores = np.full(prepared.n, np.nan)
    usable = grey & np.array([not issues for issues in prepared.row_issues])
    if usable.any():
        scores[usable] = bundle["model"].predict_proba(X[usable])[:, 1]
    codes = apply_thresholds(np.nan_to_num(scores, nan=0.5), thresholds["positive"], thresholds["negative"])

    ranges = bundle.get("training_ranges", {})
    red_flags = [c for c in cfg["decision"].get("red_flags", []) if c in prepared.table.columns]
    flagged = [[c for c in red_flags if prepared.table[c].iloc[i] == 1] for i in range(prepared.n)]
    rows = []
    for i in range(prepared.n):
        issues = prepared.row_issues[i]
        notes = list(prepared.row_notes[i])
        missing_vars = [column_name(f) for f in features if np.isnan(X.iloc[i][f])]
        score = scores[i]
        if issues:
            decision = CHECK_DATA_TXT
            reason = tr("Data problem: {issues}. Correct the value(s) and run again.", issues="; ".join(issues))
        elif not grey[i]:
            stage1 = NEGATIVE_TXT if ptau[i] < gz["ptau217_lower"] else POSITIVE_TXT
            decision = NOT_APPLICABLE_TXT
            reason = tr("p-tau217 = {v:g} pg/mL is outside the grey zone [{lo}-{hi}]: Stage-1 result is {stage1}. "
                        "The model was trained only on grey-zone patients and was not applied.",
                        v=ptau[i], lo=gz["ptau217_lower"], hi=gz["ptau217_upper"], stage1=stage1)
        elif flagged[i]:
            decision = INCONCLUSIVE_TXT
            reason = tr("Red flag present ({flags}): atypical presentation, plasma p-tau217 is not reliable here. "
                        "The model was not applied. Refer to lumbar puncture / PET.",
                        flags=", ".join(column_name(f) for f in flagged[i]))
        elif miss[i] > max_missing:
            decision = INCONCLUSIVE_TXT
            reason = tr("Insufficient data: {miss:.0%} of the model variables are missing (limit {limit:.0%}). "
                        "Refer to lumbar puncture.", miss=miss[i], limit=max_missing)
        else:
            code = codes[i]
            if code == POSITIVE:
                decision = POSITIVE_TXT
                reason = tr("RF score {s:.3f} >= rule-in threshold {t:.2f}; {pv}.", s=score,
                            t=thresholds["positive"], pv=_pv_text(details["positive"], "PPV", conf))
            elif code == NEGATIVE:
                decision = NEGATIVE_TXT
                reason = tr("RF score {s:.3f} <= rule-out threshold {t:.2f}; {pv}.", s=score,
                            t=thresholds["negative"], pv=_pv_text(details["negative"], "NPV", conf))
            else:
                decision = INCONCLUSIVE_TXT
                parts = []
                parts.append(tr("rule-out <= {t:.2f}", t=thresholds["negative"]) if thresholds["negative"] is not None
                             else tr("no safe rule-out threshold"))
                parts.append(tr("rule-in >= {t:.2f}", t=thresholds["positive"]) if thresholds["positive"] is not None
                             else tr("no safe rule-in threshold"))
                reason = tr("RF score {s:.3f} is not in a zone with demonstrated PPV/NPV >= {ppv:.0%}/{npv:.0%} "
                            "({parts}). Refer to lumbar puncture.", s=score, ppv=cfg["decision"]["target_ppv"],
                            npv=cfg["decision"]["target_npv"], parts="; ".join(parts))
            for f in features:
                v = X.iloc[i][f]
                if f in ranges and not np.isnan(v) and not ranges[f][0] <= v <= ranges[f][1]:
                    notes.append(tr("{f} = {v:g} outside the range seen in training [{lo:g}-{hi:g}]",
                                    f=column_name(f), v=v, lo=ranges[f][0], hi=ranges[f][1]))
        rows.append({
            "patient_id": prepared.ids[i],
            "decision": decision,
            "rf_score": round(float(score), 4) if not np.isnan(score) else None,
            "ptau217": ptau[i] if not np.isnan(ptau[i]) else None,
            "explanation": reason,
            "missing_variables": ", ".join(missing_vars),
            "notes": "; ".join(notes),
        })
    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame) -> dict[str, int]:
    counts = results["decision"].value_counts()
    return {d: int(counts.get(d, 0)) for d in DECISION_ORDER}


def results_to_excel(results: pd.DataFrame, prepared: PreparedData, bundle: dict) -> bytes:
    """Excel workbook with the results, a summary and the original input."""
    report = bundle["report"]
    thr = bundle["thresholds"]
    summary = summarize(results)
    none = tr("none")
    info = [
        (tr("Generated"), pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")),
        (tr("Model trained"), bundle["created"]),
        (tr("Training patients (grey zone)"), report["cohort"]["n_train"]),
        (tr("Rule-in threshold (RF score >=)"), thr["positive"] if thr["positive"] is not None else none),
        (tr("Rule-out threshold (RF score <=)"), thr["negative"] if thr["negative"] is not None else none),
        (tr("Target PPV / NPV"), f"{bundle['config']['decision']['target_ppv']:.0%} / "
                                 f"{bundle['config']['decision']['target_npv']:.0%}"),
        (tr("Confidence bound required"), tr("yes") if bundle["config"]["decision"]["use_confidence_bound"]
         else tr("no")),
        ("", ""),
        *[(tr("Patients: {decision}", decision=k), v) for k, v in summary.items()],
        ("", ""),
        (tr("DISCLAIMER"), DISCLAIMER),
    ]
    sheets = {"results": tr("Results"), "summary": tr("Summary"), "input": tr("Input")}
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        results.rename(columns=result_headers()).to_excel(writer, sheet_name=sheets["results"], index=False)
        info = [(item, "" if value is None else str(value)) for item, value in info]
        pd.DataFrame(info, columns=[tr("Item"), tr("Value")]).to_excel(writer, sheet_name=sheets["summary"],
                                                                       index=False)
        prepared.raw.to_excel(writer, sheet_name=sheets["input"], index=False)
        _style_results(writer.book[sheets["results"]], results)
        sheet = writer.book[sheets["summary"]]
        sheet.column_dimensions["A"].width = 38
        sheet.column_dimensions["B"].width = 60
    return buffer.getvalue()


def result_headers() -> dict[str, str]:
    """Column headers of the results table in the interface language."""
    return {"patient_id": tr("patient_id"), "decision": tr("decision"), "rf_score": tr("rf_score"),
            "ptau217": "ptau217", "explanation": tr("explanation"), "missing_variables": tr("missing_variables"),
            "notes": tr("notes")}


def _style_results(sheet, results: pd.DataFrame) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill

    fills = {
        POSITIVE_TXT: "F8D7D3", NEGATIVE_TXT: "D5ECDD", INCONCLUSIVE_TXT: "FCEBC5",
        NOT_APPLICABLE_TXT: "E7E6E2", CHECK_DATA_TXT: "E7E6E2",
    }
    widths = {"A": 16, "B": 34, "C": 10, "D": 10, "E": 90, "F": 40, "G": 60}
    for col, width in widths.items():
        sheet.column_dimensions[col].width = width
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for r, decision in enumerate(results["decision"], start=2):
        sheet.cell(row=r, column=2).fill = PatternFill("solid", fgColor=fills.get(decision, "FFFFFF"))
        sheet.cell(row=r, column=2).font = Font(bold=True)
        sheet.cell(row=r, column=5).alignment = Alignment(wrap_text=True, vertical="top")
    sheet.freeze_panes = "C2"


# ---------------------------------------------------------------------------
# The uploaded file itself, with the predictions added as extra columns
# ---------------------------------------------------------------------------
ANNOTATION_COLUMNS = {
    tr("AI decision"): "decision",
    tr("AI RF score"): "rf_score",
    tr("AI explanation"): "explanation",
    tr("AI missing variables"): "missing_variables",
    tr("AI notes"): "notes",
}
INFO_SHEET = tr("AI prediction info")
_WIDTHS = {"decision": 32, "rf_score": 12, "explanation": 80, "missing_variables": 30, "notes": 40}
_FILLS = {
    POSITIVE_TXT: "F8D7D3", NEGATIVE_TXT: "D5ECDD", INCONCLUSIVE_TXT: "FCEBC5",
    NOT_APPLICABLE_TXT: "E7E6E2", CHECK_DATA_TXT: "E7E6E2",
}


def _info_rows(results: pd.DataFrame, bundle: dict) -> list[tuple[str, str]]:
    thr = bundle["thresholds"]
    dec = bundle["config"]["decision"]
    gz = bundle["config"]["grey_zone"]
    uncertified = tr("none (not certified)")
    rows = [
        (tr("Generated"), pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")),
        (tr("Model trained"), str(bundle["created"])),
        (tr("Training data"), str(bundle["report"].get("source_file") or "")),
        (tr("Training patients (grey zone)"), str(bundle["report"]["cohort"]["n_train"])),
        (tr("Grey zone (p-tau217, pg/mL)"), f"{gz['ptau217_lower']} - {gz['ptau217_upper']}"),
        (tr("POSITIVE if RF score >="), uncertified if thr["positive"] is None else f"{thr['positive']:.2f}"),
        (tr("NEGATIVE if RF score <="), uncertified if thr["negative"] is None else f"{thr['negative']:.2f}"),
        (tr("Safety target"), tr("PPV >= {ppv:.0%}, NPV >= {npv:.0%}", ppv=dec["target_ppv"], npv=dec["target_npv"])
         + (tr(" (one-sided {conf:.0%} lower bound)", conf=dec["confidence_level"])
            if dec["use_confidence_bound"] else tr(" (point estimate)"))),
        ("", ""),
    ]
    rows += [(tr("Patients: {decision}", decision=k), str(v)) for k, v in summarize(results).items()]
    rows += [("", ""), (tr("DISCLAIMER"), DISCLAIMER)]
    return rows


def annotated_original(results: pd.DataFrame, prepared: PreparedData, bundle: dict) -> bytes:
    """Return the uploaded file with the prediction columns added to the right of each patient row.

    For an Excel upload the original workbook is kept (other sheets, formatting, column order);
    a CSV upload is converted to Excel. A sheet "AI prediction info" describes the model used.
    Column and sheet names follow the interface language.
    Columns added by a previous run are overwritten, not duplicated.
    """
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    source = prepared.source or {"kind": "csv"}
    if source["kind"] == "excel":
        wb = load_workbook(io.BytesIO(source["content"]))
        ws = wb[source["sheet"]]
        rows = source["rows"]
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = tr("Patients")
        ws.append([str(c) for c in prepared.raw.columns])
        for record in prepared.raw.itertuples(index=False):
            ws.append([None if pd.isna(v) else v for v in record])
        rows = list(range(2, prepared.n + 2))

    headers = {str(c.value).strip(): c.column for c in ws[1] if c.value is not None}
    # Start after the last column that holds ANY value (also unnamed columns), so nothing is overwritten.
    # AI columns that already exist (re-uploaded file) are reused in place.
    last = max((c.column for row in ws.iter_rows() for c in row if c.value is not None), default=0)
    columns = {}
    for name in ANNOTATION_COLUMNS:
        if name not in headers:
            last += 1
            headers[name] = last
        columns[name] = headers[name]
        cell = ws.cell(row=1, column=columns[name], value=name)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DCE8F8")

    for i, excel_row in enumerate(rows):
        result = results.iloc[i]
        for name, key in ANNOTATION_COLUMNS.items():
            value = result[key]
            value = None if value is None or (isinstance(value, float) and pd.isna(value)) or value == "" else value
            cell = ws.cell(row=excel_row, column=columns[name], value=value)
            if key == "decision":
                cell.font = Font(bold=True)
                cell.fill = PatternFill("solid", fgColor=_FILLS.get(result[key], "FFFFFF"))
            elif key == "explanation":
                cell.alignment = Alignment(wrap_text=False, vertical="top")

    from openpyxl.utils import get_column_letter
    for name, key in ANNOTATION_COLUMNS.items():
        ws.column_dimensions[get_column_letter(columns[name])].width = _WIDTHS[key]

    if INFO_SHEET in wb.sheetnames:
        del wb[INFO_SHEET]
    info = wb.create_sheet(INFO_SHEET)
    for item, value in _info_rows(results, bundle):
        info.append([item, value])
    info.column_dimensions["A"].width = 34
    info.column_dimensions["B"].width = 90
    for cell in info["A"]:
        cell.font = Font(bold=True)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
