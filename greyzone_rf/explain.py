"""SHAP explanations: how much each variable pushed one patient's score up or down.

Method
------
For a patient, the SHAP value of a variable is its average contribution to the model score over all
possible orders in which the variables could be "revealed" (Shapley values, from cooperative game
theory; Lundberg & Lee 2017). "Not revealed" means the value is replaced by the values of real
training patients (the *background*, 100 patients stored in the model file). With the 8-12
variables of this project the Shapley values are computed **exactly** (every subset of variables,
``shap.explainers.ExactExplainer``), so:

    score of the patient = average score of the background + sum of the SHAP values

All values are on the **score scale** (0-1, the scale the POSITIVE/NEGATIVE thresholds use), so a
SHAP value of +0.08 means "this variable raised the score by 8 percentage points". The method is the
same for every model type (Random Forest, Logistic Regression, XGBoost, ...), so explanations can be
compared between models.

Read them as "why did the MODEL give this score", not as causal effects: correlated variables share
credit (e.g. eGFR and anaemia), and a model can use a variable in a way that does not reflect biology.
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .i18n import column_name, tr  # noqa: E402
from .report import BLUE, INK, INK_2, ORANGE, _fig  # noqa: E402

BACKGROUND_SIZE = 100


def background_sample(X: pd.DataFrame, seed: int = 0, size: int = BACKGROUND_SIZE) -> pd.DataFrame:
    """Training patients used as the 'average patient' reference (stored in the model file)."""
    if len(X) <= size:
        return X.reset_index(drop=True).copy()
    return X.sample(size, random_state=seed).reset_index(drop=True)


def available(bundle: dict) -> bool:
    return bundle.get("background") is not None


def _score_function(bundle: dict):
    features = bundle["features"]
    model = bundle["model"]

    def f(values: np.ndarray) -> np.ndarray:
        return model.predict_proba(pd.DataFrame(values, columns=features))[:, 1]

    return f


def shap_values(bundle: dict, X: pd.DataFrame, max_background: int = 60) -> tuple[np.ndarray, float]:
    """SHAP values (patients x variables, score scale) and the base value (average background score)."""
    import shap

    features = bundle["features"]
    background = bundle["background"][features]
    if len(background) > max_background:
        background = background.sample(max_background, random_state=0)
    masker = shap.maskers.Independent(background.to_numpy(float), max_samples=len(background))
    f = _score_function(bundle)
    algorithm = "exact" if len(features) <= 12 else "permutation"
    explainer = shap.Explainer(f, masker, algorithm=algorithm, feature_names=features)
    result = explainer(X[features].to_numpy(float), silent=True) if algorithm == "exact" else \
        explainer(X[features].to_numpy(float), max_evals=2 * len(features) * 20 + 1, silent=True)
    base = float(np.atleast_1d(result.base_values)[0])
    return np.asarray(result.values, float), base


def _display_value(feature: str, value) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return tr("missing")
    if feature == "clinical_stage":
        return {0: tr("SCD"), 1: tr("MCI"), 2: tr("Dementia")}.get(int(value), f"{value:g}")
    if feature == "sex":
        return "F" if value == 1 else "M"
    if feature in ("anemia", "hypertension", "stroke", "diabetes", "atypical_features"):
        return tr("yes") if value == 1 else tr("no")
    if feature == "apoe4":
        return tr("{n} e4 allele(s)", n=int(value))
    return f"{value:.3g}"


def explanation_table(bundle: dict, X_row: pd.Series, values: np.ndarray) -> pd.DataFrame:
    """One patient: variable, its value, its SHAP contribution, sorted by size."""
    rows = []
    for feature, v in zip(bundle["features"], values):
        rows.append({
            tr("Variable"): column_name(feature),
            tr("Patient value"): _display_value(feature, X_row[feature]),
            tr("Contribution to the score"): round(float(v), 4),
            tr("Effect"): tr("raises the score (towards POSITIVE)") if v > 0.0005 else
            (tr("lowers the score (towards NEGATIVE)") if v < -0.0005 else tr("no effect")),
        })
    table = pd.DataFrame(rows)
    order = np.argsort(-np.abs(values))
    return table.iloc[order].reset_index(drop=True)


def waterfall_png(bundle: dict, X_row: pd.Series, values: np.ndarray, base: float, score: float,
                  thresholds: dict, title: str = "") -> bytes:
    """Waterfall from the average score to this patient's score, with the decision thresholds."""
    order = np.argsort(np.abs(values))                      # smallest at the bottom, largest on top
    features = [bundle["features"][i] for i in order]
    contrib = values[order]
    labels = [f"{column_name(f)} = {_display_value(f, X_row[f])}" for f in features]
    fig, ax = _fig(figsize=(7.4, 0.42 * len(features) + 1.9))
    # drawn top-down from the average score: bar i starts where the bars above it ended
    left = base + np.cumsum(contrib[::-1])[::-1] - contrib
    for i, (lft, c) in enumerate(zip(left, contrib)):
        ax.barh(i, c, left=lft, color=ORANGE if c > 0 else BLUE, height=0.62, zorder=2)
        ax.text(lft + c + (0.004 if c >= 0 else -0.004), i, f"{c:+.3f}", va="center",
                ha="left" if c >= 0 else "right", fontsize=7.5, color=INK, zorder=3)
    ax.set_yticks(range(len(features)), labels, fontsize=8)
    ax.axvline(base, color=INK_2, linewidth=0.9, linestyle="--", zorder=1)
    ax.axvline(score, color=INK, linewidth=1.4, zorder=1)
    for side, color in (("negative", BLUE), ("positive", ORANGE)):
        if thresholds.get(side) is not None:
            ax.axvline(thresholds[side], color=color, linewidth=1, linestyle=":", zorder=1)
    lo = min(base, score, *(left), *(left + contrib), *(t for t in thresholds.values() if t is not None))
    hi = max(base, score, *(left), *(left + contrib), *(t for t in thresholds.values() if t is not None))
    pad = 0.08 * (hi - lo + 0.05)
    ax.set_xlim(max(0, lo - pad), min(1, hi + pad) if hi + pad > lo else 1)
    ax.set_xlabel(tr("Model score (dashed: average patient {b:.2f}; solid: this patient {s:.2f}; dotted: "
                     "NEGATIVE / POSITIVE thresholds)", b=base, s=score), color=INK_2, fontsize=8)
    ax.grid(axis="y", visible=False)
    if title:
        ax.set_title(title, color=INK, fontsize=10, loc="left")
    return _png(fig)


