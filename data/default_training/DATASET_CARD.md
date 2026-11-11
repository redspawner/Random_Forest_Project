# Dataset card - default training dataset

**File:** `data/default_training/synthetic_training_dataset.xlsx`  
**SHA-256:** `90607fe988031a7054501d7a83ceb260b4b6ce756de9b378360d9cba83441f98`  
**Patients:** 600 grey-zone patients (p-tau217 0.14-0.43 pg/mL), 218 LP-positive / 382 LP-negative  
**Generator:** `greyzone_rf/synthetic.py`, `grey_zone_cohort(n=600, seed=2024, real=True)`

## What this is

**A hybrid dataset: real clinical covariates + simulated biomarkers and diagnosis.** No public dataset contains plasma p-tau217 together with an LP result and routine clinical data at individual level, so:

1. **Real data (Cardiovascular Health Study, MRI sub-study, n = 735, aged 65+; public file `data/external/chs_mri_rigr.csv`):** age, sex, BMI, serum creatinine (-> eGFR, CKD-EPI 2021), LDL, diabetes, stroke, coronary disease/heart failure and systolic blood pressure are taken from real participants (resampled with small jitter), so their joint distribution and correlations are real.
2. **Real frequencies (Knight ADRC CSF study, n = 333):** APOE e4 allele counts.
3. **Simulated, conditional on the above:** amyloid status (the LP label), plasma p-tau217, Abeta42/40, haemoglobin, triglycerides, HDL, known hypertension (from the real blood pressure), sleep apnoea, weight loss, education, MoCA, clinical stage and MTA, with parameters tuned so the population reproduces the published values below. Grey-zone patients were then selected with the Stage-1 cut-offs.

Only the columns of the compact model are kept (see config.yaml). Missing values follow the expected future cohort: Abeta42/40 measured with p-tau217 (missing ~3%), APOE known in ~90%. p-tau181, GFAP and NfL are not included (not measured in that cohort).

## Calibration against published values (simulated population of 30 000 patients)

