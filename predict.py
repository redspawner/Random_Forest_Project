"""Classify new grey-zone patients with a trained model (command-line version of the app).

    python predict.py data/synthetic/synthetic_new_patients.xlsx
    python predict.py new_patients.xlsx --model models/my_model --out results.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from greyzone_rf.config import PROJECT_ROOT
from greyzone_rf.data import DataError, load_patient_file
from greyzone_rf.i18n import tr
from greyzone_rf.model import load_bundle
from greyzone_rf.predict import (DISCLAIMER, annotated_original, predict_prepared, result_headers, results_to_excel,
                                 summarize)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="patients file (.xlsx or .csv)")
    parser.add_argument("--model", default=str(PROJECT_ROOT / "models" / "default"),
                        help="model folder or file (default: the shipped default model)")
    parser.add_argument("--out", default=None, help="results file (default: <input>_results.xlsx)")
    args = parser.parse_args()

    try:
        bundle = load_bundle(args.model)
    except FileNotFoundError:
        print(tr("ERROR: no model found at {path}. Train one first with train.py.", path=args.model), file=sys.stderr)
        return 1
    try:
        prepared = load_patient_file(args.file, bundle["config"])
    except DataError as exc:
        print(tr("ERROR: {exc}", exc=exc), file=sys.stderr)
        return 1

    results = predict_prepared(bundle, prepared)
    out = Path(args.out) if args.out else Path(args.file).with_name(Path(args.file).stem + tr("_results") + ".xlsx")
    out.write_bytes(results_to_excel(results, prepared, bundle))
    annotated = out.with_name(Path(args.file).stem + tr("_with_predictions") + ".xlsx")
    annotated.write_bytes(annotated_original(results, prepared, bundle))

    for message in prepared.messages:
        print(tr("Note: {message}", message=message))
    print()
    print(results[["patient_id", "decision", "rf_score", "ptau217"]].rename(columns=result_headers())
          .to_string(index=False))
    print()
    for decision, count in summarize(results).items():
        print(f"  {decision:<36} {count}")
    print("\n" + tr("Results written to {out}", out=out) + "\n"
          + tr("Original file with predictions added: {path}", path=annotated) + "\n" + DISCLAIMER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
