# Extra routine factors, SMOTE and other improvements (version-3 synthetic data)

All results come from **synthetic patients** (generator version 3 = the default version-2 biology plus the
factors below). A factor can only help here as much as the assumed effect size allows, so treat the tables as
"what to expect *if* the literature effect sizes are right". Re-run them on the Coimbra data. Reproduce:
the scripts in this document's "How to reproduce" section.

## The factors (screenshot from the Gemini research + routine memory-clinic data)

| Factor | Effect on plasma p-tau217 in the simulation | Evidence | Routinely available? |
|---|---|---|---|
| Kidney function (eGFR) | rises below eGFR ~70, steeply below 45 (hinge); **slightly lower above 90 (hyperfiltration)** | strong for CKD (Mielke 2022, Pichet Binette 2023, JAMA Neurol 2026); hyperfiltration weak | yes (creatinine) |
| BMI | about 2 % lower per kg/m² (haemodilution); underweight raises | moderate (JAMA Neurol 2026, Martino-Adami 2026) | yes (weight/height) |
| Anaemia | +25 % (cut-off ratio about 1.4) | moderate (JAMA Neurol 2026) | yes (blood count) |
| Age | +0.7 % per year independently of amyloid | moderate | yes |
| Stroke / cardiovascular events (MI, heart failure) | +10 % | moderate (Mielke 2022) | yes |
| **Thyroid disease** (hypo/hyper, levothyroxine) and **TSH** | +10 % with thyroid disease (assumed) | **weak / inconsistent** | yes: TSH is part of the standard dementia blood screen |
| Obstructive sleep apnoea | −13 % (more false negatives) | limited (Shir 2026) | often known |
| Triglycerides | modest inverse association (−8 % per log unit) | weak | yes (lipid panel) |
| **MRI MTA** (Scheltens 0–4) | not a p-tau217 confounder: higher with age, clinical stage and tau in amyloid-positive patients | strong for AD-type neurodegeneration (Wahlund 2017, Persson 2017) | **sometimes** (rating present in about 1/3–1/2) |
| MRI Fazekas (0–3) | vascular burden (age, hypertension, diabetes, stroke); no direct amyloid effect | strong for vascular disease | sometimes |
| **MMSE** (0–30) | by stage; about 1 point lower in amyloid-positive patients with tau | moderate (ADNI-type differences) | **yes, at every memory-clinic visit** |

The thyroid, sleep-apnoea, triglyceride and hyperfiltration effect sizes are **assumptions**: their direction
comes from the literature summary, their size does not. The library in `data/synthetic/training_sets/` has a
weak-evidence (×0.5) and a strong-evidence (×1.5) version so you can see how much this matters.

## Do the extra factors help? (600 grey-zone patients, no Aβ, strict 90 % / 95 % rule)

AUC on 6,000 independent synthetic patients (version 3); in brackets the net lumbar punctures avoided per 100 at
pt = 0.10 (decision curve, see MODEL_COMPARISON.md):

| Variables | Logistic Regression | Spline LR | XGBoost | Random Forest |
|---|---|---|---|---|
| base 8 (current routine set) | 0.798 (+0.2) | 0.793 (−1.4) | 0.783 (+0.9) | 0.776 (−1.2) |
| + BMI + sleep apnoea | **0.806** (+2.0) | 0.796 (0.0) | 0.789 (+0.2) | 0.783 (−1.2) |
| + TSH + thyroid disease | 0.797 (+0.4) | 0.791 (−1.5) | 0.780 (+0.4) | 0.775 (−1.1) |
| + MMSE | 0.798 (+0.6) | 0.792 (−1.3) | 0.783 (+0.7) | 0.775 (−2.4) |
| + MRI (MTA, Fazekas) | 0.796 (+0.6) | 0.790 (−0.3) | 0.781 (+0.4) | 0.774 (−4.2) |
| + all of them | 0.804 (+1.8) | 0.791 (−1.2) | 0.787 (+0.9) | 0.780 (−0.6) |

**No combination lets any model prove PPV or NPV ≥ 90 % with 600 patients.**

- **BMI and sleep apnoea** give the only consistent gain (about +0.006–0.008 AUC and a better Brier score).
  Both are well-documented p-tau217 confounders and cheap to record, so they are now switched on
  (`use_as_feature: true`).
- **Thyroid, MMSE and the MRI ratings add nothing measurable here.**
  - The thyroid effect is small and only assumed.
  - MMSE mostly repeats the clinical stage.
  - MTA and Fazekas are missing in half the patients, and inside the grey zone they differ little between
    LP-positive and LP-negative patients (MTA about +0.13 points, MMSE about −0.4 points).
  - They remain in the template as optional columns (`use_as_feature: false`). Switch them on and compare on the
    real data: real MRI ratings may carry more information than this simulation assumes.

## SMOTE and other resampling (`config.yaml → resampling`, training-only)

