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

from .estimators import model_label, model_params  # noqa: E402
from .i18n import column_name, tr  # noqa: E402

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
    return tr("n/a") if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.1%}"


def _ci(p: dict) -> str:
    if not p["n"]:
        return tr("n/a (no calls)")
    lo, hi = p["ci"]
    return tr("{v:.1%} (95% CI {lo:.1%}-{hi:.1%}; {k}/{n})", v=p["value"], lo=lo, hi=hi, k=p["k"], n=p["n"])


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def plot_scores(scores, y, thresholds, path, title=None, label="Random Forest"):
    title = title or tr("Cross-validated {model} scores", model=label)
    t_pos, t_neg = thresholds["positive"], thresholds["negative"]
    fig, axes = _fig(2, 1, figsize=(8, 5.0), sharex=True)
    bins = np.linspace(0, 1, 41)
    for ax, cls, color, name in ((axes[0], 0, BLUE, tr("LP negative")), (axes[1], 1, ORANGE, tr("LP positive"))):
        lo = t_neg if t_neg is not None else -0.01
        hi = t_pos if t_pos is not None else 1.01
        ax.axvspan(-0.01, lo, color=ZONE_NEG, zorder=0, linewidth=0)
        ax.axvspan(lo, hi, color=ZONE_GREY, zorder=0, linewidth=0)
        ax.axvspan(hi, 1.01, color=ZONE_POS, zorder=0, linewidth=0)
        ax.hist(scores[y == cls], bins=bins, color=color, edgecolor=SURFACE, linewidth=1.2, zorder=2)
        for t in (t_neg, t_pos):
            if t is not None:
                ax.axvline(t, color=INK_2, linewidth=1, zorder=3)
        ax.set_ylabel(tr("{name}\n(patients)", name=name), color=INK_2, fontsize=9)
        ax.set_xlim(-0.01, 1.01)
    labels = []
    if t_neg is not None:
        labels.append((t_neg / 2, tr("NEGATIVE\nscore <= {t:.2f}", t=t_neg)))
    labels.append((((t_neg or 0) + (t_pos or 1)) / 2, tr("INCONCLUSIVE\n-> lumbar puncture")))
    if t_pos is not None:
        labels.append(((t_pos + 1) / 2, tr("POSITIVE\nscore >= {t:.2f}", t=t_pos)))
    for x, text in labels:
        axes[0].text(x, 1.03, text, ha="center", va="bottom", fontsize=8, color=INK,
                     transform=axes[0].get_xaxis_transform())
    axes[1].set_xlabel(tr("{model} score (out-of-fold)", model=label), color=INK_2, fontsize=9)
    fig.suptitle(title, color=INK, fontsize=11, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.99))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_roc(report, path):
    fig, ax = _fig(figsize=(4.8, 4.6))
    ax.plot([0, 1], [0, 1], color=GRID, linewidth=1)
    fpr, tpr = report["roc"]["ptau217"]
    a = report["auc_ptau217_alone"]
    ax.plot(fpr, tpr, color=GRAY, linewidth=2, label=tr("p-tau217 alone  AUC {v:.2f}", v=a["value"]))
    fpr, tpr = report["roc"]["model"]
    a = report["auc_model"]
    ax.plot(fpr, tpr, color=BLUE, linewidth=2, label=tr("{model}  AUC {v:.2f}", model=report.get("model_label",
                                                                                               "Random Forest"),
                                                        v=a["value"]))
    ax.set_xlabel(tr("1 - specificity"), color=INK_2, fontsize=9)
    ax.set_ylabel(tr("Sensitivity"), color=INK_2, fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    ax.legend(frameon=False, fontsize=8, loc="lower right", labelcolor=INK)
    ax.set_title(tr("Discrimination inside the grey zone\n(cross-validated)"), color=INK, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_safety(report, path):
    dec = report["decision_rule"]
    fig, axes = _fig(2, 2, figsize=(8.4, 5.4), sharex="col")
    for col, side, metric, target in ((0, "negative", tr("NPV"), dec["target_npv"]),
                                      (1, "positive", tr("PPV"), dec["target_ppv"])):
        rows = pd.DataFrame(report["threshold_curves"][side])
        chosen = report["thresholds"][side]
        ax = axes[0, col]
        ax.plot(rows["threshold"], rows["predictive_value"], color=BLUE, linewidth=2,
                label=tr("{metric} (estimate)", metric=metric))
        ax.plot(rows["threshold"], rows["lower_bound"], color=ORANGE, linewidth=2,
                label=tr("{metric} one-sided {conf:.0%} lower bound", metric=metric, conf=dec["confidence_level"]))
        ax.axhline(target, color=INK_2, linewidth=1, label=tr("target {t:.0%}", t=target))
        ax.set_ylim(max(0.5, min(0.9, np.nanmin(rows["lower_bound"].replace(0, np.nan)) - 0.02)
                        if rows["lower_bound"].gt(0).any() else 0.5), 1.005)
        ax.set_ylabel(metric, color=INK_2, fontsize=9)
        word = (tr("Rule-out (NEGATIVE if score <= t)") if side == "negative"
                else tr("Rule-in (POSITIVE if score >= t)"))
        ax.set_title(word, color=INK, fontsize=10, loc="left")
        ax.legend(frameon=False, fontsize=7.5, loc="lower left" if side == "positive" else "lower right",
                  labelcolor=INK)
        ax2 = axes[1, col]
        ax2.plot(rows["threshold"], rows["n_called"], color=INK_2, linewidth=2)
        ax2.set_ylabel(tr("patients called"), color=INK_2, fontsize=9)
        ax2.set_xlabel(tr("threshold t on the model score"), color=INK_2, fontsize=9)
        for a in (ax, ax2):
            if chosen is not None:
                a.axvline(chosen, color=INK, linewidth=1)
        if chosen is not None:
            ax2.text(chosen, ax2.get_ylim()[1] * 0.95, tr(" chosen t = {t:.2f}", t=chosen), fontsize=8, color=INK,
                     va="top", ha="left" if side == "positive" else "right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_importance(report, path):
    imp = pd.DataFrame(report["importance"]).sort_values("mean_auc_decrease")
    fig, ax = _fig(figsize=(6.4, 0.32 * len(imp) + 1.2))
    ax.barh([column_name(f) for f in imp["feature"]], imp["mean_auc_decrease"], xerr=imp["sd"], color=BLUE,
            height=0.6, error_kw={"ecolor": INK_2, "elinewidth": 0.8, "capsize": 0})
    ax.axvline(0, color=INK_2, linewidth=0.8)
    ax.set_xlabel(tr("Decrease in cross-validated AUC when the variable is shuffled"), color=INK_2, fontsize=9)
    ax.set_title(tr("Permutation importance"), color=INK, fontsize=10, loc="left")
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
    kind = bundle.get("model_type")
    label = model_label(kind)
    params = ", ".join(f"{k}={v}" for k, v in model_params(bundle["config"], kind or "random_forest").items()
                       if k != "n_jobs")
    rule = (tr("one-sided {conf:.0%} Clopper-Pearson lower bound >= target", conf=dec["confidence_level"])
            if dec["use_confidence_bound"] else tr("point estimate >= target (exploratory mode)"))
    lines = [
        tr("# Training report - grey-zone {model}", model=label),
        "",
        tr("*Trained {created}* - source: `{source}`", created=r["created"], source=r["source_file"] or tr("n/a")),
        "",
        tr("## Cohort"),
        tr("- Rows in file: {rows}; excluded: {no_lp} without LP result, {no_ptau} without p-tau217, {outside} "
           "outside the grey zone [{lo}-{hi} pg/mL].", rows=c["rows_in_file"], no_lp=c["missing_lp_result"],
           no_ptau=c["missing_ptau217"], outside=c["outside_grey_zone"], lo=gz["ptau217_lower"],
           hi=gz["ptau217_upper"]),
        tr("- **Training patients: {n}** ({pos} LP-positive, {neg} LP-negative; prevalence {prev:.1%}).",
           n=c["n_train"], pos=c["n_lp_positive"], neg=c["n_lp_negative"], prev=c["prevalence"]),
        tr("- Model: **{model}** ({params}).", model=label, params=params),
        tr("- Variables used ({k}): {names}.", k=len(r["features"]),
           names=", ".join(column_name(f) for f in r["features"])),
        "",
        tr("## Discrimination (repeated cross-validation)"),
        tr("- {model} AUC: **{auc:.3f}** (95% CI {lo:.3f}-{hi:.3f}); {folds}-fold x {repeats} repeats, "
           "AUC per repeat {mn:.3f}-{mx:.3f}.", model=label, auc=r["auc_model"]["value"], lo=r["auc_model"]["ci"][0],
           hi=r["auc_model"]["ci"][1], folds=r["cv"]["folds"], repeats=r["cv"]["repeats"],
           mn=min(r["cv"]["repeat_aucs"]), mx=max(r["cv"]["repeat_aucs"])),
        tr("- p-tau217 alone (inside the grey zone): AUC {auc:.3f} (95% CI {lo:.3f}-{hi:.3f}).",
           auc=r["auc_ptau217_alone"]["value"], lo=r["auc_ptau217_alone"]["ci"][0],
           hi=r["auc_ptau217_alone"]["ci"][1]),
        "",
        tr("## Decision thresholds used for new patients"),
        tr("Rule: PPV >= {ppv:.0%} for POSITIVE calls and NPV >= {npv:.0%} for NEGATIVE calls, using the {rule}.",
           ppv=dec["target_ppv"], npv=dec["target_npv"], rule=rule),
        "",
        tr("| Call | Threshold on score | Training calls | Correct | Estimate | Lower bound |"),
        "|---|---|---|---|---|---|",
    ]
    for side, word, metric in (("positive", tr("POSITIVE"), tr("PPV")), ("negative", tr("NEGATIVE"), tr("NPV"))):
        d = det[side]
        if d:
            sign = ">=" if side == "positive" else "<="
            lines.append(f"| {word} | {sign} {thr[side]:.2f} | {d['n_called']} | {d['n_correct']} | "
                         f"{metric} {d['predictive_value']:.1%} | {d['lower_bound']:.1%} |")
        else:
            lines.append(f"| {word} | **{tr('none could be certified')}** | - | - | - | - |")
    lines += ["", tr("Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**."), ""]

    n = r["nested"]
    if n:
        m = n["metrics"]
        lines += [
            tr("## Honest estimate for NEW patients (nested cross-validation)"),
            tr("The whole procedure (cross-validation, threshold selection, final model) was repeated in {k} outer "
               "folds and applied to patients it had never seen:", k=n["outer_folds"]),
            "",
            tr("- **Lumbar punctures avoided (patients resolved): {v}**", v=_ci(m["resolved"])),
            tr("- PPV of POSITIVE calls: {v}", v=_ci(m["ppv"])),
            tr("- NPV of NEGATIVE calls: {v}", v=_ci(m["npv"])),
            tr("- Wrong calls: {e} ({fp} false positive, {fn} false negative) out of {n} grey-zone patients",
               e=m["errors"], fp=m["false_positive"], fn=m["false_negative"], n=m["n"]),
            tr("- Remaining INCONCLUSIVE (sent to LP): {v}", v=m["inconclusive"]),
            tr("- Thresholds chosen in each outer fold: {v}", v="; ".join(
                tr("pos {p} / neg {n}", p=_t(t["positive"]), n=_t(t["negative"])) for t in n["fold_thresholds"])),
            "",
        ]
    else:
        lines += [tr("## Honest estimate for new patients"),
                  tr("Nested cross-validation was switched off: the numbers above are optimistic because the "
                     "thresholds were chosen on the same data. Re-train with nested validation for an honest "
                     "estimate."), ""]

    need = r["calls_needed_for_bound"]
    lines += [
        tr("## How many patients does the {conf:.0%} rule need?", conf=dec["confidence_level"]),
        tr("To prove PPV/NPV >= {t:.0%} with {conf:.0%} confidence, a threshold must classify at least: {v}.",
           t=dec["target_ppv"], conf=dec["confidence_level"],
           v=", ".join(tr("{v} patients with {k} error(s)", v=v, k=k) for k, v in list(need.items())[:4])),
        "",
    ]
    if r.get("importance"):
        top = pd.DataFrame(r["importance"]).head(8)
        lines += [tr("## Most informative variables (permutation importance)"), ""]
        lines += [tr("{i}. {name} (AUC drop {v:.3f})", i=i + 1, name=column_name(row.feature),
                     v=row.mean_auc_decrease) for i, row in enumerate(top.itertuples())]
        lines += [""]
    if r["messages"]:
        lines += [tr("## Warnings"), ""] + [f"- {m}" for m in r["messages"]] + [""]
    lines += ["---", tr("Research prototype - not a medical device. Validate on an independent cohort before any "
                        "clinical use.")]
    return "\n".join(lines)


def _t(x):
    return tr("none") if x is None else f"{x:.2f}"


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
    plot_scores(bundle["oof_scores"], bundle["oof_labels"], r["thresholds"], paths["scores"],
                label=model_label(bundle.get("model_type")))
    plot_roc(r, paths["roc"])
    plot_safety(r, paths["safety"])
    if r.get("importance"):
        plot_importance(r, paths["importance"])
    else:
        paths.pop("importance")
    if bundle.get("background") is not None:                 # global SHAP picture (once, at training)
        try:
            from .explain import shap_values, summary_png

            sample = bundle["background"][bundle["features"]].head(60)
            values, _ = shap_values(bundle, sample, max_background=40)
            paths["shap"] = out_dir / "shap_summary.png"
            paths["shap"].write_bytes(summary_png(bundle, values, sample))
        except Exception:                                    # explanations are optional
            pass
    paths["markdown"] = out_dir / "report.md"
    paths["markdown"].write_text(markdown_report(bundle), encoding="utf-8")
    paths["json"] = out_dir / "report.json"
    slim = {k: v for k, v in r.items() if k not in ("roc", "threshold_curves")}
    paths["json"].write_text(json.dumps(slim, indent=2, default=_json_default), encoding="utf-8")
    paths["predictions"] = out_dir / "training_predictions.xlsx"
    bundle["predictions"].to_excel(paths["predictions"], index=False)
    return paths
