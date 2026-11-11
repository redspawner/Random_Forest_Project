"""Train the grey-zone Random Forest from an Excel/CSV file with LP results.

    python train.py --default                      # re-train the shipped default model
    python train.py data/default_training/synthetic_training_dataset.xlsx --out models/my_model
    python train.py my_cohort.xlsx --out models/rf_2026_11 --no-nested

The model and its report are written to the output folder (default: models/rf_model):
    model.joblib, report.md, report.json, *.png figures, training_predictions.xlsx
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from greyzone_rf.config import PROJECT_ROOT, load_config
from greyzone_rf.data import DataError, load_patient_file
from greyzone_rf.model import TrainingError, save_bundle, train_model
from greyzone_rf.report import markdown_report, write_report

DEFAULT_OUT = PROJECT_ROOT / "models" / "rf_model"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="?", help="training file (.xlsx or .csv) with the lp_result column")
    parser.add_argument("--default", action="store_true",
                        help="(re)train the shipped default model from the dataset in config.yaml "
                             "(default_model.training_file) into default_model.model_dir")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output folder (default models/rf_model)")
    parser.add_argument("--config", default=None, help="alternative config.yaml")
    nested = parser.add_mutually_exclusive_group()
    nested.add_argument("--nested", dest="nested", action="store_true", default=None,
                        help="force nested cross-validation (honest estimate, slower)")
    nested.add_argument("--no-nested", dest="nested", action="store_false", help="skip nested validation")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.default:
        from greyzone_rf.default_model import train_default

        print("Training the DEFAULT model from", cfg["default_model"]["training_file"], "...")
        bundle = train_default(cfg, nested=args.nested)
        print(markdown_report(bundle))
        print(f"\nDefault model saved to {cfg['default_model']['model_dir']} (with manifest.json).")
        return 0
    if not args.file:
        parser.error("give a training file, or use --default")
    try:
        prepared = load_patient_file(args.file, cfg, require_label=True)
    except DataError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    start = time.time()
    last = [-1]

    def progress(fraction: float, message: str) -> None:
        pct = int(fraction * 100)
        if pct // 10 != last[0]:
            last[0] = pct // 10
            print(f"  [{pct:3d}%] {message}", flush=True)

    print(f"Training on {args.file} ...")
    try:
        bundle = train_model(prepared, cfg, nested=args.nested, progress=progress, source_name=Path(args.file).name)
    except TrainingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    model_path = save_bundle(bundle, args.out)
    write_report(bundle, args.out)
    print()
    print(markdown_report(bundle))
    print()
    print(f"Finished in {time.time() - start:.0f} s. Model saved to {model_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
