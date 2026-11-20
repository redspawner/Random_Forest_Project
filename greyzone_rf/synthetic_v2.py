"""Synthetic memory-clinic cohort, version 2: non-linear and anchored to two public real datasets.

Why a second generator?
-----------------------
Version 1 (synthetic.py) builds the lumbar-puncture result and plasma p-tau217 from mostly additive,
log-linear effects. That structure is exactly what a logistic regression assumes, so it favours that
model. Biology is not additive. Version 2 keeps the same real clinical covariates but makes the
relationships non-linear where the literature says they are:

* **Amyloid prevalence** depends on clinical stage, APOE e4 *dose* (two alleles far more than twice
  one) and age with a flattening curve. The APOE effect shrinks with age.
  - The APOE x clinical-status prevalences are estimated from REAL data: the Knight ADRC CSF study
    (Craig-Schapiro 2011, n = 333, vendored in data/external/knight_adrc_csf_ad_data.csv).
    Amyloid status is CSF Abeta42 positivity from a two-component mixture.
  - The age curves follow the amyloid-PET/CSF meta-analysis of Jansen et al. (JAMA 2015) and, for
    dementia, Ossenkoppele et al. (JAMA 2015).
* **Continuous amyloid load** (centiloid-like). The LP (CSF) result is a noisy threshold on it, so
  about 5-10 % of borderline patients are discordant, as between CSF and PET in practice.
* **Plasma p-tau217 rises sigmoidally** with amyloid load (starts around 20-30 centiloids, then
  plateaus) and further with tau, which is higher in later clinical stages. Sources: Mattsson-
  Carlgren 2023 (Nat Med), Therriault 2023.
* **Kidney function acts with a threshold.** p-tau217 is almost unaffected above an eGFR of about
  70 mL/min/1.73 m2 and rises steeply below 60, roughly doubling in CKD stage 4. Sources: Mielke
  2022 (JAMA Neurol), Janelidze 2023, Pichet Binette 2023.
* Anaemia (ratio about 1.25-1.4; JAMA Neurol 2026), lower BMI, hypertension and stroke shift
  p-tau217 independently of amyloid, as in version 1.

Real covariates (age, sex, creatinine/eGFR, BMI, LDL, diabetes, stroke, cardiovascular disease,
blood pressure) come from the Cardiovascular Health Study via ``synthetic.real_clinical_base``.
The output columns are those of version 1, so all downstream code works unchanged.

THE PATIENTS ARE ARTIFICIAL. Use them to test the pipeline and to compare models under realistic
structure, never as clinical evidence.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from .data import ckd_epi_2021

KNIGHT_FILE = "data/external/knight_adrc_csf_ad_data.csv"
APOE4_ADRC = [206 / 333, 114 / 333, 13 / 333]       # e4 allele count frequencies, Knight ADRC

# Memory-clinic case mix of clinical stage by age (SCD, MCI, dementia): older patients are more
# often demented. About 30/45/25 % at age 72, close to European memory-clinic registries.
STAGE_LOGIT = {"mci": 0.40, "dem": -0.45, "age_mci": 0.03, "age_dem": 0.07}

# Amyloid prevalence at age 70 in APOE e4 non-carriers (logit intercept per stage), from Jansen 2015
# (SCD about 0.18, MCI about 0.38) and Ossenkoppele 2015 / memory-clinic mixed dementia (about 0.62).
AMY_ALPHA = {0: -1.52, 1: -0.49, 2: 0.49}
AGE_SLOPE_YOUNG, AGE_SLOPE_OLD, AGE_KNOT = 0.065, 0.025, 75.0  # flattening of prevalence with age
APOE_AGE_SHRINK = 0.025                                         # APOE log-odds shrink 2.5 % per year >70

# Plasma p-tau217 (Lumipulse, pg/mL), log scale
PTAU_BASE = np.log(0.105)
PTAU_AMY_MAX, PTAU_AMY_MID, PTAU_AMY_WIDTH = 1.75, 32.0, 11.0   # sigmoid in amyloid load (centiloid-like)
PTAU_TAU = 0.32                                                 # tau burden (stage-related, amyloid+)
PTAU_SD = 0.40
KIDNEY_KNEE1, KIDNEY_SLOPE1 = 70.0, 0.012                       # +1.2 % per mL/min below 70
KIDNEY_KNEE2, KIDNEY_SLOPE2 = 45.0, 0.012                       # steeper below 45 (CKD 3b-4)
ANEMIA_PTAU = np.log(1.25)
HTN_PTAU, VASC_PTAU = np.log(1.06), np.log(1.10)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


@lru_cache(maxsize=1)
def knight_apoe_log_odds() -> dict[str, tuple[float, float]]:
    """APOE e4 (1 allele, 2 alleles) log odds ratios for CSF amyloid positivity, estimated from the
    real Knight ADRC data separately for cognitively normal and impaired participants.

    Amyloid positivity = lower component of a two-component Gaussian mixture of CSF Abeta42 (the
    data are bimodal). Counts get +0.5 (Haldane) so that empty or full cells stay finite.
    """
    from sklearn.mixture import GaussianMixture

    from .config import PROJECT_ROOT

    d = pd.read_csv(PROJECT_ROOT / KNIGHT_FILE)
    ab = d["Ab_42"].to_numpy().reshape(-1, 1)
    gm = GaussianMixture(2, random_state=0).fit(ab)
    low = int(np.argmin(gm.means_.ravel()))
    amyloid = gm.predict_proba(ab)[:, low] > 0.5
    e4 = d["Genotype"].str.count("4").to_numpy()
    out = {}
    for group in ("Control", "Impaired"):
        mask = d["Class"].to_numpy() == group

        def logit(k):
            pos = np.sum(amyloid[mask & (e4 == k)]) + 0.5
            neg = np.sum(~amyloid[mask & (e4 == k)]) + 0.5
            return np.log(pos / neg)

        out[group] = (logit(1) - logit(0), logit(2) - logit(0))
    return out


def amyloid_probability(age, apoe4, stage) -> np.ndarray:
    """P(amyloid positive | age, APOE e4 count, clinical stage 0/1/2), non-linear in all three."""
    lor = knight_apoe_log_odds()
    age = np.asarray(age, float)
    apoe4 = np.asarray(apoe4, int)
    stage = np.asarray(stage, int)
    het = np.where(stage == 0, lor["Control"][0], lor["Impaired"][0])
    hom = np.where(stage == 0, lor["Control"][1], lor["Impaired"][1])
    hom = np.minimum(hom, 3.0)                                  # few E4E4 patients: cap the odds ratio
    shrink = np.clip(1 - APOE_AGE_SHRINK * np.clip(age - 70, 0, None), 0.35, 1.0)
    apoe = np.select([apoe4 == 1, apoe4 == 2], [het, hom], 0.0) * shrink
    young = np.minimum(age, AGE_KNOT) - 70
    old = np.clip(age - AGE_KNOT, 0, None)
    alpha = np.select([stage == 0, stage == 1], [AMY_ALPHA[0], AMY_ALPHA[1]], AMY_ALPHA[2])
    return _sigmoid(alpha + AGE_SLOPE_YOUNG * young + AGE_SLOPE_OLD * old + apoe)


def kidney_effect(egfr) -> np.ndarray:
    """Log-scale increase of plasma p-tau217 due to reduced kidney function (hinge, not linear)."""
    egfr = np.asarray(egfr, float)
    return (KIDNEY_SLOPE1 * np.clip(KIDNEY_KNEE1 - egfr, 0, None)
            + KIDNEY_SLOPE2 * np.clip(KIDNEY_KNEE2 - egfr, 0, None))


def simulate_memory_clinic_v2(n: int, seed: int = 0, real_base: pd.DataFrame | None = None,
                              extended: bool = False, effects: float = 1.0) -> pd.DataFrame:
    """``n`` consecutive memory-clinic patients (all p-tau217 values), version-2 biology.

    ``extended=True`` is **version 3**: the same patients plus the factors of :func:`_extended_factors`
    (thyroid, MRI MTA / Fazekas, MMSE, BMI, sleep apnoea, triglyceride and hyperfiltration effects).
    They come from a separate random stream, so version 2 stays reproducible. ``effects`` scales
    the version-3 effect sizes (0.5 = weak-evidence scenario, 1.5 = strong-evidence scenario).
    """
    from .synthetic import _creatinine_from_egfr

    rng = np.random.default_rng(seed + 2_000_003)
    base = real_base
    age = np.clip(rng.normal(72, 8, n), 50, 92) if base is None else base["age"].to_numpy(float)
    female = (rng.random(n) < 0.57).astype(int) if base is None else base["female"].to_numpy(int)
    apoe4 = rng.choice([0, 1, 2], size=n, p=APOE4_ADRC)

    # Clinical stage (memory-clinic case mix, older -> more dementia); multinomial logit
    s = STAGE_LOGIT
    z_mci = s["mci"] + s["age_mci"] * (age - 72)
    z_dem = s["dem"] + s["age_dem"] * (age - 72)
    denom = 1 + np.exp(z_mci) + np.exp(z_dem)
    u = rng.random(n)
    stage = np.where(u < 1 / denom, 0, np.where(u < (1 + np.exp(z_mci)) / denom, 1, 2))

    amyloid = (rng.random(n) < amyloid_probability(age, apoe4, stage)).astype(int)
    # continuous amyloid load (centiloid-like): negatives around 0, positives broad and stage-dependent
    load = np.where(amyloid == 1, 18 + rng.gamma(2.0, 22 + 10 * stage, n), rng.normal(0, 8, n))
    lp_positive = (load + rng.normal(0, 9, n) > 18).astype(int)      # CSF result: noisy threshold
    tau = np.where(amyloid == 1, rng.normal(0.4 * stage, 0.5, n), rng.normal(0, 0.25, n))

    if base is None:
        egfr = np.clip(rng.normal(72 - 0.8 * (age - 72), 17, n), 12, 120)
        bmi = np.clip(rng.normal(26.5, 4.2, n), 16, 45)
        creat = _creatinine_from_egfr(egfr, age, female)
        diabetes = (rng.random(n) < _sigmoid(-1.6 + 0.08 * (bmi - 26.5))).astype(int)
        stroke = (rng.random(n) < _sigmoid(-3.0 + 0.05 * (age - 72))).astype(int)
        cvd = (rng.random(n) < _sigmoid(-2.4 + 0.05 * (age - 72))).astype(int)
        systolic = np.clip(rng.normal(132 + 0.4 * (age - 72), 17, n), 85, 220)
        ldl = np.clip(rng.normal(118, 35, n), 30, 300)
    else:
        creat = base["creatinine"].to_numpy(float)
        egfr = np.clip(ckd_epi_2021(creat, age, female), 5, 130)
        bmi = base["bmi"].to_numpy(float) - 0.6 * amyloid * (stage == 2)
        diabetes = base["diabetes"].to_numpy(int)
        stroke = base["stroke"].to_numpy(int)
        cvd = base["cardiovascular_disease"].to_numpy(int)
        systolic = base["systolic_bp"].to_numpy(float)
        ldl = base["ldl"].to_numpy(float)

    rng_lab = np.random.default_rng(seed + 2_007_919)
    hemoglobin = np.clip(rng_lab.normal(np.where(female == 1, 13.4, 14.6)
                                        - 0.035 * np.clip(70 - egfr, 0, None) - 0.01 * (age - 72), 1.2), 7, 18)
    anemia = np.where(female == 1, hemoglobin < 12.0, hemoglobin < 13.0).astype(int)
    tg = np.exp(rng_lab.normal(np.log(125) + 0.03 * (bmi - 26.5) + 0.25 * diabetes, 0.4))
    hdl = np.clip(rng_lab.normal(52 + 7 * female - 0.9 * (bmi - 26.5), 13), 20, 120)
    hypertension = (rng_lab.random(n) < _sigmoid(0.2 + 0.06 * (systolic - 130) + 0.03 * (age - 75)
                                                 + 0.6 * diabetes)).astype(int)
    atypical = (rng_lab.random(n) < 0.03).astype(int)

    ln_ptau = (PTAU_BASE
               + PTAU_AMY_MAX * _sigmoid((load - PTAU_AMY_MID) / PTAU_AMY_WIDTH)
               + 0.003 * np.clip(load - 60, 0, None)
               + PTAU_TAU * tau
               + 0.007 * (age - 72)
               + kidney_effect(egfr)
               + ANEMIA_PTAU * anemia
               - 0.022 * (bmi - 26.5)
               + HTN_PTAU * hypertension + VASC_PTAU * np.maximum(stroke, cvd)
               + rng.normal(0, PTAU_SD, n))
    extra = _extended_factors(n, seed, age, female, egfr, bmi, tg, stage, amyloid, tau, stroke, cvd,
                              hypertension, diabetes, effects) if extended else None
    if extra is not None:
        ln_ptau = ln_ptau + extra.pop("_ln_ptau_shift")
    ratio = np.clip(0.100 - 0.016 * _sigmoid((load - 15) / 8) + rng.normal(0, 0.008, n), 0.04, 0.16)
    ab40 = np.clip(rng.normal(300 + 1.5 * np.clip(70 - egfr, 0, None), 45, n), 120, 700)

    return pd.DataFrame({
        "age": np.round(age).astype(int),
        "sex": np.where(female == 1, "F", "M"),
        "education_years": np.clip(np.round(rng.normal(8, 4, n)), 0, 20).astype(int),
        "bmi": np.round(bmi, 1),
        "egfr": np.round(egfr).astype(int),
        "creatinine": np.round(creat, 2),
        "triglycerides": np.round(tg).astype(int),
        "hemoglobin": np.round(hemoglobin, 1),
        "ldl": np.round(ldl).astype(int),
        "hdl": np.round(hdl).astype(int),
        "hypertension": hypertension,
        "diabetes": diabetes.astype(int),
        "stroke": stroke,
        "cardiovascular_disease": cvd,
        "sleep_apnea": (rng_lab.random(n) < 0.08).astype(int),
        "weight_loss": (rng_lab.random(n) < _sigmoid(-2.7 + 0.8 * amyloid * (stage == 2))).astype(int),
        "clinical_stage": np.array(["SCD", "MCI", "Dementia"])[stage],
        "atypical_features": atypical,
        "ptau217": np.round(np.exp(ln_ptau), 3),
        "ptau181": np.nan,
        "gfap": np.nan,
        "ab42": np.round(ratio * ab40, 1),
        "ab40": np.round(ab40, 1),
        "apoe4": apoe4,
        "moca": np.nan,
        "mta_score": np.nan,
        "amyloid_load": np.round(load, 1),            # not given to the model (for analyses only)
        "lp_result": np.where(lp_positive == 1, "Positive", "Negative"),
        **({} if extra is None else extra),
    })


CALIBRATION_TARGETS_V2 = {
    "auc_ptau217": (0.95, "Lumipulse plasma p-tau217 vs CSF, memory clinic (Alzheimer's Res Ther 2025)"),
    "grey_zone_fraction": ("0.15-0.35", "intermediate zone with two cut-offs (several Lumipulse studies)"),
    "npv_below_lower_cutoff": ("~0.95", "two-cut-off design: lower cut-off set for ~95 % NPV"),
    "ppv_above_upper_cutoff": ("~0.95", "two-cut-off design: upper cut-off set for ~95 % PPV"),
    "ptau217_ratio_anemia": (1.40, "optimal p-tau217 cut-off with anaemia 0.595 vs 0.425 pg/mL (JAMA Neurol 2026)"),
    "ptau217_ratio_egfr_30_45_vs_60plus": (">1 (threshold)", "CKD raises p-tau217, little effect above eGFR ~60 "
                                                             "(Mielke 2022; Pichet Binette 2023)"),
    "csf_vs_amyloid_state_discordance": ("0.05-0.10", "CSF vs amyloid-PET discordance in memory clinics"),
}


def calibration_report_v2(n: int = 30000, seed: int = 0, lower: float = 0.14, upper: float = 0.43) -> pd.DataFrame:
    """Compare the version-2 population (with real CHS covariates) with the literature targets."""
    from sklearn.metrics import roc_auc_score

    from .synthetic import _chs_cache, real_clinical_base

    pop = simulate_memory_clinic_v2(n, seed, real_clinical_base(n, seed, chs=_chs_cache()))
    y = (pop["lp_result"] == "Positive").to_numpy()
    p = pop["ptau217"].to_numpy()
    neg = ~y
    anemic = np.where(pop["sex"] == "F", pop["hemoglobin"] < 12, pop["hemoglobin"] < 13)
    egfr = pop["egfr"].to_numpy()
    simulated = {
        "auc_ptau217": roc_auc_score(y, p),
        "grey_zone_fraction": float(((p >= lower) & (p <= upper)).mean()),
        "npv_below_lower_cutoff": float(neg[p < lower].mean()),
        "ppv_above_upper_cutoff": float(y[p > upper].mean()),
        "ptau217_ratio_anemia": float(np.median(p[neg & anemic]) / np.median(p[neg & ~anemic])),
        "ptau217_ratio_egfr_30_45_vs_60plus": float(np.median(p[neg & (egfr >= 30) & (egfr < 45)])
                                                    / np.median(p[neg & (egfr >= 60)])),
        "csf_vs_amyloid_state_discordance": float(((pop["amyloid_load"] > 18).to_numpy() != y).mean()),
    }
    return pd.DataFrame([{"quantity": k, "published": CALIBRATION_TARGETS_V2[k][0], "simulated": round(v, 3),
                          "source": CALIBRATION_TARGETS_V2[k][1]} for k, v in simulated.items()])


# ---------------------------------------------------------------------------
# Version 3: extra routine factors (effect sizes scaled by ``effects``)
# ---------------------------------------------------------------------------
V3_EFFECTS = {
    # log-scale effects on plasma p-tau217, independent of amyloid
    "thyroid": np.log(1.10),        # thyroid disease: higher p-tau217 (weak, inconsistent evidence; ASSUMED size)
    "osa": np.log(1 / 1.13),        # obstructive sleep apnoea: lower p-tau217 (Shir 2026; ASSUMED size)
    "tg": -0.08,                    # per log unit of triglycerides: modest inverse association (ASSUMED size)
    "hyperfiltration": -0.006,      # per mL/min above eGFR 90: faster clearance, lower p-tau217 (ASSUMED)
}


def _extended_factors(n, seed, age, female, egfr, bmi, tg, stage, amyloid, tau, stroke, cvd, hypertension,
                      diabetes, effects: float = 1.0) -> dict:
    """Routine memory-clinic factors for version 3, plus their effect on log p-tau217.

    * Thyroid (dementia blood screen): TSH log-normal (median about 1.9 mIU/L). Known thyroid disease
      (hypothyroidism treated or not, or hyperthyroidism) in about 12 % (women and older people more).
    * Sleep apnoea: more with higher BMI and in men (about 10-15 %), lowers p-tau217.
    * MRI (often unavailable): MTA score 0-4 (Scheltens; rises with age, clinical stage and tau in
      amyloid-positive patients: Wahlund 2017, Persson 2017). Fazekas 0-3 (age, hypertension,
      diabetes, stroke).
    * MMSE (routine): by clinical stage, about 1 point lower in amyloid-positive patients with tau, and
      lower with age.
    """
    rng = np.random.default_rng(seed + 3_000_017)
    e = float(effects)
    tsh = np.exp(rng.normal(np.log(1.9) + 0.004 * (age - 72), 0.45, n))
    thyroid = ((rng.random(n) < _sigmoid(-2.4 + 0.8 * female + 0.02 * (age - 72))) | (tsh > 6) | (tsh < 0.3))
    thyroid = thyroid.astype(int)
    osa = (rng.random(n) < _sigmoid(-2.4 + 0.12 * (bmi - 26.5) + 0.6 * (1 - female))).astype(int)
    tau_pos = np.clip(tau, 0, None) * amyloid
    mta = np.clip(np.round(0.3 + 0.045 * (age - 65) + 0.45 * stage + 0.55 * e * tau_pos
                           + rng.normal(0, 0.6, n)), 0, 4)
    fazekas = np.clip(np.round(0.6 + 0.035 * (age - 72) + 0.5 * hypertension + 0.3 * diabetes + 0.6 * stroke
                               + 0.2 * cvd + 0.01 * np.clip(70 - egfr, 0, None) + rng.normal(0, 0.7, n)), 0, 3)
    mmse = np.clip(np.round(np.select([stage == 0, stage == 1], [28.6, 26.2], 21.0) - 0.04 * (age - 72)
                            - 1.0 * e * tau_pos + rng.normal(0, 1.7, n)), 0, 30)
    mri_available = rng.random(n) < 0.55                      # MRI rating present in about half of patients
    shift = (e * V3_EFFECTS["thyroid"] * thyroid + e * V3_EFFECTS["osa"] * osa
             + e * V3_EFFECTS["tg"] * np.log(tg / 125)
             + e * V3_EFFECTS["hyperfiltration"] * np.clip(egfr - 90, 0, None))
    return {
        "tsh": np.round(tsh, 2),
        "thyroid_disease": thyroid,
        "sleep_apnea": osa,
        "mta_score": np.where(mri_available, mta, np.nan),
        "fazekas": np.where(mri_available, fazekas, np.nan),
        "mmse": mmse,
        "_ln_ptau_shift": shift,
    }


def simulate_memory_clinic_v3(n: int, seed: int = 0, real_base: pd.DataFrame | None = None,
                              effects: float = 1.0) -> pd.DataFrame:
    """Version 3 = version 2 plus thyroid, MRI, MMSE, sleep apnoea and metabolic factors."""
    return simulate_memory_clinic_v2(n, seed, real_base, extended=True, effects=effects)
