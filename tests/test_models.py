"""Every model type uses the same procedure and the same safeguards as the Random Forest."""

import copy

import numpy as np
import pandas as pd
import pytest

from greyzone_rf.compare import (calibration_figure, classify_with_all, comparison_table, paired_differences,
                                 roc_figure, same_patients, triage_figure)
from greyzone_rf.config import load_config
from greyzone_rf.data import prepare_table
from greyzone_rf.default_model import default_status, shipped_types
from greyzone_rf.estimators import MODEL_TYPES, build_estimator
from greyzone_rf.model import load_bundle, model_info, save_bundle, train_model
from greyzone_rf.predict import CHECK_DATA_TXT, INCONCLUSIVE_TXT, NOT_APPLICABLE_TXT, predict_prepared
from greyzone_rf.synthetic import demo_new_patients, grey_zone_cohort

KINDS = list(MODEL_TYPES)


@pytest.fixture(scope="module")
def fast_cfg():
    cfg = copy.deepcopy(load_config())
    cfg["random_forest"]["n_estimators"] = 60
    cfg["models"]["extra_trees"]["n_estimators"] = 60
    cfg["models"]["gradient_boosting"]["max_iter"] = 60
    cfg["validation"].update(cv_repeats=2, inner_repeats=1, outer_folds=3, permutation_importance=False)
    return cfg


@pytest.fixture(scope="module")
def bundles(fast_cfg):
    train = prepare_table(grey_zone_cohort(240, seed=5), fast_cfg, require_label=True)
    return {kind: train_model(train, fast_cfg, nested=True, model_type_name=kind) for kind in KINDS}


@pytest.mark.parametrize("kind", KINDS)
def test_same_procedure_and_safety_rule(bundles, kind):
    b = bundles[kind]
    assert b["model_type"] == kind and b["report"]["model_type"] == kind
    assert 0.5 < b["report"]["auc_model"]["value"] <= 1.0
    for side, target in (("positive", "target_ppv"), ("negative", "target_npv")):
        detail = b["report"]["threshold_details"][side]
        if detail is not None:                               # every call side must meet the proven target
            assert detail["lower_bound"] >= b["config"]["decision"][target]
    assert b["report"]["nested"]["metrics"]["n"] == 240
    assert len(b["nested_decisions"]) == 240


@pytest.mark.parametrize("kind", KINDS)
def test_same_safeguards(bundles, fast_cfg, kind):
    new, _ = demo_new_patients(20, seed=11)
    new.loc[0, "atypical_features"] = 1                       # red flag
    for col in ["triglycerides", "ab42", "ab40", "ab42_ab40_ratio", "apoe4", "hypertension", "stroke",
                "clinical_stage", "creatinine", "egfr"]:
        if col in new.columns:
            new.loc[1, col] = np.nan                          # most variables missing
    res = predict_prepared(bundles[kind], prepare_table(new, fast_cfg)).set_index("patient_id")["decision"]
    assert res["NEW-LOW"] == NOT_APPLICABLE_TXT and res["NEW-HIGH"] == NOT_APPLICABLE_TXT
    assert res["NEW-TYPO"] == CHECK_DATA_TXT
    assert res.iloc[0] == INCONCLUSIVE_TXT
    assert res.iloc[1] == INCONCLUSIVE_TXT


def test_model_info_and_old_bundles(bundles, tmp_path):
    save_bundle(bundles["logistic_regression"], tmp_path / "lr")
    assert model_info(tmp_path / "lr")["model_type"] == "logistic_regression"
    old = dict(bundles["random_forest"])
    old.pop("model_type")                                     # a model saved before this feature
    save_bundle(old, tmp_path / "old")
    (tmp_path / "old" / "model_info.json").unlink()
    assert model_info(tmp_path / "old")["model_type"] == "random_forest"
    assert load_bundle(tmp_path / "old")["model_type"] == "random_forest"


def test_comparison(bundles, fast_cfg):
    named = {MODEL_TYPES[k]["label"]: b for k, b in bundles.items()}
    assert same_patients(named)
    table = comparison_table(named)
    assert len(table) == len(KINDS)
    paired = paired_differences(named, "Random Forest", n_boot=100)
    assert len(paired) == len(KINDS) - 1
    for png in (roc_figure(named), triage_figure(named), calibration_figure(named)):
        assert png[:4] == b"\x89PNG"
    new, _ = demo_new_patients(10, seed=3)
    wide = classify_with_all(named, prepare_table(new, fast_cfg))
    assert len(wide) == len(new) and "All models agree" in wide.columns


def test_missing_values_accepted_by_every_estimator():
    X = pd.DataFrame({"ptau217": [0.2, 0.3, np.nan, 0.25] * 10, "egfr": [80, np.nan, 60, 70] * 10})
    y = np.array([0, 1, 1, 0] * 10)
    cfg = load_config()
    for kind in KINDS:
        model = build_estimator({**cfg, "model_type": kind}, seed=0, n_jobs=1).fit(X, y)
        p = model.predict_proba(X)[:, 1]
        assert np.all((p >= 0) & (p <= 1))


@pytest.mark.parametrize("kind", shipped_types(load_config()))
def test_shipped_models(kind):
    status = default_status(load_config(), kind)
    assert status["loadable"], status["error"]
    assert status["dataset_matches"]
    assert load_bundle(status["model_dir"])["model_type"] == kind
