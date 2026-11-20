"""SHAP explanations, decision curves, training-only augmentation and the v2 generator."""

import copy

import numpy as np
import pandas as pd
import pytest

from greyzone_rf import explain
from greyzone_rf.compare import dca_figure, decision_curves, net_benefit
from greyzone_rf.config import load_config
from greyzone_rf.data import prepare_table
from greyzone_rf.model import train_model
from greyzone_rf.synthetic import grey_zone_cohort


@pytest.fixture(scope="module")
def cfg():
    c = copy.deepcopy(load_config())
    c["random_forest"]["n_estimators"] = 60
    c["validation"].update(cv_repeats=2, inner_repeats=1, outer_folds=3, permutation_importance=False)
    return c


@pytest.fixture(scope="module")
def train(cfg):
    return prepare_table(grey_zone_cohort(240, seed=5, version=2), cfg, require_label=True)


@pytest.mark.parametrize("kind", ["random_forest", "logistic_regression", "xgboost"])
def test_shap_values_are_exact_and_additive(cfg, train, kind):
    b = train_model(train, cfg, nested=False, model_type_name=kind)
    assert explain.available(b)
    X = train.table.reindex(columns=b["features"]).iloc[:3]
    values, base = explain.shap_values(b, X)
    scores = b["model"].predict_proba(X)[:, 1]
    assert values.shape == (3, len(b["features"]))
    np.testing.assert_allclose(base + values.sum(axis=1), scores, atol=1e-6)   # Shapley efficiency
    table = explain.explanation_table(b, X.iloc[0], values[0])
    assert len(table) == len(b["features"])
    png = explain.waterfall_png(b, X.iloc[0], values[0], base, float(scores[0]), b["thresholds"])
    assert png[:4] == b"\x89PNG"
    assert explain.summary_png(b, values, X)[:4] == b"\x89PNG"
    allp = explain.all_patients_table(b, X, ["a", "b", "c"], scores)
    assert len(allp) == 3


def test_decision_curve(cfg, train):
    b = train_model(train, cfg, nested=False, model_type_name="logistic_regression")
    curves = decision_curves({"LR": b})
    y = np.asarray(b["oof_labels"])
    # treat-all net benefit at pt: prevalence - (1 - prevalence) * pt / (1 - pt)
    pt = curves["threshold"].iloc[5]
    assert curves["LP for everyone"].iloc[5] == pytest.approx(y.mean() - (1 - y.mean()) * pt / (1 - pt))
    assert np.allclose(net_benefit(y, np.zeros(len(y)) - 1), 0)               # act on no one -> 0
    assert dca_figure({"LR": b})[:4] == b"\x89PNG"


def test_augmentation_is_training_only(cfg, train):
    aug = prepare_table(grey_zone_cohort(300, seed=9, version=1), cfg, require_label=True)
    c = copy.deepcopy(cfg)
    c["augmentation"] = {"enabled": False, "ratio": 1.0}
    b = train_model(train, c, nested=True, model_type_name="logistic_regression", augmentation=aug)
    assert len(b["oof_scores"]) == 240                                          # scores only for real patients
    assert b["report"]["nested"]["metrics"]["n"] == 240
    assert any("augmented" in m for m in b["report"]["messages"])


def test_generator_v2_is_nonlinear_in_kidney_function():
    from greyzone_rf.synthetic_v2 import amyloid_probability, kidney_effect

    k = kidney_effect(np.array([100, 80, 70, 60, 45, 30]))
    assert k[0] == k[1] == k[2] == 0 and k[3] > 0 and (k[5] - k[4]) > (k[4] - k[3])
    p = amyloid_probability(np.array([70, 70, 70]), np.array([0, 1, 2]), np.array([1, 1, 1]))
    assert p[0] < p[1] < p[2]
    df = grey_zone_cohort(50, seed=1, version=2)
    assert df["ptau217"].between(0.14, 0.43).all() and set(df["lp_result"]) <= {"Positive", "Negative"}
    assert isinstance(df, pd.DataFrame)


@pytest.mark.parametrize("method", ["smote", "random_oversample", "noise"])
def test_resampling_is_training_only(cfg, train, method):
    c = copy.deepcopy(cfg)
    c["resampling"] = {"method": method, "ratio": 1.0, "k": 5}
    b = train_model(train, c, nested=True, model_type_name="logistic_regression")
    assert len(b["oof_scores"]) == 240 and b["report"]["nested"]["metrics"]["n"] == 240


def test_smote_keeps_categories_and_missing():
    from greyzone_rf.resampling import resample

    rng = np.random.default_rng(0)
    X = pd.DataFrame({"ptau217": rng.random(80), "apoe4": rng.integers(0, 3, 80).astype(float),
                      "egfr": rng.random(80) * 80})
    X.loc[::4, "egfr"] = np.nan
    y = (rng.random(80) > 0.75).astype(int)
    Xr, yr = resample(X, y, {"resampling": {"method": "smote"}}, seed=1)
    assert yr.mean() == pytest.approx(0.5, abs=0.02)
    assert set(Xr["apoe4"].dropna().unique()) <= {0.0, 1.0, 2.0}               # no impossible 1.37 alleles
    assert Xr["egfr"].isna().any()


def test_generator_v3_extra_factors():
    df = grey_zone_cohort(80, seed=3, version=3)
    for col in ("tsh", "thyroid_disease", "sleep_apnea", "mta_score", "fazekas", "mmse"):
        assert col in df.columns
    assert pd.to_numeric(df["mmse"], errors="coerce").dropna().between(0, 30).all()
    v2a, v2b = grey_zone_cohort(50, seed=4, version=2), grey_zone_cohort(50, seed=4, version=2)
    assert v2a.equals(v2b)


def test_xgboost_monotone_and_portable(cfg, train):
    import io

    import joblib

    c = copy.deepcopy(cfg)
    c["models"]["xgboost"]["monotone"] = {"ptau217": 1, "egfr": 1}
    b = train_model(train, c, nested=False, model_type_name="xgboost")
    X = train.table.reindex(columns=b["features"])
    buffer = io.BytesIO()
    joblib.dump(b["model"], buffer)
    buffer.seek(0)
    np.testing.assert_allclose(joblib.load(buffer).predict_proba(X), b["model"].predict_proba(X))
    grid = X.iloc[[0] * 20].copy()
    grid["ptau217"] = np.linspace(0.14, 0.43, 20)
    p = b["model"].predict_proba(grid)[:, 1]
    assert np.all(np.diff(p) >= -1e-9)                                        # never decreases with p-tau217
