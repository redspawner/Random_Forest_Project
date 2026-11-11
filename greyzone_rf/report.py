"""Human-readable training report (Markdown + figures + Excel)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# Validated reference palette (see README "Figures").
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e5e4e0", "#fcfcfb"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8984"
ZONE_NEG, ZONE_GREY, ZONE_POS = "#e3eefb", "#f0efec", "#fbe6dc"

FIGURES = {
    "scores": "score_distribution.png",
    "roc": "roc_curve.png",
    "safety": "safety_curves.png",
    "importance": "feature_importance.png",
}


def _style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=9)
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _fig(nrows=1, ncols=1, **kw):
    fig, axes = plt.subplots(nrows, ncols, facecolor=SURFACE, **kw)
    for ax in np.atleast_1d(axes).ravel():
        _style(ax)
    return fig, axes


def _pct(x) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.1%}"


def _ci(p: dict) -> str:
    if not p["n"]:
        return "n/a (no calls)"
    lo, hi = p["ci"]
    return f"{p['value']:.1%} (95% CI {lo:.1%}-{hi:.1%}; {p['k']}/{p['n']})"


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def plot_scores(scores, y, thresholds, path, title="Cross-validated Random-Forest scores"):
    t_pos, t_neg = thresholds["positive"], thresholds["negative"]
    fig, axes = _fig(2, 1, figsize=(8, 5.0), sharex=True)
    bins = np.linspace(0, 1, 41)
    for ax, cls, color, name in ((axes[0], 0, BLUE, "LP negative"), (axes[1], 1, ORANGE, "LP positive")):
        lo = t_neg if t_neg is not None else -0.01
        hi = t_pos if t_pos is not None else 1.01
        ax.axvspan(-0.01, lo, color=ZONE_NEG, zorder=0, linewidth=0)
        ax.axvspan(lo, hi, color=ZONE_GREY, zorder=0, linewidth=0)
        ax.axvspan(hi, 1.01, color=ZONE_POS, zorder=0, linewidth=0)
        ax.hist(scores[y == cls], bins=bins, color=color, edgecolor=SURFACE, linewidth=1.2, zorder=2)
        for t in (t_neg, t_pos):
            if t is not None:
                ax.axvline(t, color=INK_2, linewidth=1, zorder=3)
        ax.set_ylabel(f"{name}\n(patients)", color=INK_2, fontsize=9)
        ax.set_xlim(-0.01, 1.01)
    labels = []
    if t_neg is not None:
        labels.append((t_neg / 2, f"NEGATIVE\nscore <= {t_neg:.2f}"))
    labels.append((((t_neg or 0) + (t_pos or 1)) / 2, "INCONCLUSIVE\n-> lumbar puncture"))
    if t_pos is not None:
        labels.append(((t_pos + 1) / 2, f"POSITIVE\nscore >= {t_pos:.2f}"))
    for x, text in labels:
        axes[0].text(x, 1.03, text, ha="center", va="bottom", fontsize=8, color=INK,
                     transform=axes[0].get_xaxis_transform())
    axes[1].set_xlabel("Random-Forest score (out-of-fold)", color=INK_2, fontsize=9)
    fig.suptitle(title, color=INK, fontsize=11, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.99))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_roc(report, path):
    fig, ax = _fig(figsize=(4.8, 4.6))
    ax.plot([0, 1], [0, 1], color=GRID, linewidth=1)
    fpr, tpr = report["roc"]["ptau217"]
    a = report["auc_ptau217_alone"]
    ax.plot(fpr, tpr, color=GRAY, linewidth=2, label=f"p-tau217 alone  AUC {a['value']:.2f}")
    fpr, tpr = report["roc"]["model"]
    a = report["auc_model"]
    ax.plot(fpr, tpr, color=BLUE, linewidth=2, label=f"Random Forest  AUC {a['value']:.2f}")
    ax.set_xlabel("1 - specificity", color=INK_2, fontsize=9)
    ax.set_ylabel("Sensitivity", color=INK_2, fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    ax.legend(frameon=False, fontsize=8, loc="lower right", labelcolor=INK)
    ax.set_title("Discrimination inside the grey zone\n(cross-validated)", color=INK, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_safety(report, path):
    dec = report["decision_rule"]
    fig, axes = _fig(2, 2, figsize=(8.4, 5.4), sharex="col")
    for col, side, metric, target in ((0, "negative", "NPV", dec["target_npv"]),
                                      (1, "positive", "PPV", dec["target_ppv"])):
        rows = pd.DataFrame(report["threshold_curves"][side])
        chosen = report["thresholds"][side]
        ax = axes[0, col]
        ax.plot(rows["threshold"], rows["predictive_value"], color=BLUE, linewidth=2, label=f"{metric} (estimate)")
        ax.plot(rows["threshold"], rows["lower_bound"], color=ORANGE, linewidth=2,
                label=f"{metric} one-sided {dec['confidence_level']:.0%} lower bound")
        ax.axhline(target, color=INK_2, linewidth=1, label=f"target {target:.0%}")
        ax.set_ylim(max(0.5, min(0.9, np.nanmin(rows["lower_bound"].replace(0, np.nan)) - 0.02)
                        if rows["lower_bound"].gt(0).any() else 0.5), 1.005)
        ax.set_ylabel(metric, color=INK_2, fontsize=9)
        word = "Rule-out (NEGATIVE if score <= t)" if side == "negative" else "Rule-in (POSITIVE if score >= t)"
        ax.set_title(word, color=INK, fontsize=10, loc="left")
        ax.legend(frameon=False, fontsize=7.5, loc="lower left" if side == "positive" else "lower right",
                  labelcolor=INK)
        ax2 = axes[1, col]
        ax2.plot(rows["threshold"], rows["n_called"], color=INK_2, linewidth=2)
        ax2.set_ylabel("patients called", color=INK_2, fontsize=9)
        ax2.set_xlabel("threshold t on the RF score", color=INK_2, fontsize=9)
        for a in (ax, ax2):
            if chosen is not None:
                a.axvline(chosen, color=INK, linewidth=1)
        if chosen is not None:
            ax2.text(chosen, ax2.get_ylim()[1] * 0.95, f" chosen t = {chosen:.2f}", fontsize=8, color=INK,
                     va="top", ha="left" if side == "positive" else "right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_importance(report, path):
    imp = pd.DataFrame(report["importance"]).sort_values("mean_auc_decrease")
    fig, ax = _fig(figsize=(6.4, 0.32 * len(imp) + 1.2))
    ax.barh(imp["feature"], imp["mean_auc_decrease"], xerr=imp["sd"], color=BLUE, height=0.6,
            error_kw={"ecolor": INK_2, "elinewidth": 0.8, "capsize": 0})
    ax.axvline(0, color=INK_2, linewidth=0.8)
    ax.set_xlabel("Decrease in cross-validated AUC when the variable is shuffled", color=INK_2, fontsize=9)
    ax.set_title("Permutation importance", color=INK, fontsize=10, loc="left")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------
def markdown_report(bundle: dict) -> str:
    r = bundle["report"]
    c = r["cohort"]
    dec = r["decision_rule"]
    thr = r["thresholds"]
    det = r["threshold_details"]
    gz = bundle["config"]["grey_zone"]
    rule = (f"one-sided {dec['confidence_level']:.0%} Clopper-Pearson lower bound >= target"
            if dec["use_confidence_bound"] else "point estimate >= target (exploratory mode)")
    lines = [
        "# Training report - grey-zone Random Forest",
        "",
        f"*Trained {r['created']}* - source: `{r['source_file'] or 'n/a'}`",
        "",
        "## Cohort",
        f"- Rows in file: {c['rows_in_file']}; excluded: {c['missing_lp_result']} without LP result, "
        f"{c['missing_ptau217']} without p-tau217, {c['outside_grey_zone']} outside the grey zone "
        f"[{gz['ptau217_lower']}-{gz['ptau217_upper']} pg/mL].",
        f"- **Training patients: {c['n_train']}** ({c['n_lp_positive']} LP-positive, "
        f"{c['n_lp_negative']} LP-negative; prevalence {c['prevalence']:.1%}).",
        f"- Variables used ({len(r['features'])}): {', '.join(r['features'])}.",
        "",
        "## Discrimination (repeated cross-validation)",
        f"- Random Forest AUC: **{r['auc_model']['value']:.3f}** (95% CI {r['auc_model']['ci'][0]:.3f}-"
        f"{r['auc_model']['ci'][1]:.3f}); {r['cv']['folds']}-fold x {r['cv']['repeats']} repeats, "
        f"AUC per repeat {min(r['cv']['repeat_aucs']):.3f}-{max(r['cv']['repeat_aucs']):.3f}.",
        f"- p-tau217 alone (inside the grey zone): AUC {r['auc_ptau217_alone']['value']:.3f} "
        f"(95% CI {r['auc_ptau217_alone']['ci'][0]:.3f}-{r['auc_ptau217_alone']['ci'][1]:.3f}).",
        "",
        "## Decision thresholds used for new patients",
        f"Rule: PPV >= {dec['target_ppv']:.0%} for POSITIVE calls and NPV >= {dec['target_npv']:.0%} for "
        f"NEGATIVE calls, using the {rule}.",
        "",
        "| Call | Threshold on RF score | Training calls | Correct | Estimate | Lower bound |",
        "|---|---|---|---|---|---|",
    ]
    for side, word, metric in (("positive", "POSITIVE", "PPV"), ("negative", "NEGATIVE", "NPV")):
        d = det[side]
        if d:
            sign = ">=" if side == "positive" else "<="
            lines.append(f"| {word} | {sign} {thr[side]:.2f} | {d['n_called']} | {d['n_correct']} | "
                         f"{metric} {d['predictive_value']:.1%} | {d['lower_bound']:.1%} |")
        else:
            lines.append(f"| {word} | **none could be certified** | - | - | - | - |")
    lines += ["", "Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.", ""]

    n = r["nested"]
    if n:
        m = n["metrics"]
        lines += [
            "## Honest estimate for NEW patients (nested cross-validation)",
            "The whole procedure (cross-validation, threshold selection, final model) was repeated in "
            f"{n['outer_folds']} outer folds and applied to patients it had never seen:",
            "",
            f"- **Lumbar punctures avoided (patients resolved): {_ci(m['resolved'])}**",
            f"- PPV of POSITIVE calls: {_ci(m['ppv'])}",
            f"- NPV of NEGATIVE calls: {_ci(m['npv'])}",
            f"- Wrong calls: {m['errors']} ({m['false_positive']} false positive, {m['false_negative']} "
            f"false negative) out of {m['n']} grey-zone patients",
            f"- Remaining INCONCLUSIVE (sent to LP): {m['inconclusive']}",
            "- Thresholds chosen in each outer fold: " + "; ".join(
                f"pos {_t(t['positive'])} / neg {_t(t['negative'])}" for t in n["fold_thresholds"]),
            "",
        ]
    else:
        lines += ["## Honest estimate for new patients",
                  "Nested cross-validation was switched off: the numbers above are optimistic because the "
                  "thresholds were chosen on the same data. Re-train with nested validation for an honest "
                  "estimate.", ""]

    need = r["calls_needed_for_bound"]
    lines += [
        "## How many patients does the 95% rule need?",
        f"To prove PPV/NPV >= {dec['target_ppv']:.0%} with {dec['confidence_level']:.0%} confidence, a "
        "threshold must classify at least: " + ", ".join(f"{v} patients with {k} error(s)"
                                                         for k, v in list(need.items())[:4]) + ".",
        "",
    ]
    if r.get("importance"):
        top = pd.DataFrame(r["importance"]).head(8)
        lines += ["## Most informative variables (permutation importance)", ""]
        lines += [f"{i + 1}. {row.feature} (AUC drop {row.mean_auc_decrease:.3f})"
                  for i, row in enumerate(top.itertuples())]
        lines += [""]
    if r["messages"]:
        lines += ["## Warnings", ""] + [f"- {m}" for m in r["messages"]] + [""]
    lines += ["---", "Research prototype - not a medical device. Validate on an independent cohort before any "
              "clinical use."]
    return "\n".join(lines)


def _t(x):
    return "none" if x is None else f"{x:.2f}"


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if math.isnan(obj) else float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, tuple):
        return list(obj)
    return str(obj)


def write_report(bundle: dict, out_dir: str | Path) -> dict[str, Path]:
    """Write report.md, report.json, figures and the OOF predictions file."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    r = bundle["report"]
    paths = {k: out_dir / v for k, v in FIGURES.items()}
    plot_scores(bundle["oof_scores"], bundle["oof_labels"], r["thresholds"], paths["scores"])
    plot_roc(r, paths["roc"])
    plot_safety(r, paths["safety"])
    if r.get("importance"):
        plot_importance(r, paths["importance"])
    else:
        paths.pop("importance")
    paths["markdown"] = out_dir / "report.md"
    paths["markdown"].write_text(markdown_report(bundle), encoding="utf-8")
    paths["json"] = out_dir / "report.json"
    slim = {k: v for k, v in r.items() if k not in ("roc", "threshold_curves")}
    paths["json"].write_text(json.dumps(slim, indent=2, default=_json_default), encoding="utf-8")
    paths["predictions"] = out_dir / "training_predictions.xlsx"
    bundle["predictions"].to_excel(paths["predictions"], index=False)
    return paths
