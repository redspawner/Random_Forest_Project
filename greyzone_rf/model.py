"""Training of the grey-zone Random Forest and selection of the safe thresholds.

Procedure (what "training" means here)
--------------------------------------
1. Keep grey-zone patients with a lumbar-puncture (LP) result.
2. Repeated stratified K-fold cross-validation: every patient gets an
   out-of-fold (OOF) Random-Forest score from models that never saw them.
3. On those OOF scores choose two thresholds:
      score >= T_pos -> POSITIVE   (PPV >= 95%, by default proven with 95% confidence)
      score <= T_neg -> NEGATIVE   (NPV >= 95%, idem)
      otherwise      -> INCONCLUSIVE -> lumbar puncture
4. Fit the final Random Forest on all training patients (used for new patients).
5. (Optional, default on) Nested cross-validation: repeat steps 2-4 inside
   each outer fold and apply the result to the held-out outer fold. This is an
   honest estimate of how many LPs the procedure saves and how often it is wrong.
"""

from __future__ import annotations

import datetime as dt
import platform
from pathlib import Path
from typing import Callable

import joblib
from joblib import Parallel, delayed
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold

from .config import config_snapshot, model_feature_names
from .data import PreparedData, in_grey_zone
from .stats import (INCONCLUSIVE, apply_thresholds, bootstrap_auc_ci, minimum_calls_needed,
                    select_threshold, triage_metrics)

FORMAT_VERSION = 1
MIN_PER_CLASS = 5
Progress = Callable[[float, str], None] | None


class TrainingError(ValueError):
    pass


class _Counter:
    def __init__(self, total: int, callback: Progress):
        self.total, self.done, self.callback = max(total, 1), 0, callback

    def step(self, message: str) -> None:
        self.done += 1
        if self.callback:
            self.callback(min(self.done / self.total, 1.0), message)


def build_forest(cfg: dict, seed: int, n_jobs: int | None = None) -> RandomForestClassifier:
    params = dict(cfg["random_forest"])
    return RandomForestClassifier(
        n_estimators=int(params.get("n_estimators", 500)),
        min_samples_leaf=int(params.get("min_samples_leaf", 3)),
        max_features=params.get("max_features", "sqrt"),
        max_depth=params.get("max_depth"),
        class_weight=params.get("class_weight"),
        n_jobs=params.get("n_jobs", -1) if n_jobs is None else n_jobs,
        random_state=seed,
    )


def _n_folds(y: np.ndarray, requested: int) -> int:
    smallest = int(min(np.sum(y == 0), np.sum(y == 1)))
    return max(2, min(int(requested), smallest))


def _workers(cfg: dict) -> int:
    return int(cfg["random_forest"].get("n_jobs", -1) or 1)


def missing_fraction(X: pd.DataFrame) -> np.ndarray:
    return X.isna().mean(axis=1).to_numpy()


def decide(scores, X: pd.DataFrame, thresholds: dict, max_missing: float) -> np.ndarray:
    decisions = apply_thresholds(scores, thresholds["positive"], thresholds["negative"])
    decisions[missing_fraction(X) > max_missing] = INCONCLUSIVE
    return decisions


def _fit_fold(X, y, train, test, cfg, seed, importance):
    """One cross-validation fit (runs in a worker process)."""
    forest = build_forest(cfg, seed, n_jobs=1).fit(X.iloc[train], y[train])
    scores = forest.predict_proba(X.iloc[test])[:, 1]
    imp = None
    if importance:
        imp = permutation_importance(forest, X.iloc[test], y[test], scoring="roc_auc",
                                     n_repeats=5, random_state=seed).importances_mean
    return test, scores, imp