def summary_png(bundle: dict, values: np.ndarray, X: pd.DataFrame) -> bytes:
    """Global picture: mean |SHAP| per variable (bar) and every patient's SHAP value coloured by value."""
    features = bundle["features"]
    mean_abs = np.abs(values).mean(axis=0)
    order = np.argsort(mean_abs)
    fig, (ax1, ax2) = _fig(1, 2, figsize=(10.5, 0.42 * len(features) + 1.8), sharey=True,
                           gridspec_kw={"width_ratios": [1, 1.6]})
    names = [column_name(features[i]) for i in order]
    ax1.barh(range(len(order)), mean_abs[order], color=BLUE, height=0.6)
    ax1.set_yticks(range(len(order)), names, fontsize=8.5)
    ax1.set_xlabel(tr("Mean |SHAP| (average change of the score)"), color=INK_2, fontsize=8.5)
    ax1.grid(axis="y", visible=False)
    rng = np.random.default_rng(0)
    cmap = matplotlib.colormaps["coolwarm"]
    for row, i in enumerate(order):
        col = X[features[i]].to_numpy(float)
        finite = ~np.isnan(col)
        rank = np.full(len(col), 0.5)
        if finite.sum() > 1 and np.nanmax(col) > np.nanmin(col):
            rank[finite] = (col[finite] - np.nanmin(col)) / (np.nanmax(col) - np.nanmin(col))
        colors = [cmap(r) if f else (0.6, 0.6, 0.6, 1) for r, f in zip(rank, finite)]
        ax2.scatter(values[:, i], row + rng.uniform(-0.25, 0.25, len(col)), c=colors, s=9, linewidths=0,
                    zorder=2)
    ax2.axvline(0, color=INK_2, linewidth=0.8)
    ax2.set_xlabel(tr("SHAP value per patient (red = high value of the variable, blue = low, grey = missing)"),
                   color=INK_2, fontsize=8.5)
    ax2.grid(axis="y", visible=False)
    fig.suptitle(tr("What drives the {model} score (SHAP, {n} training patients)",
                    model=bundle["report"].get("model_label", ""), n=len(X)), color=INK, fontsize=10.5,
                 x=0.01, ha="left")
    return _png(fig)


def all_patients_table(bundle: dict, X: pd.DataFrame, ids: list[str], scores: np.ndarray,
                       progress=None) -> pd.DataFrame:
    """SHAP values of every patient (one row per patient, one column per variable), for Excel."""
    out = []
    chunk = 10
    for start in range(0, len(X), chunk):
        part = X.iloc[start:start + chunk]
        values, base = shap_values(bundle, part)
        for j, (_, row) in enumerate(part.iterrows()):
            rec = {tr("patient_id"): ids[start + j], tr("score"): round(float(scores[start + j]), 4),
                   tr("Average score (base)"): round(base, 4)}
            rec.update({f"SHAP {column_name(f)}": round(float(v), 4) for f, v in zip(bundle["features"], values[j])})
            top = np.argsort(-np.abs(values[j]))[:3]
            rec[tr("Main factors")] = "; ".join(
                f"{column_name(bundle['features'][k])} {values[j][k]:+.2f}" for k in top)
            out.append(rec)
        if progress:
            progress(min(1.0, (start + chunk) / len(X)))
    return pd.DataFrame(out)


def _png(fig) -> bytes:
    buffer = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    return buffer.getvalue()


