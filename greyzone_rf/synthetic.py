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
EGFR_PTAU = np.log(1.12) / 10     # +12% p-tau217 per 10 mL/min lower eGFR (Lumipulse, Mayo data)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _creatinine_from_egfr(egfr, age, female):
    """Invert the CKD-EPI 2021 equation (so creatinine and eGFR are consistent)."""
    kappa = np.where(female == 1, 0.7, 0.9)
    alpha = np.where(female == 1, -0.241, -0.302)
    g = egfr / (142.0 * 0.9938 ** age * np.where(female == 1, 1.012, 1.0))
    ratio = np.where(g >= 1, g ** (1.0 / alpha), g ** (-1.0 / 1.2))
    return kappa * ratio


def simulate_memory_clinic(n: int, seed: int = 0) -> pd.DataFrame:
    """Simulate ``n`` consecutive memory-clinic patients (all p-tau217 values)."""
    rng = np.random.default_rng(seed)
    age = np.clip(rng.normal(71, 8, n), 50, 92)
    female = (rng.random(n) < 0.57).astype(int)
    education = np.clip(np.round(rng.normal(8, 4, n)), 0, 20)
    apoe4 = rng.choice([0, 1, 2], size=n, p=[0.66, 0.29, 0.05])
    amyloid = (rng.random(n) < _sigmoid(-0.55 + 0.05 * (age - 71) + 1.25 * apoe4)).astype(int)
    burden = np.where(amyloid == 1, rng.normal(1.0, 0.6, n), rng.normal(0.0, 0.35, n))
    non_ad = rng.gamma(1.2, 0.5, n)          # non-AD neurodegeneration (vascular, FTLD, ...)

    egfr = np.clip(rng.normal(74 - 0.8 * (age - 71), 16, n), 15, 120)
    bmi = np.clip(rng.normal(26.8 - 0.8 * amyloid, 4.2, n), 16, 45)
    tg = np.exp(rng.normal(np.log(125) + 0.03 * (bmi - 26.5), 0.4, n))
    creat = _creatinine_from_egfr(egfr, age, female)

    renal = 85 - egfr
    ptau_noise = rng.normal(0, PTAU_SD, n)   # biological + analytical variation shared by p-tau isoforms
    ln_ptau217 = (np.log(PTAU_BASE) + PTAU_AMY * amyloid + PTAU_BURDEN * burden + 0.010 * (age - 71)
                  + EGFR_PTAU * renal - 0.030 * (bmi - 26.5) - 0.15 * np.log(tg / 125)
                  + ptau_noise)
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
                            - 2.6 * impairment + rng.normal(0, 2.0, n)), 0, 30)
    mta = np.clip(np.round(0.8 + 0.06 * (age - 71) + MTA_AMY * amyloid * (burden + 0.4)
                           + 0.3 * non_ad + rng.normal(0, 0.6, n)), 0, 4)
    fazekas = np.clip(np.round(1.0 + 0.04 * (age - 71) + 0.012 * renal + 0.3 * non_ad
                               + rng.normal(0, 0.7, n)), 0, 3)

    return pd.DataFrame({
        "age": np.round(age).astype(int),
        "sex": np.where(female == 1, "F", "M"),
        "education_years": education.astype(int),
        "bmi": np.round(bmi, 1),
        "egfr": np.round(egfr).astype(int),
        "creatinine": np.round(creat, 2),
        "triglycerides": np.round(tg).astype(int),
        "ptau217": np.round(np.exp(ln_ptau217), 3),
        "ptau181": np.round(np.exp(ln_ptau181), 2),
        "ab42": np.round(ab42, 1),
        "ab40": np.round(ab40, 1),
        "gfap": np.round(np.exp(ln_gfap), 1),
        "nfl": np.round(np.exp(ln_nfl), 1),
        "apoe4": apoe4,
        "moca": moca.astype(int),
        "mta_score": mta.astype(int),
        "fazekas": fazekas.astype(int),
        "lp_result": np.where(amyloid == 1, "Positive", "Negative"),
    })


MISSING_RATES = {
    "education_years": 0.05, "bmi": 0.05, "triglycerides": 0.10, "ptau181": 0.10,
    "gfap": 0.08, "nfl": 0.08, "apoe4": 0.30, "moca": 0.05, "mta_score": 0.15, "fazekas": 0.15,
}