def out_of_fold_scores(X, y, cfg, n_repeats, seed, importance=False, counter=None, parallel=True) -> dict:
    folds = _n_folds(y, cfg["validation"]["cv_folds"])
    splitter = RepeatedStratifiedKFold(n_splits=folds, n_repeats=n_repeats, random_state=seed)
    splits = list(splitter.split(X, y))
    tasks = (delayed(_fit_fold)(X, y, tr, te, cfg, seed + k, importance and k < folds)
             for k, (tr, te) in enumerate(splits))
    runner = Parallel(n_jobs=_workers(cfg) if parallel else 1, return_as="generator")
    per_repeat = np.full((n_repeats, len(y)), np.nan)
    importances = []
    for k, (test, scores, imp) in enumerate(runner(tasks)):
        per_repeat[k // folds, test] = scores
        if imp is not None:
            importances.append(imp)
        if counter:
            counter.step(f"Cross-validation: fit {k + 1}/{len(splits)}")
    out = {"scores": per_repeat.mean(axis=0), "folds": folds, "repeats": n_repeats,
           "repeat_aucs": [float(roc_auc_score(y, row)) for row in per_repeat]}
    if importances:
        stack = np.vstack(importances)
        out["importance"] = pd.DataFrame({
            "feature": list(X.columns),
            "mean_auc_decrease": stack.mean(axis=0),
            "sd": stack.std(axis=0),
        }).sort_values("mean_auc_decrease", ascending=False).reset_index(drop=True)
    return out


def fit_procedure(X, y, cfg, n_repeats, seed, importance=False, counter=None, parallel=True) -> dict:
    """Steps 2-4 of the module docstring on (X, y)."""
    dec = cfg["decision"]
    oof = out_of_fold_scores(X, y, cfg, n_repeats, seed, importance, counter, parallel)
    kwargs = dict(use_bound=bool(dec["use_confidence_bound"]), confidence=float(dec["confidence_level"]),
                  min_calls=int(dec["min_calls_per_side"]))
    sel_pos = select_threshold(oof["scores"], y, "positive", float(dec["target_ppv"]), **kwargs)
    sel_neg = select_threshold(oof["scores"], y, "negative", float(dec["target_npv"]), **kwargs)
    forest = build_forest(cfg, seed, n_jobs=None if parallel else 1).fit(X, y)
    if counter:
        counter.step("Fitting final Random Forest")
    thresholds = {
        "positive": sel_pos["chosen"]["threshold"] if sel_pos["chosen"] else None,
        "negative": sel_neg["chosen"]["threshold"] if sel_neg["chosen"] else None,
    }
    return {"model": forest, "thresholds": thresholds, "selection_positive": sel_pos,
            "selection_negative": sel_neg, "oof": oof}


def _outer_fold(X, y, train, test, cfg, seed):
    """One outer fold of the nested cross-validation (runs in a worker process)."""
    proc = fit_procedure(X.iloc[train], y[train], cfg, int(cfg["validation"]["inner_repeats"]),
                         seed, parallel=False)
    scores = proc["model"].predict_proba(X.iloc[test])[:, 1]
    decisions = decide(scores, X.iloc[test], proc["thresholds"], float(cfg["decision"]["max_missing_fraction"]))
    return test, scores, decisions, proc["thresholds"]


def nested_evaluation(X, y, cfg, seed, counter=None) -> dict:
    folds = _n_folds(y, cfg["validation"]["outer_folds"])
    outer = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed + 1000)
    splits = list(outer.split(X, y))
    tasks = (delayed(_outer_fold)(X, y, tr, te, cfg, seed + 100 * (k + 1)) for k, (tr, te) in enumerate(splits))
    scores = np.full(len(y), np.nan)
    decisions = np.full(len(y), INCONCLUSIVE)
    fold_thresholds = [None] * folds
    runner = Parallel(n_jobs=_workers(cfg), return_as="generator")
    for k, (test, s, d, thr) in enumerate(runner(tasks)):
        scores[test], decisions[test], fold_thresholds[k] = s, d, thr
        if counter:
            counter.step(f"Nested validation: outer fold {k + 1}/{folds}")
    return {"scores": scores, "decisions": decisions, "fold_thresholds": fold_thresholds,
            "outer_folds": folds,
            "metrics": triage_metrics(y, decisions, float(cfg["decision"]["confidence_level"]))}


