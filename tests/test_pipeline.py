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
