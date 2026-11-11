import io

import numpy as np
import pandas as pd
import pytest

from greyzone_rf.config import load_config, normalize_name
from greyzone_rf.data import (DataError, ckd_epi_2021, in_grey_zone, parse_apoe4, parse_label, parse_number,
                              parse_sex, prepare_table, read_table)
from greyzone_rf.template import build_template


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def test_normalize_name():
    assert normalize_name("p-Tau217 (pg/mL)") == "ptau217"
    assert normalize_name("Aβ42") == "ab42"
    assert normalize_name(" Idade ") == "idade"


def test_cell_parsers():
    assert parse_number("0,25")[0] == 0.25
    assert parse_number(0.3)[0] == 0.3
    value, note, error = parse_number("<0.03")
    assert value == 0.03 and note and not error
    assert parse_number("abc")[2]
    assert np.isnan(parse_number("NA")[0])
    assert parse_sex("F")[0] == 1 and parse_sex("Masculino")[0] == 0
    assert parse_sex("1")[2]                      # numeric sex codes are ambiguous -> error
    assert parse_apoe4("E3/E4")[0] == 1 and parse_apoe4("ε4/ε4")[0] == 2 and parse_apoe4(0)[0] == 0
    assert parse_label("Positivo") == 1 and parse_label("Negative") == 0 and np.isnan(parse_label("?"))


def test_ckd_epi_2021_reference_values():
    # creatinine 1.0 mg/dL, 60-year-old: ~ 86 (male) and ~ 64 (female) mL/min/1.73m2
    male, female = ckd_epi_2021([1.0, 1.0], [60, 60], [0, 1])
    assert 84 < male < 88
    assert 62 < female < 66


def test_prepare_table_checks_and_derivations(cfg):
    df = pd.DataFrame({
        "Patient_ID": ["A", "B", "C", "D"],
        "Idade": [70, 75, 80, 66],
        "Sexo": ["F", "M", "F", "X"],
        "p-Tau217 (pg/mL)": ["0,20", 0.30, None, 0.25],
        "ab42": [30, 25, 28, 27],
        "ab40": [300, 310, 290, 305],
        "creatinine": [None, 1.0, None, None],
        "MoCA": [25, 34, 22, 20],
        "homocysteine": [10, 11, 12, 13],
        "lp_result": ["Positive", "Negative", "Positive", "Negative"],
    })
    p = prepare_table(df, cfg, require_label=True)
    assert p.ids == ["A", "B", "C", "D"]
    assert p.table.loc[0, "ptau217"] == 0.20
    assert np.isclose(p.table.loc[0, "ab42_ab40_ratio"], 0.1)
    assert np.isclose(p.table.loc[0, "ptau217_ab42_ratio"], 0.2 / 30)
    assert 70 < p.table.loc[1, "egfr"] < 90                    # computed from creatinine
    assert any("moca" in s for s in p.row_issues[1])             # MoCA 34 is implausible
    assert np.isnan(p.table.loc[1, "moca"])
    assert any("ptau217 missing" in s for s in p.row_issues[2])
    assert any("sex" in s for s in p.row_issues[3])
    assert "homocysteine" in p.unrecognized_columns
    assert list(p.labels) == [1, 0, 1, 0]


def test_egfr_not_computed_without_sex_or_age(cfg):
    df = pd.DataFrame({"ptau217": [0.2, 0.2], "creatinine": [1.0, 1.0], "age": [70, None], "sex": [None, "F"]})
    p = prepare_table(df, cfg)
    assert p.table["egfr"].isna().all()


def test_missing_required_columns(cfg):
    with pytest.raises(DataError):
        prepare_table(pd.DataFrame({"age": [70]}), cfg)
    with pytest.raises(DataError):
        prepare_table(pd.DataFrame({"ptau217": [0.2]}), cfg, require_label=True)


def test_semicolon_csv(cfg):
    content = "patient_id;ptau217;age\nP1;0,21;70\nP2;0,35;81\n".encode()
    p = prepare_table(read_table(content, filename="x.csv"), cfg)
    assert list(p.table["ptau217"]) == [0.21, 0.35]


def test_template_round_trip(cfg):
    df = read_table(build_template(cfg), filename="template.xlsx")
    p = prepare_table(df, cfg, require_label=True)     # the example row must be valid
    assert p.n == 1 and not p.row_issues[0]
    assert p.labels[0] == 1
    assert set(p.columns_found) >= {"age", "sex", "ptau217", "egfr", "moca"}


def test_grey_zone(cfg):
    assert list(in_grey_zone([0.10, 0.14, 0.30, 0.43, 0.50], cfg)) == [False, True, True, True, False]


def test_anemia_computed_from_hemoglobin_and_sex(cfg):
    df = pd.DataFrame({"ptau217": [0.2] * 5, "sex": ["F", "F", "M", "M", None],
                       "Hemoglobina (g/dL)": [11.5, 12.5, 12.5, 13.5, 10.0]})
    p = prepare_table(df, cfg)
    assert list(p.table["anemia"][:4]) == [1, 0, 1, 0]
    assert np.isnan(p.table["anemia"][4])          # sex unknown -> not computed


def test_clinical_stage_and_yes_no_parsing(cfg):
    df = pd.DataFrame({"ptau217": [0.2] * 4, "clinical_stage": ["SCD", "DCL", "Demência", "MCI"],
                       "HTA": ["sim", "não", 1, 0], "SAOS": ["yes", "no", None, "1"]})
    p = prepare_table(df, cfg)
    assert list(p.table["clinical_stage"]) == [0, 1, 2, 1]
    assert list(p.table["hypertension"]) == [1, 0, 1, 0]
    assert p.table["sleep_apnea"].tolist()[:2] == [1, 0] and np.isnan(p.table["sleep_apnea"][2])