def _add_missingness(df: pd.DataFrame, rng) -> pd.DataFrame:
    df = df.astype(object)
    for column, rate in MISSING_RATES.items():
        df.loc[rng.random(len(df)) < rate, column] = None
    amyloid_missing = rng.random(len(df)) < 0.08          # Abeta assay not run
    df.loc[amyloid_missing, ["ab42", "ab40"]] = None
    egfr_missing = rng.random(len(df)) < 0.06             # only creatinine available
    df.loc[egfr_missing, "egfr"] = None
    df.loc[~egfr_missing & (rng.random(len(df)) < 0.5), "creatinine"] = None
    return df


def grey_zone_cohort(n_patients: int, lower: float = 0.14, upper: float = 0.43,
                     seed: int = 0, prefix: str = "SYN") -> pd.DataFrame:
    """Return ``n_patients`` synthetic patients whose p-tau217 is in the grey zone."""
    rng = np.random.default_rng(seed + 1)
    chunks, total = [], 0
    batch = 0
    while total < n_patients:
        pop = simulate_memory_clinic(max(4 * n_patients, 2000), seed=seed + 17 * batch)
        grey = pop[(pop["ptau217"] >= lower) & (pop["ptau217"] <= upper)]
        chunks.append(grey)
        total += len(grey)
        batch += 1
    df = pd.concat(chunks).iloc[:n_patients].reset_index(drop=True)
    df = _add_missingness(df, rng)
    df.insert(0, "patient_id", [f"{prefix}-{i + 1:04d}" for i in range(len(df))])
    return df


def demo_new_patients(n_grey: int = 40, seed: int = 999, lower: float = 0.14,
                      upper: float = 0.43) -> tuple[pd.DataFrame, pd.DataFrame]:
    """New (unlabelled) patients for the prediction demo, plus a hidden answer key.

    Besides grey-zone patients, three special rows show the safety checks:
    one below the grey zone, one above it, and one with an impossible MoCA (34).
    """
    df = grey_zone_cohort(n_grey, lower, upper, seed=seed, prefix="NEW")
    extra = simulate_memory_clinic(400, seed=seed + 5)
    low = extra[extra["ptau217"] < lower].iloc[[0]]
    high = extra[extra["ptau217"] > upper].iloc[[0]]
    bad = extra[(extra["ptau217"] >= lower) & (extra["ptau217"] <= upper)].iloc[[0]].copy()
    bad["moca"] = 34
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
    "age_variance_nfl": (0.26, "age explains 26% of plasma NfL variance (memory-clinic study)"),
    "age_variance_gfap": (0.12, "age explains 12% of plasma GFAP variance (same study)"),
}


def calibration_report(n: int = 30000, seed: int = 0, lower: float = 0.14, upper: float = 0.43) -> pd.DataFrame:
    """Compare the simulated population with the literature targets."""
    from sklearn.metrics import roc_auc_score

    pop = simulate_memory_clinic(n, seed)
    y = (pop["lp_result"] == "Positive").astype(int)
    ratio = pop["ab42"] / pop["ab40"]
    simulated = {
        "auc_ptau217": roc_auc_score(y, pop["ptau217"]),
        "auc_ptau217_ab42": roc_auc_score(y, pop["ptau217"] / pop["ab42"]),
        "auc_ab42_ab40": roc_auc_score(y, -ratio),
        "grey_zone_fraction": float(((pop["ptau217"] >= lower) & (pop["ptau217"] <= upper)).mean()),
        "ptau217_increase_per_10_egfr": float(np.exp(10 * EGFR_PTAU) - 1),
        "age_variance_nfl": float(np.corrcoef(pop["age"], np.log(pop["nfl"]))[0, 1] ** 2),
        "age_variance_gfap": float(np.corrcoef(pop["age"], np.log(pop["gfap"]))[0, 1] ** 2),
    }
    return pd.DataFrame([{"quantity": k, "published": CALIBRATION_TARGETS[k][0], "simulated": round(v, 3),
                          "source": CALIBRATION_TARGETS[k][1]} for k, v in simulated.items()])
