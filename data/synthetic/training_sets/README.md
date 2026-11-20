# Synthetic training sets (artificial patients - not real data)

Made by `python make_training_sets.py`. Every file has the template columns (the optional factors are
filled for version 3) and `lp_result`. Use them in the app (Train model) or with
`python train.py <file> --model all --out models/<name>`.

| File | Grey-zone patients | Assumptions | LP-positive |
|---|---|---|---|
| `v3_central_n150.xlsx` | 150 | version 3, central literature effect sizes | 31% |
| `v3_central_n300.xlsx` | 300 | version 3, central literature effect sizes | 26% |
| `v3_central_n600.xlsx` | 600 | version 3, central literature effect sizes | 33% |
| `v3_central_n1200.xlsx` | 1200 | version 3, central literature effect sizes | 28% |
| `v3_central_n2500.xlsx` | 2500 | version 3, central literature effect sizes | 30% |
| `v3_central_n5000.xlsx` | 5000 | version 3, central literature effect sizes | 30% |
| `v3_weak_effects_n600.xlsx` | 600 | version 3, extra-factor effects halved (weak-evidence scenario) | 30% |
| `v3_strong_effects_n600.xlsx` | 600 | version 3, extra-factor effects x1.5 (strong-evidence scenario) | 29% |
| `v2_nonlinear_n600.xlsx` | 600 | version 2 (default dataset generator, without the extra factors) | 29% |
| `v1_additive_n600.xlsx` | 600 | version 1, additive log-linear biology (earlier, optimistic) | 32% |
| `v3_separation1.25_n600.xlsx` | 600 | version 3, OPTIMISTIC separation x1.25 (moderate) | 26% |
| `v3_separation1.25_n1000.xlsx` | 1000 | version 3, OPTIMISTIC separation x1.25 (moderate) | 29% |
| `v3_separation1.25_n1500.xlsx` | 1500 | version 3, OPTIMISTIC separation x1.25 (moderate) | 23% |
| `v3_separation1.25_n2000.xlsx` | 2000 | version 3, OPTIMISTIC separation x1.25 (moderate) | 26% |
| `v3_separation1.5_n600.xlsx` | 600 | version 3, OPTIMISTIC separation x1.5 (high) | 24% |
| `v3_separation1.5_n1000.xlsx` | 1000 | version 3, OPTIMISTIC separation x1.5 (high) | 23% |
| `v3_separation1.5_n1500.xlsx` | 1500 | version 3, OPTIMISTIC separation x1.5 (high) | 24% |
| `v3_separation1.5_n2000.xlsx` | 2000 | version 3, OPTIMISTIC separation x1.5 (high) | 24% |
| `v3_separation2.0_n600.xlsx` | 600 | version 3, OPTIMISTIC separation x2.0 (very high) | 21% |
| `v3_separation2.0_n1000.xlsx` | 1000 | version 3, OPTIMISTIC separation x2.0 (very high) | 23% |
| `v3_separation2.0_n1500.xlsx` | 1500 | version 3, OPTIMISTIC separation x2.0 (very high) | 22% |
| `v3_separation2.0_n2000.xlsx` | 2000 | version 3, OPTIMISTIC separation x2.0 (very high) | 21% |

- **Version 3** = the default version-2 biology plus thyroid status, MRI ratings (MTA, Fazekas; missing
  in about half), MMSE, BMI, sleep apnoea and the triglyceride and hyperfiltration effects.
  See `greyzone_rf/synthetic_v2.py` and docs/EXTRA_FACTORS.md for the sources and the assumed sizes.
- **Sizes 150-5000** show how the certified LP savings grow with the number of patients.
- **Weak / strong scenarios** show how much the conclusions depend on effect sizes that the
  literature does not pin down.
- **Version 1** is the earlier, optimistic generator (mostly additive effects): use it to show how
  much an over-simple simulation flatters the models.
- **`v3_separation*`** files are deliberately OPTIMISTIC: p-tau217 and CSF measurement noise divided by
  the separation factor, and tau / MRI / MMSE effects multiplied by it. LP-positive and LP-negative patients
  are further apart, so the 90 % / 95 % rule can certify thresholds (Logistic Regression, tested on new
  patients from the same scenario):
  - x1.25: about 7 % of LPs avoided with 600 patients, about 68 % with 2000;
  - x1.5: about 73 % with 600, 83 % with 2000;
  - x2.0: about 88-91 %;
  - true PPV and NPV about 92-97 %.
  Use them for demonstrations and teaching, never as evidence about real patients.
