"""Apply a trained model to new patients and build the results table."""

from __future__ import annotations

import io

import numpy as np
import pandas as pd

from .data import PreparedData, in_grey_zone
from .model import missing_fraction
from .stats import INCONCLUSIVE, NEGATIVE, POSITIVE, apply_thresholds

POSITIVE_TXT = "POSITIVE"
NEGATIVE_TXT = "NEGATIVE"
INCONCLUSIVE_TXT = "INCONCLUSIVE - refer to LP"
NOT_APPLICABLE_TXT = "NOT APPLICABLE - outside grey zone"
CHECK_DATA_TXT = "CHECK DATA"
DECISION_ORDER = [POSITIVE_TXT, NEGATIVE_TXT, INCONCLUSIVE_TXT, NOT_APPLICABLE_TXT, CHECK_DATA_TXT]

DISCLAIMER = ("Research prototype for teaching purposes - not a medical device. Results must not be "
              "used for clinical decisions without validation in an independent cohort and "
              "regulatory/ethical approval.")


def _pv_text(detail: dict | None, kind: str, confidence: float) -> str:
    if not detail:
        return ""
    return (f"cross-validated {kind} {detail['predictive_value']:.1%} "
            f"(one-sided {confidence:.0%} lower bound {detail['lower_bound']:.1%}; "
            f"{detail['n_correct']}/{detail['n_called']} training calls correct)")


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
    rows = []
    for i in range(prepared.n):
        issues = prepared.row_issues[i]
        notes = list(prepared.row_notes[i])
        missing_vars = [f for f in features if np.isnan(X.iloc[i][f])]
        score = scores[i]
        if issues:
            decision = CHECK_DATA_TXT
            reason = "Data problem: " + "; ".join(issues) + ". Correct the value(s) and run again."
        elif not grey[i]:
            stage1 = "NEGATIVE" if ptau[i] < gz["ptau217_lower"] else "POSITIVE"
            decision = NOT_APPLICABLE_TXT
            reason = (f"p-tau217 = {ptau[i]:g} pg/mL is outside the grey zone "
                      f"[{gz['ptau217_lower']}-{gz['ptau217_upper']}]: Stage-1 result is {stage1}. "
                      "The model was trained only on grey-zone patients and was not applied.")
        elif miss[i] > max_missing:
            decision = INCONCLUSIVE_TXT
            reason = (f"Insufficient data: {miss[i]:.0%} of the model variables are missing "
                      f"(limit {max_missing:.0%}). Refer to lumbar puncture.")
        else:
            code = codes[i]
            if code == POSITIVE:
                decision = POSITIVE_TXT
                reason = (f"RF score {score:.3f} >= rule-in threshold {thresholds['positive']:.2f}; "
                          + _pv_text(details["positive"], "PPV", conf) + ".")
            elif code == NEGATIVE:
                decision = NEGATIVE_TXT
                reason = (f"RF score {score:.3f} <= rule-out threshold {thresholds['negative']:.2f}; "
                          + _pv_text(details["negative"], "NPV", conf) + ".")
            else:
                decision = INCONCLUSIVE_TXT
                parts = []
                parts.append(f"rule-out <= {thresholds['negative']:.2f}" if thresholds["negative"] is not None
                             else "no safe rule-out threshold")
                parts.append(f"rule-in >= {thresholds['positive']:.2f}" if thresholds["positive"] is not None
                             else "no safe rule-in threshold")
                reason = (f"RF score {score:.3f} is not in a zone with demonstrated "
                          f"PPV/NPV >= {cfg['decision']['target_ppv']:.0%}/{cfg['decision']['target_npv']:.0%} "
                          f"({'; '.join(parts)}). Refer to lumbar puncture.")
            for f in features:
                v = X.iloc[i][f]
                if f in ranges and not np.isnan(v) and not ranges[f][0] <= v <= ranges[f][1]:
                    notes.append(f"{f} = {v:g} outside the range seen in training "
                                 f"[{ranges[f][0]:g}-{ranges[f][1]:g}]")
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
    info = [
        ("Generated", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")),
        ("Model trained", bundle["created"]),
        ("Training patients (grey zone)", report["cohort"]["n_train"]),
        ("Rule-in threshold (RF score >=)", thr["positive"] if thr["positive"] is not None else "none"),
        ("Rule-out threshold (RF score <=)", thr["negative"] if thr["negative"] is not None else "none"),
        ("Target PPV / NPV", f"{bundle['config']['decision']['target_ppv']:.0%} / "
                             f"{bundle['config']['decision']['target_npv']:.0%}"),
        ("Confidence bound required", bundle["config"]["decision"]["use_confidence_bound"]),
        ("", ""),
        *[(f"Patients: {k}", v) for k, v in summary.items()],
        ("", ""),
        ("DISCLAIMER", DISCLAIMER),
    ]
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        results.to_excel(writer, sheet_name="Results", index=False)
        info = [(item, "" if value is None else str(value)) for item, value in info]
        pd.DataFrame(info, columns=["Item", "Value"]).to_excel(writer, sheet_name="Summary", index=False)
        prepared.raw.to_excel(writer, sheet_name="Input", index=False)
        _style_results(writer.book["Results"], results)
        sheet = writer.book["Summary"]
        sheet.column_dimensions["A"].width = 38
        sheet.column_dimensions["B"].width = 60
    return buffer.getvalue()


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
