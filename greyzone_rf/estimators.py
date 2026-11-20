"""The machine-learning models that can produce the grey-zone score.

Every model goes through exactly the same procedure (``model.py``): repeated cross-validation,
the Clopper-Pearson PPV/NPV threshold rule, nested validation and all prediction safeguards
(CHECK DATA, NOT APPLICABLE, red flags, too much missing data). Only the algorithm that turns the
variables into a score between 0 and 1 changes.

The model type is read from ``cfg["model_type"]`` (default ``random_forest``, so models trained
before this option existed keep working). Settings live in ``config.yaml``: ``random_forest:`` for
the Random Forest and ``models: <type>:`` for the others; any setting left out uses the defaults
below.

Missing values
--------------
* Tree models (Random Forest, Extra Trees, Gradient Boosting) handle missing values natively.
* Logistic Regression and the SVM cannot: missing values are replaced by the training median **and**
  a 0/1 "was missing" indicator is added for each variable, so the model can still learn from the
  fact that a value is unknown. The patient-level safeguard (more than 50 % missing ->
  INCONCLUSIVE) applies to every model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import (ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier,
                              VotingClassifier)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

DEFAULT_TYPE = "random_forest"

# label = shown in the app; short = used in texts such as "RF score 0.82"
MODEL_TYPES: dict[str, dict] = {
    "random_forest": {"label": "Random Forest", "short": "RF"},
    "logistic_regression": {"label": "Logistic Regression", "short": "LR"},
    "gradient_boosting": {"label": "Gradient Boosting", "short": "GB"},
    "extra_trees": {"label": "Extra Trees", "short": "ET"},
    "svm": {"label": "Support Vector Machine", "short": "SVM"},
    "ensemble": {"label": "Ensemble (RF + LR + GB)", "short": "ENS"},
}

# Variables with a right-skewed distribution: log-transformed for the models that are not tree based
# (trees are unaffected by monotone transformations).
SKEWED = ("ptau217", "ptau217_ab42_ratio", "triglycerides", "ab42", "ab40", "creatinine")

DEFAULT_PARAMS: dict[str, dict] = {
    "logistic_regression": {"C": 0.5, "class_weight": None, "log_transform": True},
    "gradient_boosting": {"learning_rate": 0.03, "max_iter": 150, "max_leaf_nodes": 4, "min_samples_leaf": 20,
                          "l2_regularization": 1.0, "class_weight": None},
    "extra_trees": {"n_estimators": 500, "min_samples_leaf": 3, "max_features": "sqrt", "class_weight": None},
    "svm": {"C": 0.5, "gamma": "scale", "class_weight": None, "log_transform": True},
    "ensemble": {"members": ["random_forest", "logistic_regression", "gradient_boosting"]},
}


def model_type(cfg: dict) -> str:
    kind = cfg.get("model_type") or DEFAULT_TYPE
    if kind not in MODEL_TYPES:
        raise ValueError(f"Unknown model type '{kind}'. Choose one of: {', '.join(MODEL_TYPES)}")
    return kind


def model_label(kind: str | None) -> str:
    return MODEL_TYPES.get(kind or DEFAULT_TYPE, MODEL_TYPES[DEFAULT_TYPE])["label"]


def model_short(kind: str | None) -> str:
    return MODEL_TYPES.get(kind or DEFAULT_TYPE, MODEL_TYPES[DEFAULT_TYPE])["short"]


def model_params(cfg: dict, kind: str) -> dict:
    if kind == "random_forest":
        return dict(cfg.get("random_forest") or {})
    params = dict(DEFAULT_PARAMS.get(kind, {}))
    params.update((cfg.get("models") or {}).get(kind) or {})
    return params


class LogSkewed(BaseEstimator, TransformerMixin):
    """log(x) for the right-skewed laboratory variables (by column name); other columns unchanged."""

    def __init__(self, columns=SKEWED):
        self.columns = columns

    def fit(self, X, y=None):
        names = list(X.columns) if isinstance(X, pd.DataFrame) else []
        self.index_ = [i for i, name in enumerate(names) if name in self.columns]
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        values = np.array(X, dtype=float, copy=True)
        if self.index_:
            part = values[:, self.index_]
            values[:, self.index_] = np.log(np.clip(part, 1e-6, None))   # NaN stays NaN
        return values


def _imputed_pipeline(final, log_transform: bool):
    steps = [LogSkewed()] if log_transform else []
    steps += [SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), final]
    return make_pipeline(*steps)


def build_estimator(cfg: dict, seed: int, n_jobs: int | None = None, kind: str | None = None):
    """A fresh, unfitted model of the configured type (scikit-learn API: fit / predict_proba)."""
    kind = kind or model_type(cfg)
    p = model_params(cfg, kind)
    if kind == "random_forest":
        return RandomForestClassifier(
            n_estimators=int(p.get("n_estimators", 500)), min_samples_leaf=int(p.get("min_samples_leaf", 3)),
            max_features=p.get("max_features", "sqrt"), max_depth=p.get("max_depth"),
            class_weight=p.get("class_weight"), n_jobs=p.get("n_jobs", -1) if n_jobs is None else n_jobs,
            random_state=seed)
    if kind == "extra_trees":
        return ExtraTreesClassifier(
            n_estimators=int(p["n_estimators"]), min_samples_leaf=int(p["min_samples_leaf"]),
            max_features=p["max_features"], class_weight=p.get("class_weight"),
            n_jobs=-1 if n_jobs is None else n_jobs, random_state=seed)
    if kind == "gradient_boosting":
        return HistGradientBoostingClassifier(
            learning_rate=float(p["learning_rate"]), max_iter=int(p["max_iter"]),
            max_leaf_nodes=int(p["max_leaf_nodes"]), min_samples_leaf=int(p["min_samples_leaf"]),
            l2_regularization=float(p["l2_regularization"]), class_weight=p.get("class_weight"),
            early_stopping=False, random_state=seed)
    if kind == "logistic_regression":
        return _imputed_pipeline(LogisticRegression(C=float(p["C"]), class_weight=p.get("class_weight"),
                                                    max_iter=5000), bool(p.get("log_transform", True)))
    if kind == "svm":
        # Platt scaling on internal 5-fold CV turns the SVM margin into a probability-like score
        svm = SVC(C=float(p["C"]), gamma=p.get("gamma", "scale"), kernel="rbf", class_weight=p.get("class_weight"))
        calibrated = CalibratedClassifierCV(svm, method="sigmoid", ensemble=False,
                                            cv=StratifiedKFold(5, shuffle=True, random_state=seed))
        return _imputed_pipeline(calibrated, bool(p.get("log_transform", True)))
    if kind == "ensemble":
        members = [m for m in p["members"] if m in MODEL_TYPES and m != "ensemble"]
        return VotingClassifier([(m, build_estimator(cfg, seed, n_jobs=1, kind=m)) for m in members],
                                voting="soft")
    raise ValueError(f"Unknown model type '{kind}'")
