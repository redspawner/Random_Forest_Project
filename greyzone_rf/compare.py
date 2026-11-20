"""Side-by-side comparison of models trained on the same patients.

All models are trained with the same procedure and the same random splits (same seed), so their
out-of-fold and nested scores belong to the same patients in the same folds: the comparison is
*paired*. The differences are given with bootstrap confidence intervals, because with a few hundred
patients small differences are mostly noise. Picking the best of several models on the same data is
itself slightly optimistic - confirm the choice on an independent cohort.
"""

from __future__ import annotations

import io
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import brier_score_loss, roc_auc_score  # noqa: E402

from .estimators import model_label  # noqa: E402
from .i18n import tr  # noqa: E402
from .predict import predict_prepared  # noqa: E402
from .report import GRID, INK, INK_2, _fig  # noqa: E402
from .stats import NEGATIVE, POSITIVE  # noqa: E402

# One colour per model (validated categorical palette, same family as the report figures)
COLORS = ["#2a78d6", "#eb6834", "#1f9e6e", "#8a5cc7", "#c0841b", "#d0457a", "#4a4a48"]


def _nested_arrays(bundle: dict) -> tuple[np.ndarray | None, np.ndarray | None]:
    nested = bundle.get("nested_scores"), bundle.get("nested_decisions")
    return (None, None) if nested[0] is None else (np.asarray(nested[0], float), np.asarray(nested[1], int))


def same_patients(bundles: dict[str, dict]) -> bool:
    """True when all bundles were trained on the same patients (same labels in the same order)."""
    labels = [np.asarray(b["oof_labels"]) for b in bundles.values()]
    return all(len(x) == len(labels[0]) and np.array_equal(x, labels[0]) for x in labels)


def _ci_text(p: dict) -> str:
    if not p["n"]:
        return "-"
    return f"{p['value']:.1%} ({p['ci'][0]:.1%}-{p['ci'][1]:.1%})"


def comparison_table(bundles: dict[str, dict]) -> pd.DataFrame:
    """One row per model with discrimination, calibration, thresholds and honest (nested) triage results."""
    rows = []
    for name, b in bundles.items():
        r = b["report"]
        y, s = np.asarray(b["oof_labels"], int), np.asarray(b["oof_scores"], float)
        row = {
            tr("Model"): name,
            tr("AUC (95% CI)"): f"{r['auc_model']['value']:.3f} ({r['auc_model']['ci'][0]:.3f}-"
                                f"{r['auc_model']['ci'][1]:.3f})",
            tr("Brier score"): round(float(brier_score_loss(y, s)), 3),
            tr("POSITIVE if score >="): "-" if b["thresholds"]["positive"] is None else b["thresholds"]["positive"],
            tr("NEGATIVE if score <="): "-" if b["thresholds"]["negative"] is None else b["thresholds"]["negative"],
        }
        m = (r.get("nested") or {}).get("metrics")
        if m:
            row.update({
                tr("LPs avoided (nested)"): _ci_text(m["resolved"]),
                tr("Wrong calls (FP / FN)"): f"{m['errors']} ({m['false_positive']} / {m['false_negative']})",
                tr("PPV (nested)"): _ci_text(m["ppv"]),
                tr("NPV (nested)"): _ci_text(m["npv"]),
            })
        rows.append(row)
    return pd.DataFrame(rows)


def paired_differences(bundles: dict[str, dict], reference: str, n_boot: int = 2000, seed: int = 0) -> pd.DataFrame:
    """AUC and LPs-avoided difference of every model versus ``reference`` (paired bootstrap, 95% CI)."""
    ref = bundles[reference]
    y = np.asarray(ref["oof_labels"], int)
    s_ref = np.asarray(ref["oof_scores"], float)
    _, d_ref = _nested_arrays(ref)
    rng = np.random.default_rng(seed)
    idx_all = [rng.integers(0, len(y), len(y)) for _ in range(n_boot)]
    rows = []
    for name, b in bundles.items():
        if name == reference:
            continue
        s = np.asarray(b["oof_scores"], float)
        _, d = _nested_arrays(b)
        auc_diff, res_diff, err_diff = [], [], []
        for idx in idx_all:
            if y[idx].min() == y[idx].max():
                continue
            auc_diff.append(roc_auc_score(y[idx], s[idx]) - roc_auc_score(y[idx], s_ref[idx]))
            if d is not None and d_ref is not None:
                res_diff.append(np.mean(d[idx] != -1) - np.mean(d_ref[idx] != -1))
                err_diff.append(_errors(y[idx], d[idx]) - _errors(y[idx], d_ref[idx]))
        point = roc_auc_score(y, s) - roc_auc_score(y, s_ref)
        row = {tr("Model"): name, tr("AUC difference (95% CI)"): _diff_text(point, auc_diff, 3),
               tr("AUC difference significant?"): _significant(auc_diff)}
        if res_diff:
            point_res = np.mean(d != -1) - np.mean(d_ref != -1)
            row[tr("LPs avoided difference (95% CI)")] = _diff_text(point_res, res_diff, None)
            row[tr("Wrong-call difference (95% CI)")] = _diff_text(_errors(y, d) - _errors(y, d_ref), err_diff, 0)
            row[tr("LPs avoided difference significant?")] = _significant(res_diff)
        rows.append(row)
    return pd.DataFrame(rows)


def _errors(y, d) -> int:
    return int(np.sum((d == POSITIVE) & (y == 0)) + np.sum((d == NEGATIVE) & (y == 1)))


def _diff_text(point, values, digits) -> str:
    lo, hi = np.quantile(values, [0.025, 0.975])
    if digits is None:
        return f"{point:+.1%} ({lo:+.1%} to {hi:+.1%})"
    return f"{point:+.{digits}f} ({lo:+.{digits}f} to {hi:+.{digits}f})"