| Quantity | Published | Simulated | Source |
|---|---|---|---|
| auc_ptau217 | 0.95 | 0.951 | Lumipulse plasma p-tau217 vs CSF, memory clinic (Alzheimer's Res Ther 2025) |
| auc_ptau217_ab42 | 0.97 | 0.959 | p-tau217/Abeta42 ratio, same study |
| auc_ab42_ab40 | 0.72 | 0.79 | plasma Abeta42/40, same study (0.85 vs CSF in a Japanese memory-clinic study) |
| grey_zone_fraction | 0.3 | 0.325 | intermediate zone 15-30% with two cut-offs (several Lumipulse studies) |
| ptau217_increase_per_10_egfr | 0.12 | 0.12 | +12% Lumipulse p-tau217 per 10 mL/min lower eGFR (Mayo Clinic data) |
| ptau217_ratio_anemia | 1.4 | 1.366 | optimal p-tau217 cut-off with anaemia 0.595 vs 0.425 pg/mL (JAMA Neurol 2026, n=2571) |

## Sources

1. Diagnostic performance of plasma p-tau217 in a memory clinic cohort using the Lumipulse automated platform. *Alzheimer's Research & Therapy* 2025. https://doi.org/10.1186/s13195-025-01719-5 (p-tau217 AUC 0.95 vs CSF; p-tau217/Abeta42 AUC 0.97; Abeta42/40 AUC 0.72).
0a. Cardiovascular Health Study MRI data: R package rigr ('mri'), mirrored as CardioDataSets::mriCardioVars_tbl_df by Rdatasets, https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/CardioDataSets/mriCardioVars_tbl_df.csv (real covariates).
0b. Craig-Schapiro R et al. Multiplexed immunoassay panel identifies novel CSF biomarkers for Alzheimer's disease diagnosis and prognosis. *PLoS ONE* 2011;6:e18850 - R package modeldata ('ad_data') (APOE genotype frequencies).
2. Prospective study on clinical utility of plasma p-Tau217 and other biomarkers in Japanese memory clinics using the LUMIPULSE platform. *Alzheimer's Research & Therapy* 2026. https://doi.org/10.1186/s13195-026-01997-7 (plasma Abeta42/40 AUC 0.85 vs CSF; intermediate zone 15%).
3. Effect of kidney function on plasma pTau217 concentrations using different pTau217 assays (Mayo Clinic). https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11715048/ (+12% Lumipulse p-tau217 per 10-unit lower eGFR).
4. Profiling of plasma biomarkers in the context of memory assessment in a tertiary memory clinic. *Translational Psychiatry* 2023. https://www.nature.com/articles/s41398-023-02558-4 (age effects on NfL/GFAP; used in earlier versions, these markers are no longer part of the dataset).
5. Plasma phospho-tau217 for Alzheimer's disease diagnosis in primary and secondary care using a fully automated platform. *Nature Medicine* 2025. https://doi.org/10.1038/s41591-025-03622-w (two-cut-off approach; Lumipulse cut-offs 0.22 / 0.34 pg/mL).
6. Plasma p-tau217 for Alzheimer's disease diagnosis: a memory clinic implementation approach. *Alzheimer's & Dementia: DADM* 2026. https://doi.org/10.1002/dad2.70286 (cut-offs 0.096 / 0.319 pg/mL).
7. Plasma phosphorylated tau 217 cutoffs for amyloid pathology and kidney function, body mass index, and anemia. *JAMA Neurology* 2026 (n = 2,571, amyloid PET). https://jamanetwork.com/journals/jamaneurology/fullarticle/2844557 (optimal p-tau217 cut-off 0.595 with anaemia vs 0.425 reference; kidney dysfunction and anaemia act independently; obesity effect modest; WHO anaemia: Hb < 12 g/dL women, < 13 g/dL men).
8. Confounding factors to Alzheimer's disease plasma biomarkers in patients from a memory-clinic cohort. *Alzheimer's & Dementia* 2024. https://alz-journals.onlinelibrary.wiley.com/doi/10.1002/alz.094091 (creatinine, kidney disease and BMI are the main confounders of p-tau217, NfL and GFAP).
9. Evaluation of plasma p-tau217 for detecting amyloid pathology in a heterogeneous community-based cohort. *Alzheimer's & Dementia* 2025. https://alz-journals.onlinelibrary.wiley.com/doi/10.1002/alz.70426 (p-tau217-amyloid relationship unchanged by diabetes or hypertension; higher p-tau217 with hypertension in amyloid-negative people, exploratory).
10. The performance of plasma p-tau217 in Black middle-aged and older adults. *Alzheimer's & Dementia* 2025. https://alz-journals.onlinelibrary.wiley.com/doi/full/10.1002/alz.70288 (diabetes not related to p-tau217).
11. Enhancing diagnostic precision in Alzheimer's disease: impact of comorbidities on blood biomarkers. https://zenodo.org/records/17814411 (plasma biomarkers associated with eGFR, homocysteine and HDL).

Clinical-variable effects follow a literature summary provided by the user (VeraHealth); its DOIs were not opened from the build environment and should be checked:

12. Mielke et al., *Nature Medicine* 2022, https://doi.org/10.1038/s41591-022-01822-2 (chronic kidney disease, myocardial infarction and stroke associated with higher p-tau217).
13. Palmqvist et al., *Nature Medicine* 2025, https://doi.org/10.1038/s41591-025-03622-w (age and sex modify p-tau217: women with AD pathology higher; amyloid-positive younger patients higher).
14. Shir et al., *Neurology* 2026, https://doi.org/10.1212/wnl.0000000000218591 (sleep apnoea, higher BMI and milder clinical stage associated with false-negative p-tau217).
15. Italian joint position paper (SIN, SIBioC, SINdem), *Neurological Sciences* 2026, https://doi.org/10.1007/s10072-026-08931-7 (interpret by pretest probability, age, kidney function, phenotype; atypical presentations need CSF/PET confirmation -> red-flag rule).
16. Martino-Adami et al., *Nature Communications* 2026, https://doi.org/10.1038/s41467-026-76434-2 (APOE e4, lower BMI and lower eGFR affect p-tau217).

The values above were taken from abstracts/search summaries of these papers (the full texts could not be opened from the build environment). Check them in the original articles before citing.

## Assumptions NOT taken from a source

- Amyloid prevalence in the memory clinic (~48%), age (mean ~71 y), 57% women, APOE e4 frequencies.
- Absolute concentrations of Abeta42 (~25-35 pg/mL) and Abeta40 (~300 pg/mL); triglyceride and HDL distributions; the effect sizes of BMI and triglycerides on p-tau217 (direction from the literature, size assumed).
- MoCA, MTA and Fazekas models; the missing-data rates per variable.
- Blood panel: haemoglobin (women 13.4, men 14.6 g/dL, lower with CKD and age; ~17% anaemic), fasting glucose (~20% diabetes), LDL and HDL distributions. Glucose, LDL and HDL have NO effect on p-tau217 in the simulation (evidence is mixed/null); they only act through vascular damage (Fazekas) and diabetes on MoCA. Anaemia raises p-tau217 by 25% directly; with its link to age and kidney function, the observed difference matches the published 1.40 cut-off ratio.
- Clinical variables: hypertension ~49%, known diabetes ~15%, stroke ~8%, cardiovascular disease ~15%, sleep apnoea ~13%, weight loss ~13%, red-flag atypical features 3%; SCD/MCI/dementia ~40/28/32%. Effect sizes on p-tau217 are ASSUMED (directions from sources 12-14): hypertension +8%, stroke or cardiovascular disease +10% each, sleep apnoea -13%, amyloid-positive women +10%, amyloid-positive p-tau217 decreasing 1.2% per year of age. Vital signs (blood pressure, heart rate) have no direct effect.
- The simulation is cleaner than reality, so the model performs better on it than it will on real data.

## Real datasets with these variables (access on application)

- **ADNI** - Alzheimer's Disease Neuroimaging Initiative, https://adni.loni.usc.edu: plasma Abeta42, Abeta40, p-tau217 (Fujirebio Lumipulse), NfL and GFAP (Quanterix) in the UPENN plasma dataset, CSF amyloid, amyloid PET, MRI, MoCA, APOE, creatinine for a subset (eGFR must be computed). Free for researchers after a data-use agreement. This is the best candidate for a real pre-trained model.
- **A4/LEARN** (cognitively unimpaired, amyloid PET reference) and **J-ADNI** (eGFR computed from creatinine) - also on application.

## Missing values in this file (% of patients)

egfr 6%, creatinine 48%, triglycerides 8%, hemoglobin 5%, ab42 3%, ab40 3%, apoe4 9%, hypertension 3%, stroke 2%, clinical_stage 2%.
