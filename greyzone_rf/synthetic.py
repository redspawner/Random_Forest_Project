"""Synthetic memory-clinic cohort, for testing the pipeline before real data exist.

THE NUMBERS PRODUCED HERE ARE ARTIFICIAL. They are loosely inspired by published
plasma-biomarker behaviour (Lumipulse-like p-tau217 in pg/mL, renal and BMI
confounding of plasma p-tau217, lower Abeta42/40 in amyloid-positive patients,
higher GFAP/NfL with age and lower eGFR) but are NOT calibrated to any real
cohort and must never be used to draw scientific conclusions.

Generative story (per patient):
    APOE e4 alleles, age, sex -> amyloid status (the "LP result")
    amyloid status + latent tau burden -> plasma p-tau217, p-tau181, Abeta42/40, GFAP, NfL
    eGFR, BMI, triglycerides  -> peripheral confounding of plasma levels
    amyloid + burden + age + education -> MoCA, MTA; age + eGFR -> Fazekas
Patients whose p-tau217 falls in the Stage-1 grey zone are kept.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import ckd_epi_2021


# Effect sizes of the simulation (log scale for p-tau217 / GFAP).
PTAU_BASE, PTAU_AMY, PTAU_BURDEN, PTAU_SD = 0.10, 1.25, 0.35, 0.62
RATIO_AMY, RATIO_SD = 0.008, 0.0095
GFAP_AMY, COG_AMY, MTA_AMY = 0.30, 0.8, 0.5
HTN_PTAU = np.log(1.08)      # hypertension: higher p-tau217 in amyloid-negative people (exploratory finding)
VASC_PTAU = np.log(1.10)     # stroke / myocardial infarction: higher p-tau217 (Mielke 2022, inconsistent)
OSA_PTAU = np.log(1 / 1.15)  # sleep apnoea / sleep disorder: lower p-tau217, more false negatives
AGE_X_AMY = -0.012           # amyloid-positive: younger patients have higher p-tau217 (Palmqvist 2025)
FEMALE_X_AMY = 0.10          # women with AD pathology have higher p-tau217 (Palmqvist 2025)
ANEMIA_PTAU = np.log(1.25)   # direct effect; with its link to age/eGFR the observed ratio is ~1.4 as in JAMA Neurol 2026
EGFR_PTAU = np.log(1.12) / 10     # +12% p-tau217 per 10 mL/min lower eGFR (Lumipulse, Mayo data)


# APOE e4 allele count frequencies of the Knight ADRC CSF study (Craig-Schapiro et al. 2011, n = 333):
# E3E3 167, E3E4 106, E2E3 37, E4E4 13, E2E4 8, E2E2 2  ->  0: 206, 1: 114, 2: 13
APOE4_ADRC = [206 / 333, 114 / 333, 13 / 333]


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _creatinine_from_egfr(egfr, age, female):
    """Invert the CKD-EPI 2021 equation (so creatinine and eGFR are consistent)."""
    kappa = np.where(female == 1, 0.7, 0.9)
    alpha = np.where(female == 1, -0.241, -0.302)
    g = egfr / (142.0 * 0.9938 ** age * np.where(female == 1, 1.012, 1.0))
    ratio = np.where(g >= 1, g ** (1.0 / alpha), g ** (-1.0 / 1.2))
    return kappa * ratio


def simulate_memory_clinic(n: int, seed: int = 0, real_base: pd.DataFrame | None = None) -> pd.DataFrame:
    """Simulate ``n`` consecutive memory-clinic patients (all p-tau217 values).

    ``real_base`` (see :func:`real_clinical_base`): real patients' clinical covariates (age, sex,
    BMI, creatinine/eGFR, LDL, diabetes, stroke, cardiovascular disease, systolic BP) and real
    APOE genotype frequencies are used instead of simulated ones; everything else is simulated
    conditionally on them.
    """
    rng = np.random.default_rng(seed)
    base = real_base
    age = np.clip(rng.normal(71, 8, n), 50, 92) if base is None else base["age"].to_numpy(float)
    female = (rng.random(n) < 0.57).astype(int) if base is None else base["female"].to_numpy(int)
    education = np.clip(np.round(rng.normal(8, 4, n)), 0, 20)
    apoe4 = rng.choice([0, 1, 2], size=n, p=[0.66, 0.29, 0.05] if base is None else APOE4_ADRC)
    amyloid = (rng.random(n) < _sigmoid(-0.55 + 0.05 * (age - 71) + 1.25 * apoe4)).astype(int)
    burden = np.where(amyloid == 1, rng.normal(1.0, 0.6, n), rng.normal(0.0, 0.35, n))
    non_ad = rng.gamma(1.2, 0.5, n)          # non-AD neurodegeneration (vascular, FTLD, ...)

    if base is None:
        egfr = np.clip(rng.normal(74 - 0.8 * (age - 71), 16, n), 15, 120)
        bmi = np.clip(rng.normal(26.8 - 0.8 * amyloid, 4.2, n), 16, 45)
        creat = _creatinine_from_egfr(egfr, age, female)
    else:
        creat = base["creatinine"].to_numpy(float)
        egfr = np.clip(ckd_epi_2021(creat, age, female), 5, 130)
        bmi = np.clip(base["bmi"].to_numpy(float) - 0.8 * amyloid, 15, 50)   # AD-related weight loss
    tg = np.exp(rng.normal(np.log(125) + 0.03 * (bmi - 26.5), 0.4, n))

    renal = 85 - egfr

    # Routine blood panel. A separate random stream keeps all other simulated values unchanged.
    rng_lab = np.random.default_rng(seed + 7919)
    hemoglobin = np.clip(rng_lab.normal(np.where(female == 1, 13.4, 14.6) - 0.025 * np.clip(renal, 0, None)
                                        - 0.01 * (age - 71), 1.2), 7, 18)
    anemia = np.where(female == 1, hemoglobin < 12.0, hemoglobin < 13.0).astype(int)
    diabetes = (rng_lab.random(n) < _sigmoid(-1.6 + 0.08 * (bmi - 26.5))).astype(int)
    if base is not None:
        diabetes = base["diabetes"].to_numpy(int)
    glucose = np.exp(rng_lab.normal(np.log(np.where(diabetes == 1, 145, 96)) + 0.006 * (bmi - 26.5), 0.13))
    ldl = np.clip(rng_lab.normal(118, 35, n), 30, 300) if base is None else base["ldl"].to_numpy(float)
    hdl = np.clip(rng_lab.normal(52 + 7 * female - 0.9 * (bmi - 26.5), 13, n), 20, 120)

    # Routine consultation: vital signs, known diagnoses / medication, clinical stage (separate stream).
    rng_cl = np.random.default_rng(seed + 104729)
    if base is None:
        hypertension = (rng_cl.random(n) < _sigmoid(-0.2 + 0.05 * (age - 71) + 0.06 * (bmi - 26.5)
                                                     + 0.8 * diabetes)).astype(int)
        systolic = np.clip(rng_cl.normal(126 + 10 * hypertension + 0.3 * (age - 71), 15), 85, 210)
    else:   # known/treated hypertension simulated from the REAL blood pressure, age and diabetes
        systolic = base["systolic_bp"].to_numpy(float)
        hypertension = (rng_cl.random(n) < _sigmoid(0.2 + 0.06 * (systolic - 130) + 0.03 * (age - 75)
                                                     + 0.6 * diabetes)).astype(int)
    diastolic = np.clip(rng_cl.normal(75 + 4 * hypertension - 0.1 * (age - 71), 9), 45, 120)
    heart_rate = np.clip(rng_cl.normal(71, 11, n), 40, 130)
    diabetes_known = diabetes * (rng_cl.random(n) < 0.85) if base is None else diabetes
    stroke = (rng_cl.random(n) < _sigmoid(-3.1 + 0.05 * (age - 71) + 0.8 * hypertension
                                          + 0.5 * diabetes)).astype(int)
    cvd = (rng_cl.random(n) < _sigmoid(-2.5 + 0.05 * (age - 71) + 0.7 * hypertension + 0.5 * diabetes
                                       + 0.5 * (1 - female))).astype(int)
    if base is not None:
        stroke = base["stroke"].to_numpy(int)
        cvd = base["cardiovascular_disease"].to_numpy(int)
    osa = (rng_cl.random(n) < _sigmoid(-2.3 + 0.12 * (bmi - 26.5) + 0.6 * (1 - female))).astype(int)
    weight_loss = (rng_cl.random(n) < _sigmoid(-2.7 + 1.0 * amyloid * (burden > 0.8) + 0.6 * non_ad)).astype(int)
    atypical = (rng_cl.random(n) < 0.03).astype(int)

    ptau_noise = rng.normal(0, PTAU_SD, n)   # biological + analytical variation shared by p-tau isoforms
    ln_ptau217 = (np.log(PTAU_BASE) + PTAU_AMY * amyloid + PTAU_BURDEN * burden + 0.010 * (age - 71)
                  + EGFR_PTAU * renal - 0.030 * (bmi - 26.5) - 0.15 * np.log(tg / 125)
                  + ANEMIA_PTAU * anemia + ptau_noise
                  + AGE_X_AMY * (age - 71) * amyloid + FEMALE_X_AMY * female * amyloid
                  + HTN_PTAU * hypertension + VASC_PTAU * (stroke + cvd) + OSA_PTAU * osa)
    ln_ptau181 = (np.log(1.3) + 0.30 * amyloid + 0.15 * burden + 0.008 * renal
                  + 0.6 * ptau_noise + rng.normal(0, 0.35, n))
    ab40 = np.clip(rng.normal(300 + 1.2 * renal, 45, n), 120, 700)
    ratio = np.clip(0.102 - RATIO_AMY * amyloid - 0.003 * burden + rng.normal(0, RATIO_SD, n), 0.04, 0.16)
    ab42 = ratio * ab40
    ln_gfap = (np.log(115) + GFAP_AMY * amyloid + 0.10 * burden + 0.012 * (age - 71)
               + 0.006 * renal * (1 - 0.5 * female) + rng.normal(0, 0.35, n))
    ln_nfl = (np.log(14) + 0.12 * amyloid + 0.021 * (age - 71) + 0.010 * renal
              - 0.010 * (bmi - 26.5) + 0.35 * non_ad + rng.normal(0, 0.30, n))

    impairment = amyloid * np.clip(burden + 0.3, 0, None) * COG_AMY + 0.5 * non_ad
    moca = np.clip(np.round(26.5 + 0.18 * (education - 8) - 0.06 * (age - 71)
                            - 2.6 * impairment - 0.5 * diabetes - 1.0 * stroke + rng.normal(0, 2.0, n)), 0, 30)
    severity = impairment + 0.5 * non_ad + 0.4 * stroke + rng_cl.normal(0, 0.35, n)
    stage = np.select([severity < 0.8, severity < 1.5], [0, 1], 2)   # 0 SCD, 1 MCI, 2 dementia
    mta = np.clip(np.round(0.8 + 0.06 * (age - 71) + MTA_AMY * amyloid * (burden + 0.4)
                           + 0.3 * non_ad + rng.normal(0, 0.6, n)), 0, 4)
    fazekas = np.clip(np.round(1.0 + 0.04 * (age - 71) + 0.012 * renal + 0.3 * non_ad + 0.3 * diabetes + 0.5 * stroke + 0.2 * cvd
                               + 0.003 * (ldl - 118) - 0.005 * (hdl - 55) + rng.normal(0, 0.7, n)), 0, 3)

    return pd.DataFrame({
        "age": np.round(age).astype(int),
        "sex": np.where(female == 1, "F", "M"),
        "education_years": education.astype(int),
        "bmi": np.round(bmi, 1),
        "egfr": np.round(egfr).astype(int),
        "creatinine": np.round(creat, 2),
        "triglycerides": np.round(tg).astype(int),
        "hemoglobin": np.round(hemoglobin, 1),
        "ldl": np.round(ldl).astype(int),
        "hdl": np.round(hdl).astype(int),
        "hypertension": hypertension,
        "diabetes": diabetes_known.astype(int),
        "stroke": stroke,
        "cardiovascular_disease": cvd,
        "sleep_apnea": osa,
        "weight_loss": weight_loss,
        "clinical_stage": np.array(["SCD", "MCI", "Dementia"])[stage],
        "atypical_features": atypical,
        "ptau217": np.round(np.exp(ln_ptau217), 3),
        # Not in the current model / template (kept for sensitivity analyses; filtered out by make_demo_data.py):
        "ptau181": np.round(np.exp(ln_ptau181), 2),
        "gfap": np.round(np.exp(ln_gfap), 1),
        "ab42": np.round(ab42, 1),
        "ab40": np.round(ab40, 1),
        "apoe4": apoe4,
        "moca": moca.astype(int),
        "mta_score": mta.astype(int),
        "lp_result": np.where(amyloid == 1, "Positive", "Negative"),
    })


MISSING_RATES = {
    # Abeta42/40 always part of the work-up, MRI MTA rating often absent, APOE usually known.
    "education_years": 0.05, "bmi": 0.03, "triglycerides": 0.10, "hemoglobin": 0.05, "ldl": 0.12,
    "hdl": 0.12, "apoe4": 0.10, "moca": 0.05, "mta_score": 0.40, "hypertension": 0.03, "diabetes": 0.03,
    "stroke": 0.03, "cardiovascular_disease": 0.03, "sleep_apnea": 0.05, "weight_loss": 0.08,
    "clinical_stage": 0.02,
}


def _add_missingness(df: pd.DataFrame, rng) -> pd.DataFrame:
    df = df.astype(object)
    for column, rate in MISSING_RATES.items():
        df.loc[rng.random(len(df)) < rate, column] = None
    amyloid_missing = rng.random(len(df)) < 0.03          # Abeta42/40 part of the work-up; rare assay failure
    df.loc[amyloid_missing, ["ab42", "ab40"]] = None
    egfr_missing = rng.random(len(df)) < 0.06             # only creatinine available
    df.loc[egfr_missing, "egfr"] = None
    df.loc[~egfr_missing & (rng.random(len(df)) < 0.5), "creatinine"] = None
    return df


def grey_zone_cohort(n_patients: int, lower: float = 0.14, upper: float = 0.43,
                     seed: int = 0, prefix: str = "SYN", real: bool = False) -> pd.DataFrame:
    """Return ``n_patients`` synthetic patients whose p-tau217 is in the grey zone."""
    rng = np.random.default_rng(seed + 1)
    chunks, total = [], 0
    batch = 0
    while total < n_patients:
        size = max(4 * n_patients, 2000)
        base = real_clinical_base(size, seed=seed + 17 * batch, chs=_chs_cache()) if real else None
        pop = simulate_memory_clinic(size, seed=seed + 17 * batch, real_base=base)
        grey = pop[(pop["ptau217"] >= lower) & (pop["ptau217"] <= upper)]
        chunks.append(grey)
        total += len(grey)
        batch += 1
    df = pd.concat(chunks).iloc[:n_patients].reset_index(drop=True)
    df = _add_missingness(df, rng)
    df.insert(0, "patient_id", [f"{prefix}-{i + 1:04d}" for i in range(len(df))])
    return df


def demo_new_patients(n_grey: int = 40, seed: int = 999, lower: float = 0.14,
                      upper: float = 0.43, real: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """New (unlabelled) patients for the prediction demo, plus a hidden answer key.

    Besides grey-zone patients, three special rows show the safety checks:
    one below the grey zone, one above it, and one with an impossible haemoglobin (45 g/dL).
    """
    df = grey_zone_cohort(n_grey, lower, upper, seed=seed, prefix="NEW", real=real)
    extra = simulate_memory_clinic(400, seed=seed + 5,
                                   real_base=real_clinical_base(400, seed + 5, chs=_chs_cache()) if real else None)
    low = extra[extra["ptau217"] < lower].iloc[[0]]
    high = extra[extra["ptau217"] > upper].iloc[[0]]
    bad = extra[(extra["ptau217"] >= lower) & (extra["ptau217"] <= upper)].iloc[[0]].copy()
    bad["hemoglobin"] = 45.0          # impossible value (typing error) -> CHECK DATA
    specials = pd.concat([low, high, bad]).astype(object)
    specials.insert(0, "patient_id", ["NEW-LOW", "NEW-HIGH", "NEW-TYPO"])
    df = pd.concat([df, specials], ignore_index=True)
    key = df[["patient_id", "lp_result"]].copy()
    return df.drop(columns=["lp_result"]), key


def population_check(n: int = 20000, seed: int = 0, lower: float = 0.14, upper: float = 0.43) -> dict:
    """Quick descriptive check of the simulated memory-clinic population."""
    pop = simulate_memory_clinic(n, seed)
    grey = (pop["ptau217"] >= lower) & (pop["ptau217"] <= upper)
    pos = pop["lp_result"] == "Positive"
    egfr_check = ckd_epi_2021(pop["creatinine"], pop["age"], (pop["sex"] == "F").astype(int))
    return {
        "amyloid_prevalence": float(pos.mean()),
        "grey_zone_fraction": float(grey.mean()),
        "grey_zone_prevalence": float(pos[grey].mean()),
        "below_lower_npv": float((~pos[pop["ptau217"] < lower]).mean()),
        "above_upper_ppv": float(pos[pop["ptau217"] > upper].mean()),
        "max_egfr_inversion_error": float(np.max(np.abs(egfr_check - pop["egfr"]))),
    }


# ---------------------------------------------------------------------------
# Literature targets used to calibrate the generator (see data/default_training/DATASET_CARD.md)
# ---------------------------------------------------------------------------
CALIBRATION_TARGETS = {
    "auc_ptau217": (0.95, "Lumipulse plasma p-tau217 vs CSF, memory clinic (Alzheimer's Res Ther 2025)"),
    "auc_ptau217_ab42": (0.97, "p-tau217/Abeta42 ratio, same study"),
    "auc_ab42_ab40": (0.72, "plasma Abeta42/40, same study (0.85 vs CSF in a Japanese memory-clinic study)"),
    "grey_zone_fraction": (0.30, "intermediate zone 15-30% with two cut-offs (several Lumipulse studies)"),
    "ptau217_increase_per_10_egfr": (0.12, "+12% Lumipulse p-tau217 per 10 mL/min lower eGFR (Mayo Clinic data)"),
    "ptau217_ratio_anemia": (1.40, "optimal p-tau217 cut-off with anaemia 0.595 vs 0.425 pg/mL (JAMA Neurol 2026, n=2571)"),
}


def _anemia_ratio(pop: pd.DataFrame, y) -> float:
    """Median p-tau217 of anaemic vs non-anaemic amyloid-negative patients."""
    female = pop["sex"] == "F"
    anemic = np.where(female, pop["hemoglobin"] < 12, pop["hemoglobin"] < 13)
    neg = np.asarray(y) == 0
    return float(pop["ptau217"][neg & anemic].median() / pop["ptau217"][neg & ~anemic].median())


def calibration_report(n: int = 30000, seed: int = 0, lower: float = 0.14, upper: float = 0.43,
                       real: bool = False) -> pd.DataFrame:
    """Compare the simulated population with the literature targets."""
    from sklearn.metrics import roc_auc_score

    base = real_clinical_base(n, seed, chs=_chs_cache()) if real else None
    pop = simulate_memory_clinic(n, seed, real_base=base)
    y = (pop["lp_result"] == "Positive").astype(int)
    ratio = pop["ab42"] / pop["ab40"]
    simulated = {
        "auc_ptau217": roc_auc_score(y, pop["ptau217"]),
        "auc_ptau217_ab42": roc_auc_score(y, pop["ptau217"] / pop["ab42"]),
        "auc_ab42_ab40": roc_auc_score(y, -ratio),
        "grey_zone_fraction": float(((pop["ptau217"] >= lower) & (pop["ptau217"] <= upper)).mean()),
        "ptau217_increase_per_10_egfr": float(np.exp(10 * EGFR_PTAU) - 1),
        "ptau217_ratio_anemia": _anemia_ratio(pop, y),
    }
    return pd.DataFrame([{"quantity": k, "published": CALIBRATION_TARGETS[k][0], "simulated": round(v, 3),
                          "source": CALIBRATION_TARGETS[k][1]} for k, v in simulated.items()])


# ---------------------------------------------------------------------------
# Real clinical covariates (Cardiovascular Health Study MRI sub-study, public)
# ---------------------------------------------------------------------------
CHS_FILE = "data/external/chs_mri_rigr.csv"


def load_chs(path=None) -> pd.DataFrame:
    """The 735 CHS participants, with the columns this project uses (complete cases)."""
    from .config import PROJECT_ROOT

    raw = pd.read_csv(path or PROJECT_ROOT / CHS_FILE)
    out = pd.DataFrame({
        "age": raw["age"],
        "female": (raw["sex"] == "Female").astype(int),
        "bmi": raw["weight"] * 0.45359237 / (raw["height"] / 100) ** 2,     # weight is in pounds
        "creatinine": raw["crt"],
        "ldl": raw["ldl"],
        "diabetes": raw["diabetes"].astype(int),
        "stroke": (raw["stroke"] > 0).astype(int),
        "cardiovascular_disease": ((raw["chd"] > 0) | (raw["chf"] > 0)).astype(int),
        "systolic_bp": raw["sbp"],
    })
    return out.dropna().reset_index(drop=True)


def real_clinical_base(n: int, seed: int = 0, chs: pd.DataFrame | None = None) -> pd.DataFrame:
    """Resample ``n`` real CHS participants with small jitter (no row copied unchanged)."""
    chs = load_chs() if chs is None else chs
    rng = np.random.default_rng(seed + 31337)
    rows = chs.iloc[rng.integers(0, len(chs), n)].reset_index(drop=True).copy()
    rows["age"] = np.clip(rows["age"] + rng.integers(-2, 3, n), 60, 99)
    rows["bmi"] = rows["bmi"] * np.exp(rng.normal(0, 0.03, n))
    rows["creatinine"] = np.clip(rows["creatinine"] * np.exp(rng.normal(0, 0.05, n)), 0.3, 8)
    rows["ldl"] = np.clip(rows["ldl"] * np.exp(rng.normal(0, 0.05, n)), 20, 350)
    rows["systolic_bp"] = np.clip(rows["systolic_bp"] + rng.normal(0, 5, n), 80, 230)
    return rows


_CHS = None


def _chs_cache() -> pd.DataFrame:
    global _CHS
    if _CHS is None:
        _CHS = load_chs()
    return _CHS