def _significant(values) -> str:
    lo, hi = np.quantile(values, [0.025, 0.975])
    return tr("yes") if lo > 0 or hi < 0 else tr("no")


# ---------------------------------------------------------------------------
# Figures (returned as PNG bytes)
# ---------------------------------------------------------------------------
def _png(fig) -> bytes:
    buffer = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    return buffer.getvalue()


def roc_figure(bundles: dict[str, dict]) -> bytes:
    fig, ax = _fig(figsize=(5.4, 4.8))
    ax.plot([0, 1], [0, 1], color=GRID, linewidth=1)
    first = next(iter(bundles.values()))
    fpr, tpr = first["report"]["roc"]["ptau217"]
    ax.plot(fpr, tpr, color=INK_2, linewidth=1.5, linestyle="--",
            label=tr("p-tau217 alone  AUC {v:.2f}", v=first["report"]["auc_ptau217_alone"]["value"]))
    for color, (name, b) in zip(COLORS, bundles.items()):
        fpr, tpr = b["report"]["roc"]["model"]
        ax.plot(fpr, tpr, color=color, linewidth=2,
                label=tr("{model}  AUC {v:.2f}", model=name, v=b["report"]["auc_model"]["value"]))
    ax.set_xlabel(tr("1 - specificity"), color=INK_2, fontsize=9)
    ax.set_ylabel(tr("Sensitivity"), color=INK_2, fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    ax.legend(frameon=False, fontsize=7.5, loc="lower right", labelcolor=INK)
    ax.set_title(tr("Discrimination inside the grey zone\n(cross-validated)"), color=INK, fontsize=10, loc="left")
    return _png(fig)


def triage_figure(bundles: dict[str, dict]) -> bytes:
    """Nested validation: share of LPs avoided (bar) and wrong calls (label) per model."""
    names, avoided, lo, hi, errors = [], [], [], [], []
    for name, b in bundles.items():
        m = (b["report"].get("nested") or {}).get("metrics")
        if not m:
            continue
        names.append(name)
        avoided.append(m["resolved"]["value"])
        lo.append(m["resolved"]["value"] - m["resolved"]["ci"][0])
        hi.append(m["resolved"]["ci"][1] - m["resolved"]["value"])
        errors.append(m["errors"])
    fig, ax = _fig(figsize=(6.4, 0.55 * max(len(names), 1) + 1.4))
    ypos = np.arange(len(names))[::-1]
    ax.barh(ypos, avoided, xerr=[lo, hi], color=COLORS[:len(names)], height=0.6,
            error_kw={"ecolor": INK_2, "elinewidth": 0.8, "capsize": 0})
    for yp, value, err, upper in zip(ypos, avoided, errors, hi):
        ax.text(value + upper + 0.01, yp, tr("{v:.0%} ({e} wrong)", v=value, e=err), va="center", fontsize=8,
                color=INK)
    ax.set_yticks(ypos, names)
    ax.set_xlim(0, min(1.0, max(avoided + [0.1]) + max(hi + [0]) + 0.18))
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel(tr("Lumbar punctures avoided in nested validation (95% CI)"), color=INK_2, fontsize=9)
    ax.grid(axis="y", visible=False)
    return _png(fig)


def calibration_figure(bundles: dict[str, dict], bins: int = 8) -> bytes:
    """Reliability diagram: mean score vs observed share of LP-positive patients (quantile bins)."""
    fig, ax = _fig(figsize=(5.4, 4.8))
    ax.plot([0, 1], [0, 1], color=GRID, linewidth=1)
    for color, (name, b) in zip(COLORS, bundles.items()):
        y, s = np.asarray(b["oof_labels"], int), np.asarray(b["oof_scores"], float)
        edges = np.unique(np.quantile(s, np.linspace(0, 1, bins + 1)))
        groups = np.clip(np.searchsorted(edges, s, side="right") - 1, 0, len(edges) - 2)
        xs = [s[groups == g].mean() for g in range(len(edges) - 1) if np.any(groups == g)]
        ys = [y[groups == g].mean() for g in range(len(edges) - 1) if np.any(groups == g)]
        ax.plot(xs, ys, color=color, linewidth=1.8, marker="o", markersize=3.5, label=name)
    ax.set_xlabel(tr("Mean model score (out-of-fold)"), color=INK_2, fontsize=9)
    ax.set_ylabel(tr("Observed share LP-positive"), color=INK_2, fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", labelcolor=INK)
    ax.set_title(tr("Calibration (closer to the diagonal = better)"), color=INK, fontsize=10, loc="left")
    return _png(fig)


# ---------------------------------------------------------------------------
# New patients classified by every model
# ---------------------------------------------------------------------------
def classify_with_all(bundles: dict[str, dict], prepared) -> pd.DataFrame:
    """One row per patient: decision and score of every model, and whether the models agree."""
    out = None
    for name, b in bundles.items():
        res = predict_prepared(b, prepared)
        part = res[["patient_id", "decision", "score"]].rename(
            columns={"decision": f"{name}: {tr('decision')}", "score": f"{name}: {tr('score')}"})
        out = part if out is None else out.merge(part.drop(columns="patient_id"), left_index=True,
                                                 right_index=True)
    decision_cols = [c for c in out.columns if c.endswith(f": {tr('decision')}")]
    out[tr("All models agree")] = out[decision_cols].nunique(axis=1).eq(1).map({True: tr("yes"), False: tr("no")})
    return out


def display_names(bundles_by_type: dict[str, dict]) -> dict[str, dict]:
    """Key the bundles by their readable model name."""
    return {model_label(kind): b for kind, b in bundles_by_type.items()}


def is_finite(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))