def _select_training_rows(prepared: PreparedData, cfg: dict) -> tuple[np.ndarray, dict, list[str]]:
    if prepared.labels is None:
        raise TrainingError("The training file has no lumbar-puncture result column.")
    labels = prepared.labels.to_numpy(float)
    ptau = prepared.table["ptau217"].to_numpy(float)
    has_label = ~np.isnan(labels)
    has_ptau = ~np.isnan(ptau)
    grey = in_grey_zone(ptau, cfg)
    keep = has_label & has_ptau
    exclusions = {
        "rows_in_file": prepared.n,
        "missing_lp_result": int(np.sum(~has_label)),
        "missing_ptau217": int(np.sum(has_label & ~has_ptau)),
        "outside_grey_zone": 0,
    }
    messages = []
    if cfg["grey_zone"]["train_only_on_grey_zone"]:
        outside = keep & ~grey
        exclusions["outside_grey_zone"] = int(outside.sum())
        if outside.any():
            messages.append(f"{int(outside.sum())} patient(s) with p-tau217 outside the grey zone "
                            "were excluded from training.")
        keep &= grey
    if exclusions["missing_lp_result"]:
        messages.append(f"{exclusions['missing_lp_result']} row(s) without a usable LP result were excluded.")
    if exclusions["missing_ptau217"]:
        messages.append(f"{exclusions['missing_ptau217']} row(s) without p-tau217 were excluded.")
    return np.flatnonzero(keep), exclusions, messages


