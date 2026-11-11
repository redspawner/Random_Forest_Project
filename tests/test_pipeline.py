"""End-to-end test on a small synthetic cohort with a fast configuration."""

import copy
import io

import pandas as pd
import pytest

from greyzone_rf.config import load_config
from greyzone_rf.data import prepare_table
from greyzone_rf.model import load_bundle, save_bundle, train_model
from greyzone_rf.predict import (CHECK_DATA_TXT, DECISION_ORDER, NOT_APPLICABLE_TXT, predict_prepared,
                                 results_to_excel)
from greyzone_rf.report import markdown_report, write_report
from greyzone_rf.synthetic import demo_new_patients, grey_zone_cohort


@pytest.fixture(scope="module")
def fast_cfg():
    cfg = copy.deepcopy(load_config())
    cfg["random_forest"]["n_estimators"] = 60
    cfg["validation"].update(cv_repeats=2, inner_repeats=1, outer_folds=3, permutation_importance=True)
    return cfg


@pytest.fixture(scope="module")
def bundle(fast_cfg):
    train = prepare_table(grey_zone_cohort(240, seed=5), fast_cfg, require_label=True)
    return train_model(train, fast_cfg, nested=True, source_name="synthetic_test.xlsx")


def test_training_bundle(bundle):
    r = bundle["report"]
    assert r["cohort"]["n_train"] == 240
    assert 0.5 < r["auc_model"]["value"] <= 1.0
    assert "ptau217" in bundle["features"] and "creatinine" not in bundle["features"]
    assert r["nested"]["metrics"]["n"] == 240
    for side in ("positive", "negative"):
        detail = r["threshold_details"][side]
        if detail is not None:
            assert detail["lower_bound"] >= 0.95
    assert "Training report" in markdown_report(bundle)


def test_prediction_and_safety_flags(bundle):
    new, _ = demo_new_patients(20, seed=11)
    prepared = prepare_table(new, bundle["config"])
    results = predict_prepared(bundle, prepared)
    assert len(results) == len(new)
    assert set(results["decision"]) <= set(DECISION_ORDER)
    by_id = results.set_index("patient_id")["decision"]
    assert by_id["NEW-LOW"] == NOT_APPLICABLE_TXT
    assert by_id["NEW-HIGH"] == NOT_APPLICABLE_TXT
    assert by_id["NEW-TYPO"] == CHECK_DATA_TXT
    sheets = pd.read_excel(io.BytesIO(results_to_excel(results, prepared, bundle)), sheet_name=None)
    assert {"Results", "Summary", "Input"} <= set(sheets)


def test_save_load_and_report(bundle, tmp_path):
    save_bundle(bundle, tmp_path)
    loaded = load_bundle(tmp_path)
    assert loaded["thresholds"] == bundle["thresholds"]
    paths = write_report(loaded, tmp_path)
    for key in ("scores", "roc", "safety", "markdown", "json", "predictions"):
        assert paths[key].exists()


def test_rejects_tiny_cohort(fast_cfg):
    from greyzone_rf.model import TrainingError

    tiny = prepare_table(grey_zone_cohort(8, seed=2), fast_cfg, require_label=True)
    with pytest.raises(TrainingError):
        train_model(tiny, fast_cfg, nested=False)


def _excel_with_gap(df: pd.DataFrame) -> bytes:
    """Excel file with an empty row between patients and an extra sheet, like a hand-made file."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Patients"
    ws.append(list(df.columns))
    for i, record in enumerate(df.itertuples(index=False)):
        if i == 3:
            ws.append([None] * len(df.columns))           # blank row in the middle
        ws.append([None if pd.isna(v) else v for v in record])
    wb.create_sheet("My notes")["A1"] = "keep me"
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def test_annotated_original_excel(bundle):
    from openpyxl import load_workbook

    from greyzone_rf.data import load_patient_file
    from greyzone_rf.predict import INFO_SHEET, annotated_original

    new, _ = demo_new_patients(8, seed=3)
    content = _excel_with_gap(new)
    prepared = load_patient_file(content, bundle["config"], filename="new.xlsx")
    results = predict_prepared(bundle, prepared)
    out = annotated_original(results, prepared, bundle)
    wb = load_workbook(io.BytesIO(out))
    assert {"Patients", "My notes", INFO_SHEET} <= set(wb.sheetnames)
    ws = wb["Patients"]
    header = [c.value for c in ws[1]]
    assert header[:len(new.columns)] == list(new.columns)             # original columns untouched
    col = header.index("AI decision") + 1
    assert ws.cell(row=5, column=1).value is None                     # the blank row stays blank
    for i, pid in enumerate(results["patient_id"]):
        excel_row = i + 2 if i < 3 else i + 3
        assert ws.cell(row=excel_row, column=1).value == pid
        assert ws.cell(row=excel_row, column=col).value == results["decision"][i]

    # annotating an already annotated file overwrites the columns instead of duplicating them
    again = load_patient_file(out, bundle["config"], filename="again.xlsx")
    twice = load_workbook(io.BytesIO(annotated_original(predict_prepared(bundle, again), again, bundle)))
    assert [c.value for c in twice["Patients"][1]].count("AI decision") == 1


def test_annotated_original_csv(bundle):
    from openpyxl import load_workbook

    from greyzone_rf.data import load_patient_file
    from greyzone_rf.predict import annotated_original

    new, _ = demo_new_patients(5, seed=4)
    prepared = load_patient_file(new.to_csv(index=False).encode(), bundle["config"], filename="new.csv")
    results = predict_prepared(bundle, prepared)
    ws = load_workbook(io.BytesIO(annotated_original(results, prepared, bundle)))["Patients"]
    header = [c.value for c in ws[1]]
    assert header[0] == "patient_id" and "AI decision" in header and ws.max_row == len(new) + 1


def test_annotation_never_overwrites_unnamed_columns(bundle):
    from openpyxl import Workbook, load_workbook

    from greyzone_rf.data import load_patient_file
    from greyzone_rf.predict import annotated_original

    new, _ = demo_new_patients(4, seed=6)
    wb = Workbook()
    ws = wb.active
    ws.title = "Patients"
    ws.append(list(new.columns))
    for record in new.itertuples(index=False):
        ws.append([None if pd.isna(v) else v for v in record] + [None, "my comment"])  # unnamed column
    buffer = io.BytesIO()
    wb.save(buffer)
    prepared = load_patient_file(buffer.getvalue(), bundle["config"], filename="x.xlsx")
    out = load_workbook(io.BytesIO(annotated_original(predict_prepared(bundle, prepared), prepared, bundle)))
    sheet = out["Patients"]
    comment_col = len(new.columns) + 2
    assert sheet.cell(row=2, column=comment_col).value == "my comment"
    header = [c.value for c in sheet[1]]
    assert header.index("AI decision") + 1 == comment_col + 1


def test_red_flag_blocks_classification(bundle):
    new, _ = demo_new_patients(6, seed=8)
    new = new[new["patient_id"].str.match(r"NEW-\d")].copy()
    new["atypical_features"] = 0
    new.loc[new.index[0], "atypical_features"] = 1
    results = predict_prepared(bundle, prepare_table(new, bundle["config"]))
    first = results.iloc[0]
    assert first["decision"].startswith("INCONCLUSIVE") and "Red flag" in first["explanation"]
    assert not results.iloc[1:]["explanation"].str.contains("Red flag").any()
