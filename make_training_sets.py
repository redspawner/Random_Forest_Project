"""Library of SYNTHETIC training sets of different sizes and assumptions (data/synthetic/training_sets/).

    python make_training_sets.py

Every file has the template columns (including the optional factors) and the LP result. They are meant to
test the pipeline, to see how results change with the number of patients, and to check how much the
conclusions depend on the simulation assumptions. They are not real patients. See the README written next to
the files.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from greyzone_rf.config import PROJECT_ROOT, feature_specs, load_config
from greyzone_rf.synthetic import grey_zone_cohort

OUT = PROJECT_ROOT / "data" / "synthetic" / "training_sets"
SIZES = [150, 300, 600, 1200, 2500, 5000]
SCENARIOS = [   # (file stem, version, effects, size, description)
    *[(f"v3_central_n{n}", 3, 1.0, n, "version 3, central literature effect sizes") for n in SIZES],
    ("v3_weak_effects_n600", 3, 0.5, 600, "version 3, extra-factor effects halved (weak-evidence scenario)"),
    ("v3_strong_effects_n600", 3, 1.5, 600, "version 3, extra-factor effects x1.5 (strong-evidence scenario)"),
    ("v2_nonlinear_n600", 2, 1.0, 600, "version 2 (default dataset generator, without the extra factors)"),
    ("v1_additive_n600", 1, 1.0, 600, "version 1, additive log-linear biology (earlier, optimistic)"),
]


def main() -> None:
    cfg = load_config()
    gz = cfg["grey_zone"]
    wanted = ["patient_id", *[s.name for s in feature_specs(cfg) if s.in_template], "lp_result"]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for k, (stem, version, effects, n, text) in enumerate(SCENARIOS):
        df = grey_zone_cohort(n, gz["ptau217_lower"], gz["ptau217_upper"], seed=9000 + k, prefix="LIB",
                              real=True, version=version, effects=effects)
        df = df[[c for c in wanted if c in df.columns]]
        path = OUT / f"{stem}.xlsx"
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Patients", index=False)
            pd.DataFrame({"README": [f"SYNTHETIC DATA ({text}). Not real patients."]}).to_excel(
                writer, sheet_name="About", index=False)
        pos = (df["lp_result"] == "Positive").mean()
        rows.append(f"| `{path.name}` | {n} | {text} | {pos:.0%} |")
        print(path, len(df))
    (OUT / "README.md").write_text("\n".join([
        "# Synthetic training sets (artificial patients - not real data)",
        "",
        "Made by `python make_training_sets.py`. Every file has the template columns (the optional factors are",
        "filled for version 3) and `lp_result`. Use them in the app (Train model) or with",
        "`python train.py <file> --model all --out models/<name>`.",
        "",
        "| File | Grey-zone patients | Assumptions | LP-positive |",
        "|---|---|---|---|",
        *rows,
        "",
        "- **Version 3** = the default version-2 biology plus thyroid status, MRI ratings (MTA, Fazekas; missing",
        "  in about half), MMSE, BMI, sleep apnoea and the triglyceride and hyperfiltration effects.",
        "  See `greyzone_rf/synthetic_v2.py` and docs/EXTRA_FACTORS.md for the sources and the assumed sizes.",
        "- **Sizes 150-5000** show how the certified LP savings grow with the number of patients.",
        "- **Weak / strong scenarios** show how much the conclusions depend on effect sizes that the",
        "  literature does not pin down.",
        "- **Version 1** is the earlier, optimistic generator (mostly additive effects): use it to show how",
        "  much an over-simple simulation flatters the models.",
        "",
    ]), encoding="utf-8")


if __name__ == "__main__":
    main()