def train_model(prepared: PreparedData, cfg: dict, nested: bool | None = None,
                progress: Progress = None, source_name: str = "") -> dict:
    """Train the full procedure and return a model bundle (a plain dict)."""
    val = cfg["validation"]
    seed = int(val["random_state"])
    nested = bool(val["nested_cv"]) if nested is None else nested
    rows, exclusions, messages = _select_training_rows(prepared, cfg)
    messages = list(prepared.messages) + messages

    y = prepared.labels.to_numpy(float)[rows].astype(int)
    n_pos, n_neg = int(np.sum(y == 1)), int(np.sum(y == 0))
    if min(n_pos, n_neg) < MIN_PER_CLASS:
        raise TrainingError(f"Too few patients: {n_pos} LP-positive and {n_neg} LP-negative in the grey zone "
                            f"(at least {MIN_PER_CLASS} of each are required; several hundred are recommended).")

    table = prepared.table.iloc[rows].reset_index(drop=True)
    candidates = model_feature_names(cfg)
    features = [f for f in candidates if table[f].notna().any()]
    dropped = [f for f in candidates if f not in features]
    if dropped:
        messages.append("Variables with no data in the training file (not used by the model): "
                        + ", ".join(dropped) + ".")
    sparse = [f"{f} ({table[f].isna().mean():.0%})" for f in features if table[f].isna().mean() > 0.4]
    if sparse:
        messages.append("Variables missing in more than 40% of patients: " + ", ".join(sparse) + ".")
    issues = sum(1 for i in rows if prepared.row_issues[i])
    if issues:
        messages.append(f"{issues} training patient(s) had implausible/invalid values; those values were "
                        "treated as missing (see the OOF predictions file).")

    X = table[features]
    folds = _n_folds(y, val["cv_folds"])
    total = folds * int(val["cv_repeats"]) + 1
    if nested:
        total += _n_folds(y, val["outer_folds"])
    counter = _Counter(total, progress)

    proc = fit_procedure(X, y, cfg, int(val["cv_repeats"]), seed,
                         importance=bool(val.get("permutation_importance", True)), counter=counter)
    oof_scores = proc["oof"]["scores"]
    max_missing = float(cfg["decision"]["max_missing_fraction"])
    oof_decisions = decide(oof_scores, X, proc["thresholds"], max_missing)
    conf = float(cfg["decision"]["confidence_level"])

    auc_model, auc_model_ci = bootstrap_auc_ci(y, oof_scores, seed=seed)
    auc_ptau, auc_ptau_ci = bootstrap_auc_ci(y, X["ptau217"].to_numpy(float), seed=seed)
    fpr, tpr, _ = roc_curve(y, oof_scores)
    fpr_p, tpr_p, _ = roc_curve(y, X["ptau217"].to_numpy(float))

    nested_result = nested_evaluation(X, y, cfg, seed, counter) if nested else None

    for side, key in (("positive", "selection_positive"), ("negative", "selection_negative")):
        if proc["thresholds"][side] is None:
            word = "POSITIVE (rule-in)" if side == "positive" else "NEGATIVE (rule-out)"
            messages.append(f"No threshold reached the safety target for {word} calls with the current data: "
                            f"the model will never call a patient {side.upper()}. More patients are needed.")

    predictions = pd.DataFrame({
        "patient_id": [prepared.ids[i] for i in rows],
        "lp_result": np.where(y == 1, "Positive", "Negative"),
        "ptau217": X["ptau217"].to_numpy(),
        "rf_score_oof": np.round(oof_scores, 4),
        "decision_oof": [_decision_word(d) for d in oof_decisions],
        "missing_fraction": np.round(missing_fraction(X), 3),
        "data_issues": ["; ".join(prepared.row_issues[i]) for i in rows],
    })
    if nested_result:
        predictions["rf_score_nested"] = np.round(nested_result["scores"], 4)
        predictions["decision_nested"] = [_decision_word(d) for d in nested_result["decisions"]]

    report = {
        "created": dt.datetime.now().isoformat(timespec="seconds"),
        "source_file": source_name,
        "cohort": {**exclusions, "n_train": int(len(y)), "n_lp_positive": n_pos, "n_lp_negative": n_neg,
                   "prevalence": n_pos / len(y)},
        "features": features,
        "cv": {"folds": proc["oof"]["folds"], "repeats": proc["oof"]["repeats"],
               "repeat_aucs": proc["oof"]["repeat_aucs"]},
        "auc_model": {"value": auc_model, "ci": auc_model_ci},
        "auc_ptau217_alone": {"value": auc_ptau, "ci": auc_ptau_ci},
        "roc": {"model": [fpr.tolist(), tpr.tolist()], "ptau217": [fpr_p.tolist(), tpr_p.tolist()]},
        "thresholds": proc["thresholds"],
        "threshold_details": {
            "positive": proc["selection_positive"]["chosen"],
            "negative": proc["selection_negative"]["chosen"],
        },
        "threshold_curves": {
            "positive": proc["selection_positive"]["candidates"],
            "negative": proc["selection_negative"]["candidates"],
        },
        "oof_triage": triage_metrics(y, oof_decisions, conf),
        "nested": None if nested_result is None else {
            "outer_folds": nested_result["outer_folds"],
            "fold_thresholds": nested_result["fold_thresholds"],
            "metrics": nested_result["metrics"],
        },
        "importance": (proc["oof"]["importance"].to_dict(orient="records")
                       if "importance" in proc["oof"] else None),
        "decision_rule": dict(cfg["decision"]),
        "calls_needed_for_bound": minimum_calls_needed(float(cfg["decision"]["target_ppv"]), conf, 5),
        "messages": messages,
    }

    return {
        "format_version": FORMAT_VERSION,
        "created": report["created"],
        "model": proc["model"],
        "features": features,
        "thresholds": proc["thresholds"],
        "config": config_snapshot(cfg),
        "training_ranges": {f: [float(np.nanmin(X[f])), float(np.nanmax(X[f]))] for f in features},
        "oof_scores": oof_scores,
        "oof_labels": y,
        "predictions": predictions,
        "report": report,
        "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__},
    }


def _decision_word(code: int) -> str:
    return {1: "POSITIVE", 0: "NEGATIVE"}.get(int(code), "INCONCLUSIVE")


def save_bundle(bundle: dict, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "model.joblib"
    joblib.dump(bundle, path, compress=3)
    return path


def load_bundle(path: str | Path) -> dict:
    """Load a model saved by :func:`save_bundle`.

    Security note: joblib/pickle files can execute code when loaded. Only load
    model files that you created yourself.
    """
    path = Path(path)
    if path.is_dir():
        path = path / "model.joblib"
    bundle = joblib.load(path)
    if not isinstance(bundle, dict) or bundle.get("format_version") != FORMAT_VERSION:
        raise TrainingError(f"{path} is not a model file produced by this project (or an old version).")
    return bundle
