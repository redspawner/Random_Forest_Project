"""Benchmark model types/settings with the full procedure (used for docs/MODEL_COMPARISON.md).

    python tools/benchmark_models.py                       # every model type with its config.yaml settings
    python tools/benchmark_models.py --external 6000       # + test on 6,000 independent synthetic patients

For every model: repeated cross-validation, thresholds with the PPV/NPV rule, nested validation
(honest estimate) and, optionally, the true PPV/NPV on a large independent synthetic cohort drawn
from the same generator as the default dataset (version 3, other random seed).
"""

from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from greyzone_rf.config import load_config  # noqa: E402
from greyzone_rf.data import load_patient_file, prepare_table  # noqa: E402
from greyzone_rf.default_model import shipped_types  # noqa: E402
from greyzone_rf.estimators import model_label  # noqa: E402
from greyzone_rf.model import train_model  # noqa: E402
from greyzone_rf.predict import NEGATIVE_TXT, POSITIVE_TXT, predict_prepared  # noqa: E402
from greyzone_rf.stats import cp_interval  # noqa: E402


def main() -> None:
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", nargs="*", default=None, help="model types (default: config.yaml model_types)")
    parser.add_argument("--external", type=int, default=0, help="size of the independent synthetic test cohort")
    args = parser.parse_args()
    cfg = load_config()
    prep = load_patient_file(cfg["default_model"]["training_file"], cfg, require_label=True)
    ext = None
    if args.external:
        from greyzone_rf.synthetic import grey_zone_cohort

        cohort = grey_zone_cohort(args.external, seed=777, prefix="EXT", real=True, version=3)
        ext = (cohort["lp_result"].map({"Positive": 1, "Negative": 0}).to_numpy(),
               prepare_table(cohort.drop(columns=["lp_result"]), cfg))
    print("| Model | AUC (CV) | POS >= | NEG <= | LPs avoided (nested) | Wrong (nested) | PPV / NPV (nested) |"
          + (" AUC ext. | LPs avoided (ext.) | PPV ext. (95% CI) | NPV ext. (95% CI) | Wrong per 1000 (ext.) |"
             " Net LPs avoided /100 at pt 0.10 (ext.) |" if ext else ""))
    print("|---" * (7 + (6 if ext else 0)) + "|")
    for kind in args.models or shipped_types(cfg):
        t = time.time()
        b = train_model(prep, cfg, nested=True, model_type_name=kind)
        r, m = b["report"], b["report"]["nested"]["metrics"]
        line = (f"| {model_label(kind)} | {r['auc_model']['value']:.3f} | {b['thresholds']['positive']} | "
                f"{b['thresholds']['negative']} | {m['resolved']['value']:.1%} | {m['errors']} | "
                f"{m['ppv']['value']:.1%} / {m['npv']['value']:.1%} |")
        if ext:
            y, data = ext
            res = predict_prepared(b, data)
            d, s = res["decision"].to_numpy(), res["score"].astype(float).to_numpy()
            pos, neg = d == POSITIVE_TXT, d == NEGATIVE_TXT
            tp, fp = int((pos & (y == 1)).sum()), int((pos & (y == 0)).sum())
            tn, fn = int((neg & (y == 0)).sum()), int((neg & (y == 1)).sum())
            pci, nci = cp_interval(tp, tp + fp), cp_interval(tn, tn + fn)
            ok = ~np.isnan(s)
            yo, so = y[ok], s[ok]
            nb = np.mean((so >= 0.10) & (yo == 1)) - np.mean((so >= 0.10) & (yo == 0)) / 9
            nb_all = yo.mean() - (1 - yo.mean()) / 9
            net_lp = (nb - nb_all) * 9 * 100
            ppv = f"{tp / (tp + fp):.1%} ({pci[0]:.1%}-{pci[1]:.1%})" if tp + fp else "no calls"
            npv = f"{tn / (tn + fn):.1%} ({nci[0]:.1%}-{nci[1]:.1%})" if tn + fn else "no calls"
            line += (f" {roc_auc_score(yo, so):.3f} | {(pos | neg).mean():.1%} | {ppv} | {npv} | "
                     f"{1000 * (fp + fn) / len(y):.0f} | {net_lp:.1f} |  <!-- {time.time() - t:.0f} s -->")
        print(line, flush=True)


if __name__ == "__main__":
    main()
