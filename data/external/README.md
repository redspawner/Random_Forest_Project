# External public data

## `chs_mri_rigr.csv` - Cardiovascular Health Study, MRI sub-study (n = 735)

* **What:** 735 community-dwelling adults aged 65 or older from the U.S. Cardiovascular Health
  Study (CHS), with cranial MRI. The variables used here are age, sex, weight (pounds), height
  (cm), serum creatinine (mg/dL), LDL cholesterol (mg/dL), diabetes, stroke, coronary heart
  disease, congestive heart failure and systolic blood pressure.
* **Where it comes from:** the `mri` dataset of the R package **rigr** (University of Washington
  Department of Biostatistics teaching data). It is distributed as `mriCardioVars_tbl_df` in the R
  package **CardioDataSets** and mirrored by the Rdatasets project:
  <https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/CardioDataSets/mriCardioVars_tbl_df.csv>
  (downloaded 2026-11-11, unmodified).
* **Use in this project:** real joint distribution of the clinical covariates for the synthetic
  memory-clinic cohort (`greyzone_rf/synthetic.py`, `real_clinical_base`). Rows are resampled with
  small random jitter. No row of this file appears unchanged in the training dataset.
* De-identified public teaching data. Check the licence of the rigr / CardioDataSets packages
  before any further redistribution.

## APOE genotype frequencies (not stored as a file)

Taken from the Knight ADRC CSF study (Craig-Schapiro et al., *PLoS ONE* 2011; R package
`modeldata`, dataset `ad_data`, n = 333): E3E3 167, E3E4 106, E2E3 37, E4E4 13, E2E4 8, E2E2 2.

## `knight_adrc_csf_ad_data.csv` - Knight ADRC CSF study (n = 333)

* **What:** 333 participants of the Washington University Knight Alzheimer's Disease Research Center
  with CSF biomarkers: APOE genotype (`Genotype`), sex (`male`), clinical status (`Class`:
  Control = CDR 0, Impaired = CDR > 0), CSF Abeta42 (`Ab_42`), tau and p-tau, on the transformed
  scale of the source. Only these 6 of the 132 columns are kept.
* **Where it comes from:** Craig-Schapiro R et al., *PLoS ONE* 2011;6:e18850 (open access);
  distributed as `ad_data` in the R package **modeldata** (originally AppliedPredictiveModeling),
  mirrored by Rdatasets:
  <https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/modeldata/ad_data.csv>
  (downloaded 2026-11-20).
* **Use in this project:** `greyzone_rf/synthetic_v2.py` defines CSF amyloid positivity with a
  two-component mixture of CSF Abeta42. It then estimates the APOE e4 log odds ratios for
  amyloid positivity separately for normal and impaired participants. Those real-data effects
  drive the amyloid prevalence of the version-2 synthetic cohort.
* De-identified public research data; check the modeldata licence (MIT) and cite the original
  paper.
