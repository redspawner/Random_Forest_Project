"""Statistics behind the "95% confidence" rule.

Why not plain conformal prediction?
-----------------------------------
A standard (marginal) conformal predictor with alpha = 0.05 guarantees that the
true label is inside the prediction *set* for 95% of patients - but patients
who receive the set {Positive, Negative} (i.e. "inconclusive") always count as
covered. The error rate among the patients who actually receive a single
answer can therefore be much higher than 5%. What matters clinically is:

    "Of the patients the tool calls POSITIVE, how many are truly positive?"  (PPV)
    "Of the patients the tool calls NEGATIVE, how many are truly negative?"  (NPV)

So this module selects two thresholds on the Random-Forest score so that the
PPV of POSITIVE calls and the NPV of NEGATIVE calls reach the target (95%),
and - by default - requires the *lower* one-sided Clopper-Pearson confidence
bound of that PPV/NPV to reach the target, not just the point estimate.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import beta

POSITIVE, NEGATIVE, INCONCLUSIVE = 1, 0, -1


def cp_lower_bound(successes: int, trials: int, confidence: float = 0.95) -> float:
    """One-sided Clopper-Pearson lower confidence bound for a proportion."""
    if trials <= 0 or successes <= 0:
        return 0.0
    return float(beta.ppf(1.0 - confidence, successes, trials - successes + 1))


def cp_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    """Two-sided Clopper-Pearson (exact) confidence interval for a proportion."""
    if trials <= 0:
        return (math.nan, math.nan)
    a = 1.0 - confidence
    lower = 0.0 if successes == 0 else float(beta.ppf(a / 2, successes, trials - successes + 1))
    upper = 1.0 if successes == trials else float(beta.ppf(1 - a / 2, successes + 1, trials - successes))
    return (lower, upper)


def minimum_calls_needed(target: float = 0.95, confidence: float = 0.95, max_errors: int = 5) -> dict[int, int]:
    """Smallest number of calls for which the lower bound reaches ``target``
    when ``e`` of them are wrong, for e = 0..max_errors."""
    out = {}
    for errors in range(max_errors + 1):
        n = errors + 1
        while cp_lower_bound(n - errors, n, confidence) < target:
            n += 1
        out[errors] = n
    return out


POSITIVE_GRID = np.round(np.arange(0.50, 1.0 + 1e-9, 0.01), 2)
NEGATIVE_GRID = np.round(np.arange(0.00, 0.50 + 1e-9, 0.01), 2)


def _evaluate_side(scores, y, side, threshold, confidence):
    if side == "positive":
        called = scores >= threshold
        correct = int(np.sum(called & (y == 1)))
    else:
        called = scores <= threshold
        correct = int(np.sum(called & (y == 0)))
    n_called = int(called.sum())
    value = correct / n_called if n_called else math.nan
    return {
        "threshold": float(threshold),
        "n_called": n_called,
        "n_correct": correct,
        "n_wrong": n_called - correct,
        "predictive_value": value,
        "lower_bound": cp_lower_bound(correct, n_called, confidence),
    }


def select_threshold(scores, y, side: str, target: float, use_bound: bool = True,
                     confidence: float = 0.95, min_calls: int = 10) -> dict:
    """Choose the most permissive threshold that still meets the safety target.

    side="positive": patients with score >= threshold are called POSITIVE (PPV).
    side="negative": patients with score <= threshold are called NEGATIVE (NPV).
    Returns a dict with the chosen threshold (or None if no threshold is safe)
    and the full table of candidates (for plots and reports).
    """
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    grid = POSITIVE_GRID if side == "positive" else NEGATIVE_GRID
    rows = []
    for t in grid:
        row = _evaluate_side(scores, y, side, t, confidence)
        metric = row["lower_bound"] if use_bound else row["predictive_value"]
        row["passes"] = bool(row["n_called"] >= min_calls and not math.isnan(metric) and metric >= target)
        rows.append(row)
    passing = [r for r in rows if r["passes"]]
    if not passing:
        chosen = None
    elif side == "positive":
        chosen = min(passing, key=lambda r: r["threshold"])
    else:
        chosen = max(passing, key=lambda r: r["threshold"])
    return {"side": side, "target": target, "use_bound": use_bound, "confidence": confidence,
            "min_calls": min_calls, "chosen": chosen, "candidates": rows}


def apply_thresholds(scores, threshold_positive: float | None, threshold_negative: float | None) -> np.ndarray:
    """Map scores to POSITIVE (1), NEGATIVE (0) or INCONCLUSIVE (-1)."""
    scores = np.asarray(scores, dtype=float)
    decisions = np.full(scores.shape, INCONCLUSIVE, dtype=int)
    is_pos = scores >= threshold_positive if threshold_positive is not None else np.zeros_like(scores, bool)
    is_neg = scores <= threshold_negative if threshold_negative is not None else np.zeros_like(scores, bool)
    decisions[is_pos & ~is_neg] = POSITIVE
    decisions[is_neg & ~is_pos] = NEGATIVE
    return decisions


def triage_metrics(y, decisions, confidence: float = 0.95) -> dict:
    """Clinical summary of a three-way triage against the LP reference."""
    y = np.asarray(y, dtype=int)
    d = np.asarray(decisions, dtype=int)
    n = len(y)
    tp = int(np.sum((d == POSITIVE) & (y == 1)))
    fp = int(np.sum((d == POSITIVE) & (y == 0)))
    tn = int(np.sum((d == NEGATIVE) & (y == 0)))
    fn = int(np.sum((d == NEGATIVE) & (y == 1)))
    inconclusive = int(np.sum(d == INCONCLUSIVE))
    resolved = tp + fp + tn + fn
    n_pos, n_neg = int(np.sum(y == 1)), int(np.sum(y == 0))

    def prop(k, m):
        return {"k": k, "n": m, "value": (k / m) if m else math.nan, "ci": cp_interval(k, m, confidence)}

    return {
        "n": n, "n_lp_positive": n_pos, "n_lp_negative": n_neg,
        "called_positive": tp + fp, "called_negative": tn + fn, "inconclusive": inconclusive,
        "true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn,
        "ppv": prop(tp, tp + fp),
        "npv": prop(tn, tn + fn),
        "resolved": prop(resolved, n),                 # = lumbar punctures avoided
        "accuracy_resolved": prop(tp + tn, resolved),
        "positives_ruled_in": prop(tp, n_pos),         # share of LP+ patients spared LP
        "negatives_ruled_out": prop(tn, n_neg),        # share of LP- patients spared LP
        "errors": fp + fn,
    }


def bootstrap_auc_ci(y, scores, n_boot: int = 1000, confidence: float = 0.95, seed: int = 0):
    """Percentile bootstrap confidence interval for the ROC AUC."""
    from sklearn.metrics import roc_auc_score

    y = np.asarray(y, dtype=int)
    scores = np.asarray(scores, dtype=float)
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].min() == y[idx].max():
            continue
        values.append(roc_auc_score(y[idx], scores[idx]))
    a = (1 - confidence) / 2
    return float(roc_auc_score(y, scores)), (float(np.quantile(values, a)), float(np.quantile(values, 1 - a)))
