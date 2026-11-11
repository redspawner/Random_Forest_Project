# Dataset card - default training dataset

**File:** `data/default_training/synthetic_training_dataset.xlsx`  
**SHA-256:** `453990939ed4e448aff03b1499dfc4c62fad4e5a29ef0a4117f3f1a19c49b3f0`  
**Patients:** 600 grey-zone patients (p-tau217 0.14-0.43 pg/mL), 244 LP-positive / 356 LP-negative  
**Generator:** `greyzone_rf/synthetic.py`, `grey_zone_cohort(n=600, seed=2024)`

## What this is

**Synthetic (artificial) patients.** No real patient record was used. No open dataset contains all the variables of this project at individual level, so the patients were simulated with a causal model (APOE, age -> amyloid status -> plasma biomarkers, with kidney function, BMI and triglycerides as peripheral confounders) whose parameters were tuned so that the simulated memory-clinic population reproduces published summary statistics. Grey-zone patients were then selected with the Stage-1 cut-offs.

## Calibration against published values (simulated population of 30 000 patients)

| Quantity | Published | Simulated | Source |
|---|---|---|---|
| auc_ptau217 | 0.95 | 0.956 | Lumipulse plasma p-tau217 vs CSF, memory clinic (Alzheimer's Res Ther 2025) |
| auc_ptau217_ab42 | 0.97 | 0.963 | p-tau217/Abeta42 ratio, same study |
| auc_ab42_ab40 | 0.72 | 0.791 | plasma Abeta42/40, same study (0.85 vs CSF in a Japanese memory-clinic study) |
| grey_zone_fraction | 0.3 | 0.315 | intermediate zone 15-30% with two cut-offs (several Lumipulse studies) |
| ptau217_increase_per_10_egfr | 0.12 | 0.12 | +12% Lumipulse p-tau217 per 10 mL/min lower eGFR (Mayo Clinic data) |
| age_variance_nfl | 0.26 | 0.271 | age explains 26% of plasma NfL variance (memory-clinic study) |
| age_variance_gfap | 0.12 | 0.123 | age explains 12% of plasma GFAP variance (same study) |
| ptau217_ratio_anemia | 1.4 | 1.432 | optimal p-tau217 cut-off with anaemia 0.595 vs 0.425 pg/mL (JAMA Neurol 2026, n=2571) |

## Sources

1. Diagnostic performance of plasma p-tau217 in a memory clinic cohort using the Lumipulse automated platform. *Alzheimer's Research & Therapy* 2025. https://doi.org/10.1186/s13195-025-01719-5 (p-tau217 AUC 0.95 vs CSF; p-tau217/Abeta42 AUC 0.97; Abeta42/40 AUC 0.72).
2. Prospective study on clinical utility of plasma p-Tau217 and other biomarkers in Japanese memory clinics using the LUMIPULSE platform. *Alzheimer's Research & Therapy* 2026. https://doi.org/10.1186/s13195-026-01997-7 (plasma Abeta42/40 AUC 0.85 vs CSF; intermediate zone 15%).
3. Effect of kidney function on plasma pTau217 concentrations using different pTau217 assays (Mayo Clinic). https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11715048/ (+12% Lumipulse p-tau217 per 10-unit lower eGFR).
4. Profiling of plasma biomarkers in the context of memory assessment in a tertiary memory clinic. *Translational Psychiatry* 2023. https://www.nature.com/articles/s41398-023-02558-4 (age explains 26% of NfL and 12% of GFAP variance; GFAP best single amyloid predictor).
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
- Absolute concentrations of Abeta42 (~25-35 pg/mL), Abeta40 (~300 pg/mL), GFAP (~120-185 pg/mL), NfL (~14-20 pg/mL), p-tau181; BMI, triglyceride and eGFR distributions; the effect sizes of BMI and triglycerides on p-tau217 (direction from the literature, size assumed).
- MoCA, MTA and Fazekas models; the missing-data rates per variable.
- Blood panel: haemoglobin (women 13.4, men 14.6 g/dL, lower with CKD and age; ~17% anaemic), fasting glucose (~20% diabetes), LDL and HDL distributions. Glucose, LDL and HDL have NO effect on p-tau217 in the simulation (evidence is mixed/null); they only act through vascular damage (Fazekas) and diabetes on MoCA. Anaemia raises p-tau217 by 25% directly; with its link to age and kidney function, the observed difference matches the published 1.40 cut-off ratio.
- Clinical variables: hypertension ~49%, known diabetes ~15%, stroke ~8%, cardiovascular disease ~15%, sleep apnoea ~13%, weight loss ~13%, red-flag atypical features 3%; SCD/MCI/dementia ~40/28/32%. Effect sizes on p-tau217 are ASSUMED (directions from sources 12-14): hypertension +8%, stroke or cardiovascular disease +10% each, sleep apnoea -13%, amyloid-positive women +10%, amyloid-positive p-tau217 decreasing 1.2% per year of age. Vital signs (blood pressure, heart rate) have no direct effect.
- The simulation is cleaner than reality, so the model performs better on it than it will on real data.

## Real datasets with these variables (access on application)

- **ADNI** - Alzheimer's Disease Neuroimaging Initiative, https://adni.loni.usc.edu: plasma Abeta42, Abeta40, p-tau217 (Fujirebio Lumipulse), NfL and GFAP (Quanterix) in the UPENN plasma dataset, CSF amyloid, amyloid PET, MRI, MoCA, APOE, creatinine for a subset (eGFR must be computed). Free for researchers after a data-use agreement. This is the best candidate for a real pre-trained model.
- **A4/LEARN** (cognitively unimpaired, amyloid PET reference) and **J-ADNI** (eGFR computed from creatinine) - also on application.

## Missing values in this file (% of patients)

education_years 4%, bmi 6%, egfr 8%, creatinine 45%, triglycerides 8%, hemoglobin 5%, glucose 8%, ldl 14%, hdl 14%, systolic_bp 4%, diastolic_bp 4%, heart_rate 4%, hypertension 5%, diabetes 2%, stroke 3%, cardiovascular_disease 3%, sleep_apnea 5%, weight_loss 8%, clinical_stage 2%, ptau181 12%, ab42 8%, ab40 8%, gfap 8%, nfl 8%, apoe4 31%, moca 5%, mta_score 15%, fazekas 15%.
