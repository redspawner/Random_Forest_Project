# Dataset card - default training dataset (generator version 3)

**File:** `data/default_training/synthetic_training_dataset.xlsx`  
**SHA-256:** `10004f048c622077c6668ebec9b2c50afe36571acc9ad57c91ebf0ab6649e0be`  
**Patients:** 600 grey-zone patients (p-tau217 0.14-0.43 pg/mL), 188 LP-positive / 412 LP-negative  
**Generator:** `greyzone_rf/synthetic_v2.py` via `grey_zone_cohort(n=600, seed=2024, real=True, version=3)`

## What this is

**A hybrid dataset: real clinical covariates, real amyloid-prevalence data and simulated plasma biomarkers, with non-linear biology.** No public dataset has plasma p-tau217, an LP result and routine clinical data for the same patients, so it is built as follows:

1. **Real covariates (Cardiovascular Health Study, MRI sub-study, n = 735, public, `data/external/chs_mri_rigr.csv`):** age, sex, BMI, creatinine (-> eGFR, CKD-EPI 2021), LDL, diabetes, stroke, cardiovascular disease and systolic blood pressure from real participants (resampled with small jitter).
2. **Real amyloid data (Knight ADRC CSF study, n = 333, public, `data/external/knight_adrc_csf_ad_data.csv`):**
   - APOE e4 frequencies;
   - CSF amyloid positivity by APOE e4 dose in cognitively normal and impaired participants (positivity = lower component of a two-component mixture of CSF Abeta42). APOE log odds ratios used: normal 0.83 (one e4) / 1.98 (two); impaired 0.76 / 2.19.
3. **Literature-based non-linear biology (simulated):**
   - memory-clinic case mix (SCD / MCI / dementia, older patients more often demented);
   - amyloid prevalence by stage with a flattening age curve and an APOE effect that shrinks with age (Jansen 2015, Ossenkoppele 2015);
   - continuous amyloid load. The LP result is a noisy threshold on it (CSF/PET-type discordance);
   - plasma p-tau217 rising **sigmoidally** with amyloid load and with stage-related tau;
   - a **threshold (hinge) kidney effect**: none above eGFR 70, steeper below 45;
   - anaemia, BMI, hypertension and stroke effects as in version 1.
4. **Version 3 extra routine factors** (separate random stream; docs/EXTRA_FACTORS.md):
   - TSH and known thyroid disease (+10 % p-tau217, assumed);
   - obstructive sleep apnoea (-13 %);
   - a triglyceride effect (-8 % per log unit);
   - eGFR hyperfiltration above 90;
   - MRI MTA and Fazekas ratings (present in about 1/3-1/2 of patients);
   - MMSE.
5. Grey-zone patients were selected with the Stage-1 cut-offs.

**Plasma Abeta42/Abeta40 are not included:** they are not measured in the Coimbra cohort. Only the columns of the template are kept.

Version 1 (`greyzone_rf/synthetic.py`, mostly additive log-linear effects) is kept for reproducibility. It favoured logistic regression and gave optimistic grey-zone results (see docs/MODEL_COMPARISON.md).

## Calibration against published values (simulated population of 30 000 patients)

| Quantity | Published | Simulated | Source |
|---|---|---|---|
| auc_ptau217 | 0.95 | 0.952 | Lumipulse plasma p-tau217 vs CSF, memory clinic (Alzheimer's Res Ther 2025) |
| grey_zone_fraction | 0.15-0.35 | 0.34 | intermediate zone with two cut-offs (several Lumipulse studies) |
| npv_below_lower_cutoff | ~0.95 | 0.939 | two-cut-off design: lower cut-off set for ~95 % NPV |
| ppv_above_upper_cutoff | ~0.95 | 0.98 | two-cut-off design: upper cut-off set for ~95 % PPV |
| ptau217_ratio_anemia | 1.4 | 1.389 | optimal p-tau217 cut-off with anaemia 0.595 vs 0.425 pg/mL (JAMA Neurol 2026) |
| ptau217_ratio_egfr_30_45_vs_60plus | >1 (threshold) | 1.654 | CKD raises p-tau217, little effect above eGFR ~60 (Mielke 2022; Pichet Binette 2023) |
| csf_vs_amyloid_state_discordance | 0.05-0.10 | 0.04 | CSF vs amyloid-PET discordance in memory clinics |

## Sources

- Cardiovascular Health Study MRI data: R package rigr ('mri'), via Rdatasets (CardioDataSets::mriCardioVars_tbl_df). Real covariates.
- Craig-Schapiro R et al. *PLoS ONE* 2011;6:e18850 (Knight ADRC CSF panel); R package modeldata, dataset ad_data, via Rdatasets. Real CSF Abeta42, APOE genotype, clinical status.
- Jansen WJ et al. Prevalence of cerebral amyloid pathology in persons without dementia: a meta-analysis. *JAMA* 2015;313:1924-38 (prevalence by age, APOE and cognitive status).
- Ossenkoppele R et al. Prevalence of amyloid PET positivity in dementia syndromes: a meta-analysis. *JAMA* 2015;313:1939-49.
- Mattsson-Carlgren N et al. *Nat Med* 2023, and Therriault J et al. 2023: plasma p-tau217 rises once amyloid accumulates and further with tau.
- Mielke MM et al. *Nat Med* 2022; Pichet Binette A et al. 2023; Janelidze S et al. 2023: kidney function and plasma p-tau217.
- Plasma p-tau217 cut-offs for amyloid pathology and kidney function, BMI and anaemia. *JAMA Neurology* 2026 (anaemia ratio 1.40).
- Diagnostic performance of plasma p-tau217 in a memory-clinic cohort using Lumipulse. *Alzheimer's Research & Therapy* 2025 (AUC 0.95 vs CSF).

Effect sizes come from abstracts and summaries (the full texts could not be opened from the build environment); check them before citing.

## Assumptions NOT taken from a source

- Stage mix (about 30 / 47 / 23 % SCD / MCI / dementia), dementia amyloid prevalence about 0.62 in APOE e4 non-carriers at 70.
- The shape parameters of the amyloid-load distribution, the p-tau217 sigmoid (midpoint about 32 centiloid-like units) and the kidney hinge slopes; noise levels.
- Missing-data rates per variable.
- Real patients are messier: expect the model to perform somewhat worse on real data.

## Missing values in this file (% of patients)

egfr 6%, creatinine 48%, triglycerides 8%, hemoglobin 5%, apoe4 9%, hypertension 3%, stroke 2%, clinical_stage 2%, bmi 4%, sleep_apnea 6%, tsh 11%, thyroid_disease 3%, mta_score 67%, fazekas 46%, mmse 4%.
