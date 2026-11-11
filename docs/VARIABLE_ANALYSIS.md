# Variable analysis

## Round 2 (current) - forward selection on the hybrid dataset

The dataset combines real CHS clinical covariates with simulated biomarkers. p-tau181, GFAP and
NfL were removed on request. Starting from p-tau217, the variable that increases the
cross-validated AUC the most was added at each step (`forward_selection` in
`greyzone_rf/ablation.py`, raw values in `forward_selection.csv`):

| step | added | n variables | AUC |
|---|---|---|---|
| 0 | p-tau217 | 1 | 0.707 |
| 1 | clinical_stage | 2 | 0.816 |
| 2 | ab42_ab40_ratio | 3 | 0.854 |
| 3 | apoe4 | 4 | 0.869 |
| 4 | stroke | 5 | 0.875 |
| 5 | egfr | 6 | 0.880 |
| 6 | triglycerides | 7 | 0.885 |
| 7 | hypertension | 8 | 0.890 |
| 8 | anemia | 9 | 0.891 |
| 9 | mta_score | 10 | 0.892 |
| 10 | cardiovascular_disease | 11 | 0.896 |
| 11 | sleep_apnea | 12 | 0.896 |
| 12 | diabetes | 13 | 0.896 |
| 13 | weight_loss | 14 | 0.895 |
| 14 | hdl | 15 | 0.896 |

Nested validation, 600 patients, Aβ42/40 missing for half:

| set | n | AUC | certified thresholds | LPs avoided |
|---|---|---|---|---|
| all | 23 | 0.890 | none | 0 % |
| compact 8 | 8 | 0.893 | none | 0 % |
| compact 10 | 10 | 0.895 | none | 0 % |

**Decision:** compact 10 = p-tau217, clinical_stage, ab42_ab40_ratio, ptau217_ab42_ratio, apoe4,
stroke, egfr, triglycerides, hypertension, anemia. With Aβ42/40 always measured (your choice) and
600 patients, the default model has AUC 0.887 but still certifies no threshold. The approximate
cohort sizes needed are in README §6.

---

## Round 1 (earlier, 33 variables) - leave-one-variable-out

Run with `python analyze_variables.py data/default_training/synthetic_training_dataset.xlsx` on the
33-variable configuration (600 grey-zone patients). Each variable was removed in turn and the
model was re-evaluated with the same repeated cross-validation (averaged over 2 random seeds).
Positive deltas mean the model is **better without** the variable.

Full model: AUC 0.9452, 46.4 % resolved. Run-to-run noise (SD over 4 seeds): AUC 0.0020,
resolved 3.7 points. Differences smaller than about twice the noise are not meaningful.

| Variable | Missing % | Delta AUC if removed | Delta % resolved if removed | Verdict | Decision |
|---|---|---|---|---|---|
| ptau217_ab42_ratio | 7.7 | +0.0081 | +7.6 | detrimental - removal improves the model | kept (your choice) |
| ab42 | 7.7 | +0.0045 | +3.1 | detrimental - removal improves the model | REMOVED |
| heart_rate | 3.8 | +0.0015 | -5.2 | no measurable contribution | REMOVED |
| ab40 | 7.7 | +0.0013 | +0.1 | no measurable contribution | REMOVED |
| ldl | 14.5 | +0.0009 | +0.6 | no measurable contribution | kept (your choice) |
| systolic_bp | 3.7 | +0.0006 | +0.6 | no measurable contribution | REMOVED |
| hypertension | 4.7 | +0.0006 | -1.2 | no measurable contribution | kept (your choice) |
| nfl | 8.3 | +0.0005 | -2.8 | no measurable contribution | REMOVED |
| diabetes | 2.2 | +0.0005 | -0.1 | no measurable contribution | kept (your choice) |
| glucose | 8.3 | +0.0004 | -2.4 | no measurable contribution | REMOVED |
| education_years | 3.8 | +0.0003 | +0.1 | no measurable contribution | kept (your choice) |
| diastolic_bp | 3.8 | +0.0002 | +0.0 | no measurable contribution | REMOVED |
| cardiovascular_disease | 3.3 | +0.0002 | +3.5 | no measurable contribution | kept (your choice) |
| stroke | 2.7 | +0.0001 | +0.5 | no measurable contribution | kept (your choice) |
| fazekas | 15.3 | +0.0001 | -5.7 | no measurable contribution | REMOVED |
| bmi | 5.8 | -0.0002 | -1.8 | no measurable contribution | kept |
| weight_loss | 7.5 | -0.0002 | -0.2 | no measurable contribution | kept |
| anemia | 5.2 | -0.0003 | -7.2 | no measurable contribution | kept |
| sleep_apnea | 4.7 | -0.0003 | +3.0 | no measurable contribution | kept |
| sex | 0.0 | -0.0005 | +0.4 | no measurable contribution | kept |
| hdl | 14.0 | -0.0005 | -1.4 | no measurable contribution | kept |
| age | 0.0 | -0.0009 | -1.2 | no measurable contribution | kept |
| triglycerides | 7.7 | -0.0011 | -0.7 | no measurable contribution | kept |
| hemoglobin | 5.2 | -0.0012 | -10.8 | useful - keep | kept |
| mta_score | 14.7 | -0.0029 | -10.7 | useful - keep | kept |
| moca | 5.0 | -0.0033 | -12.8 | useful - keep | kept |
| apoe4 | 31.0 | -0.0038 | -7.2 | no measurable contribution | kept |
| clinical_stage | 1.8 | -0.0074 | +1.1 | useful - keep | kept |
| ab42_ab40_ratio | 7.7 | -0.0078 | +3.5 | useful - keep | kept |
| gfap | 7.8 | -0.0084 | -10.6 | useful - keep | kept |
| egfr | 0.0 | -0.0097 | -12.7 | useful - keep | kept |
| ptau181 | 11.7 | -0.0171 | -14.3 | useful - keep | kept |

p-tau217 is always kept, because it defines the grey zone.

## Decisions (asked one by one)

- **Removed** (`use_as_feature: false` in `config.yaml`; still read and checked, and Aβ42/Aβ40
  still feed the ratios): raw Aβ42, raw Aβ40, NfL, heart rate, systolic BP, diastolic BP,
  fasting glucose, Fazekas.
- **Kept against the synthetic result**, on literature grounds: the p-tau217/Aβ42 ratio, plus
  LDL, hypertension, diabetes, education, cardiovascular disease and stroke.

## Before / after (honest nested cross-validation)

| | 33 variables | 25 variables |
|---|---|---|
| Cross-validated AUC | 0.944 | 0.950 |
| Final model: POSITIVE threshold certified | no | yes (>= 0.82, 66/66 correct) |
| Final model: NEGATIVE threshold | <= 0.25 (215/220) | <= 0.25 (228/234) |
| Nested: lumbar punctures avoided | 38.8 % | 34.2 % |
| Nested: wrong calls | 5 / 600 | 5 / 600 |
| Nested: outer folds certifying POSITIVE | some | none (inner sets of 480 patients) |

The rule-in side sits at the limit of what 480–600 patients can prove, so it switches on and off
with small changes. With more patients, or real data, this must be re-checked.

## Caveat

This is synthetic data. The vital signs, glucose and LDL were *simulated* with no effect on
p-tau217, so the analysis largely confirms how the data were built. It does not reveal biology.
**Re-run `analyze_variables.py` on the real cohort** before final variable decisions.
