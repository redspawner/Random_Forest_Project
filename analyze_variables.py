"""Leave-one-variable-out analysis: which variables help, which add only noise.

    python analyze_variables.py data/default_training/synthetic_training_dataset.xlsx
    python analyze_variables.py my_cohort.xlsx --out variable_analysis.xlsx

Uses config.yaml. Takes a few minutes (one cross-validation per variable).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from greyzone_rf.ablation import variable_contributions, verdict
from greyzone_rf.config import load_config
from greyzone_rf.data import load_patient_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="training file with lp_result")
    parser.add_argument("--out", default=None, help="Excel output (default: <file>_variable_analysis.xlsx)")
    parser.add_argument("--repeats", type=int, default=3, help="cross-validation repeats per run (default 3)")
    args = parser.parse_args()

    cfg = load_config()
    prepared = load_patient_file(args.file, cfg, require_label=True)
    table = variable_contributions(prepared, cfg, repeats=args.repeats,
                                   progress=lambda f, m: print(f"  [{f:4.0%}] {m}", flush=True))
    a = table.attrs
    table["verdict"] = [verdict(r, a["noise_auc"], a["noise_resolved"]) for _, r in table.iterrows()]
    print(f"\nFull model: AUC {a['baseline_auc']:.4f}, resolved {a['baseline_resolved']:.1f}%, "
          f"{a['baseline_errors']:.1f} errors.  Run-to-run noise (SD): AUC {a['noise_auc']:.4f}, "
          f"resolved {a['noise_resolved']:.1f} points.\n")
    print(table.to_string(index=False))
    out = Path(args.out) if args.out else Path(args.file).with_name(Path(args.file).stem + "_variable_analysis.xlsx")
    table.to_excel(out, index=False)
    print(f"\nWritten to {out}")


if __name__ == "__main__":
    main()