| Method | n = 600 LR | n = 600 XGBoost | n = 200 LR | n = 200 XGBoost |
|---|---|---|---|---|
| none | AUC 0.804, Brier 0.145 | 0.787, 0.148 | 0.758, 0.172 | 0.759, 0.161 |
| SMOTE | 0.803, **0.167** | 0.790, **0.166** | 0.758, **0.195** | 0.773, **0.177** |
| random oversampling | 0.804, 0.166 | 0.793, 0.165 | 0.753, 0.199 | 0.746, 0.184 |
| noise jitter | 0.804, 0.145 | 0.789, 0.147 | 0.756, 0.174 | 0.772, 0.155 |

**It does not help, so it is not applied** (`method: none`):
- ranking (AUC) is unchanged within ±0.015;
- SMOTE and oversampling clearly damage calibration (Brier +0.02–0.03), because the model now believes about
  50 % of grey-zone patients are LP-positive instead of about 30 %;
- no method produced a single certified POSITIVE/NEGATIVE call.

This is expected: resampling creates no new information, and PPV/NPV depend directly on prevalence. The
option stays in the code (applied only to training folds) so that it can be re-checked on real data.

## Monotone constraints for XGBoost

The score is allowed only to rise with p-tau217, APOE ε4, clinical stage, MTA and eGFR, and only to fall with
anaemia and MMSE. eGFR and anaemia point "the wrong way" on purpose: at equal p-tau217, poor kidney function or
anaemia means the p-tau217 is inflated for non-amyloid reasons. **Accuracy was identical (AUC 0.787 vs 0.787
at n = 600, 0.760 vs 0.759 at n = 200).** The constraints are now on, because they guarantee medically
plausible behaviour for unusual patients at no cost.

## More synthetic training data

`python make_training_sets.py` writes `data/synthetic/training_sets/`:
- version 3 at **150, 300, 600, 1,200, 2,500 and 5,000** grey-zone patients;
- weak- and strong-effect scenarios;
- the version-2 and version-1 generators for comparison.

The sources are different studies for each part:
- real CHS covariates;
- real Knight ADRC CSF data;
- Jansen 2015 and Ossenkoppele 2015 (amyloid prevalence);
- Mattsson-Carlgren 2023 (p-tau217 vs amyloid);
- Mielke 2022 and Pichet Binette 2023 (kidney, cardiovascular);
- JAMA Neurol 2026 (anaemia, BMI);
- Shir 2026 (sleep apnoea);
- Wahlund 2017 and Persson 2017 (MTA).

See `data/default_training/DATASET_CARD.md`.

### What the training-set sizes show (10 variables, strict 90 % / 95 % rule)

Tested on 6,000 independent version-3 patients:

| Grey-zone training patients | Model | AUC (new patients) | Certified POSITIVE / NEGATIVE | LPs avoided | True PPV | True NPV |
|---|---|---|---|---|---|---|
| 150 | LR / XGBoost | 0.776 / 0.778 | none | 0 % | – | – |
| 300 | LR / XGBoost | 0.792 / 0.793 | none | 0 % | – | – |
| 600 | LR / XGBoost | 0.804 / 0.800 | none | 0 % | – | – |
| 1,200 | LR / XGBoost | 0.810 / 0.806 | none | 0 % | – | – |
| 2,500 | LR | 0.813 | ≥ 0.81 / none | 4.9 % | 93.5 % | – |
| 2,500 | XGBoost | 0.807 | ≥ 0.73 / none | 7.6 % | 90.1 % | – |
| 5,000 | LR | 0.816 | ≥ 0.87 / ≤ 0.10 | **30.8 %** | 96.4 % | 90.9 % |
| 5,000 | XGBoost | 0.811 | ≥ 0.81 / ≤ 0.12 | 16.2 % | 94.4 % | 90.8 % |

With realistic biology and routine variables only, the strict rule starts to pay off at about 2,500 grey-zone
patients and becomes useful at about 5,000. When it does certify a zone, the true PPV and NPV on new patients
stay above 90 %, so the rule does what it promises.

## How to reproduce

```
python make_training_sets.py
python tools/benchmark_models.py --external 6000
```

The variable and resampling experiments are reproduced by training on
`data/synthetic/training_sets/v3_central_n600.xlsx` with the `use_as_feature` / `resampling` settings of
`config.yaml` changed.

## Less missing data?

Settings: `greyzone_rf.synthetic.MISSING_SCALE` (1 = realistic, 0 = complete) and
`greyzone_rf.synthetic_v2.MRI_AVAILABILITY` (0.55 = realistic).

**Simulation** (version 3, 1,500 training patients, LR, 6,000 new patients):
- AUC 0.811 with realistic missingness (11 % of values blank);
- 0.811 with MRI for everyone;
- 0.812 with half the missingness;
- 0.814 with complete data;
- the certified LP savings stay at 0–5 %.

The variables that are often missing carry little extra information in this simulation.

**User-supplied 2,000-patient file** (LR trained on the separate 1,500 file):
- MTA present: AUC 0.889 (n = 1,218); MTA missing: 0.843 (n = 782);
- 0–1 model variables missing: 0.887; 2 or more missing: 0.846;
- LPs avoided are similar in all groups (31–33 %), because the certified thresholds do not change.

Conclusion: collect the informative variables consistently, above all the MRI MTA rating and APOE. Blanks lower
accuracy rather than safety: patients with more than 50 % missing stay INCONCLUSIVE automatically.
