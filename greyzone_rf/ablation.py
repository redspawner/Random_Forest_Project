"""Which variables help, and which only add noise? (leave-one-variable-out analysis)

For the full variable set and for every set with ONE variable removed, the same repeated
cross-validation is run (same patients, same folds). The table compares:

    AUC                 discrimination of the cross-validated RF score
    resolved            % of grey-zone patients that get a 95%-certified answer (LPs avoided)
    errors              wrong calls among them

A variable whose removal does not lower the AUC or the share resolved contributes nothing; if its
removal *raises* them it is detrimental (it adds noise). Differences smaller than the run-to-run
noise (estimated by repeating the full model with another random seed) are not meaningful.
"""

from __future__ import annotations

import copy

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .config import model_feature_names
from .data import PreparedData, in_grey_zone
from .model import out_of_fold_scores
from .stats import apply_thresholds, select_threshold, triage_metrics


def _evaluate(X, y, cfg, seed):
    dec = cfg["decision"]
    oof = out_of_fold_scores(X, y, cfg, int(cfg["validation"]["cv_repeats"]), seed)["scores"]
    kwargs = dict(use_bound=bool(dec["use_confidence_bound"]), confidence=float(dec["confidence_level"]),
                  min_calls=int(dec["min_calls_per_side"]))
    pos = select_threshold(oof, y, "positive", float(dec["target_ppv"]), **kwargs)["chosen"]
    neg = select_threshold(oof, y, "negative", float(dec["target_npv"]), **kwargs)["chosen"]
    d = apply_thresholds(oof, pos["threshold"] if pos else None, neg["threshold"] if neg else None)
    m = triage_metrics(y, d)
    return {"auc": roc_auc_score(y, oof), "resolved": m["resolved"]["value"], "errors": m["errors"]}


def variable_contributions(prepared: PreparedData, cfg: dict, repeats: int = 3, seeds: int = 2,
                           baseline_seeds: int = 4, progress=None) -> pd.DataFrame:
    """Leave-one-variable-out table. Each run is averaged over ``seeds`` random seeds; the noise level
    is the standard deviation of the full model over ``baseline_seeds`` seeds."""
    cfg = copy.deepcopy(cfg)
    cfg["validation"]["cv_repeats"] = repeats
    labels = prepared.labels.to_numpy(float)
    ptau = prepared.table["ptau217"].to_numpy(float)
    keep = ~np.isnan(labels) & ~np.isnan(ptau) & in_grey_zone(ptau, cfg)
    table = prepared.table[keep].reset_index(drop=True)
    y = labels[keep].astype(int)
    features = [f for f in model_feature_names(cfg) if table[f].notna().any()]
    seed0 = int(cfg["validation"]["random_state"])
    total = baseline_seeds + seeds * (len(features) - 1)
    done = [0]

    def run(cols, seed, label):
        r = _evaluate(table[cols], y, cfg, seed)
        done[0] += 1
        if progress:
            progress(done[0] / total, label)
        return r

    base_runs = [run(features, seed0 + s, "full model") for s in range(baseline_seeds)]
    base_auc = np.array([r["auc"] for r in base_runs])
    base_res = np.array([100 * r["resolved"] for r in base_runs])
    rows = []
    for feature in features:
        if feature == "ptau217":          # defines the grey zone: always kept
            continue
        cols = [f for f in features if f != feature]
        runs = [run(cols, seed0 + s, f"without {feature}") for s in range(seeds)]
        auc = np.mean([r["auc"] for r in runs])
        res = np.mean([100 * r["resolved"] for r in runs])
        rows.append({"variable": feature,
                     "missing_%": round(100 * table[feature].isna().mean(), 1),
                     "delta_AUC_if_removed": round(auc - base_auc[:seeds].mean(), 4),
                     "delta_resolved_pts_if_removed": round(res - base_res[:seeds].mean(), 1),
                     "errors_without": float(np.mean([r["errors"] for r in runs]))})
    out = pd.DataFrame(rows).sort_values("delta_AUC_if_removed", ascending=False).reset_index(drop=True)
    out.attrs.update(baseline_auc=float(base_auc.mean()), baseline_resolved=float(base_res.mean()),
                     baseline_errors=float(np.mean([r["errors"] for r in base_runs])),
                     noise_auc=float(base_auc.std(ddof=1)), noise_resolved=float(base_res.std(ddof=1)))
    return out


def verdict(row, noise_auc: float, noise_res: float) -> str:
    """AUC is the main criterion (stable); % resolved moves in steps and is only a tie-breaker."""
    d_auc, d_res = row["delta_AUC_if_removed"], row["delta_resolved_pts_if_removed"]
    limit = max(2 * noise_auc, 0.0015)
    if d_auc < -limit or d_res < -2 * max(noise_res, 1.0):
        return "useful - keep"
    if d_auc > limit and d_res > -max(noise_res, 1.0):
        return "detrimental - removal improves the model"
    return "no measurable contribution"


def forward_selection(prepared: PreparedData, cfg: dict, max_variables: int | None = None, repeats: int = 2,
                      start: tuple[str, ...] = ("ptau217",), progress=None) -> pd.DataFrame:
    """Greedy forward selection by cross-validated AUC.

    Starting from p-tau217, the variable that increases the cross-validated AUC the most is added at
    each step. The resulting curve shows how much each extra variable is worth, and where adding
    more stops helping (the plateau). Same folds and seed for every candidate.
    """
    cfg = copy.deepcopy(cfg)
    cfg["validation"]["cv_repeats"] = repeats
    labels = prepared.labels.to_numpy(float)
    ptau = prepared.table["ptau217"].to_numpy(float)
    keep = ~np.isnan(labels) & ~np.isnan(ptau) & in_grey_zone(ptau, cfg)
    table = prepared.table[keep].reset_index(drop=True)
    y = labels[keep].astype(int)
    pool = [f for f in model_feature_names(cfg) if table[f].notna().any() and f not in start]
    seed = int(cfg["validation"]["random_state"])
    chosen = list(start)
    first = _evaluate(table[chosen], y, cfg, seed)
    rows = [{"step": 0, "added": "+".join(start), "n_variables": len(chosen), "auc": round(first["auc"], 4),
             "resolved_%": round(100 * first["resolved"], 1), "errors": first["errors"]}]
    max_variables = max_variables or len(pool) + len(start)
    step = 0
    while pool and len(chosen) < max_variables:
        step += 1
        results = {}
        for cand in pool:
            results[cand] = _evaluate(table[chosen + [cand]], y, cfg, seed)
            if progress:
                progress(step, f"step {step}: tried {cand}")
        best = max(results, key=lambda c: results[c]["auc"])
        chosen.append(best)
        pool.remove(best)
        r = results[best]
        rows.append({"step": step, "added": best, "n_variables": len(chosen), "auc": round(r["auc"], 4),
                     "resolved_%": round(100 * r["resolved"], 1), "errors": r["errors"]})
    return pd.DataFrame(rows)
