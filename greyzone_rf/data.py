"""Reading, validating and cleaning patient files (Excel or CSV).

The functions here never silently change a value. Every correction (unit
brackets ignored, comma decimals, censored values, computed eGFR, ...) is
recorded as a note, and every implausible value is recorded as an issue.
"""

from __future__ import annotations

import io
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO

import numpy as np
import pandas as pd

from .config import FeatureSpec, feature_specs, normalize_name

MISSING_TOKENS = {"", "na", "n/a", "nan", "none", "null", "-", "--", "nd", "missing", "?", "nr"}
SEX_VALUES = {
    "f": 1, "female": 1, "feminino": 1, "fem": 1, "mulher": 1, "woman": 1,
    "m": 0, "male": 0, "masculino": 0, "masc": 0, "homem": 0, "man": 0,
}
BINARY_VALUES = {
    "1": 1, "yes": 1, "y": 1, "sim": 1, "s": 1, "true": 1, "positive": 1, "positivo": 1,
    "0": 0, "no": 0, "n": 0, "nao": 0, "false": 0, "negative": 0, "negativo": 0,
}
LABEL_VALUES = {
    "positive": 1, "pos": 1, "positivo": 1, "1": 1, "yes": 1, "sim": 1, "+": 1,
    "ad+": 1, "a+": 1, "amyloid+": 1, "ad": 1, "true": 1,
    "negative": 0, "neg": 0, "negativo": 0, "0": 0, "no": 0, "nao": 0, "-": 0,
    "ad-": 0, "a-": 0, "amyloid-": 0, "nonad": 0, "non-ad": 0, "false": 0,
}
APOE_GENOTYPE = re.compile(r"^e?([234])\s*/\s*e?([234])$")


class DataError(ValueError):
    """Raised when a file cannot be used at all (e.g. no p-tau217 column)."""


@dataclass
class PreparedData:
    """A patient table after parsing and checking."""

    ids: list[str]
    table: pd.DataFrame                 # one numeric column per variable (NaN = missing)
    labels: pd.Series | None            # 1 = LP positive, 0 = LP negative, NaN = unknown
    raw: pd.DataFrame                   # the file as read (empty rows removed)
    row_issues: list[list[str]]         # blocking problems (implausible / invalid values)
    row_notes: list[list[str]]          # non-blocking remarks
    messages: list[str] = field(default_factory=list)          # file-level warnings
    columns_found: dict[str, str] = field(default_factory=dict)  # variable -> header in file
    unrecognized_columns: list[str] = field(default_factory=list)
    source: dict | None = None        # original file (bytes, sheet, row numbers) when read from disk/upload

    @property
    def n(self) -> int:
        return len(self.ids)


# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------
def read_table(source: str | Path | BinaryIO | bytes, filename: str | None = None) -> pd.DataFrame:
    """Read an .xlsx/.xlsm or .csv file into a DataFrame (all cells as objects).

    For Excel workbooks the sheet called "Patients" is used if present,
    otherwise the first sheet.
    """
    if isinstance(source, (str, Path)):
        filename = filename or str(source)
        with open(source, "rb") as handle:
            content = handle.read()
    elif isinstance(source, bytes):
        content = source
    else:
        filename = filename or getattr(source, "name", None)
        content = source.read()
    if not filename:
        raise DataError("Cannot determine the file type (missing file name).")

    suffix = Path(filename).suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        workbook = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
        sheet = next((s for s in workbook.sheet_names if s.strip().lower() == "patients"),
                     workbook.sheet_names[0])
        df = pd.read_excel(workbook, sheet_name=sheet, dtype=object)
        source = {"kind": "excel", "sheet": sheet, "content": content}
    elif suffix in {".csv", ".txt"}:
        text = content.decode("utf-8-sig", errors="replace")
        first_line = text.splitlines()[0] if text else ""
        sep = ";" if first_line.count(";") > first_line.count(",") else ","
        df = pd.read_csv(io.StringIO(text), sep=sep, dtype=object)
        source = {"kind": "csv", "sheet": None, "content": content}
    elif suffix == ".xls":
        raise DataError("Old .xls format is not supported: open it in Excel and 'Save as' .xlsx.")
    else:
        raise DataError(f"Unsupported file type '{suffix}'. Use .xlsx or .csv.")

    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df = df.loc[:, [not str(c).startswith("Unnamed") for c in df.columns]]
    # Excel/CSV row number of each patient (header = row 1), used to annotate the original file
    source["rows"] = [int(i) + 2 for i in df.index]
    df = df.reset_index(drop=True)
    df.attrs["source"] = source
    return df


# ---------------------------------------------------------------------------
# Cell parsers: return (value, note, error)
# ---------------------------------------------------------------------------
def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if value is pd.NA or value is pd.NaT:
        return True
    return isinstance(value, str) and value.strip().lower() in MISSING_TOKENS


def _text_key(value: Any) -> str:
    text = str(value).replace("ε", "e").replace("Ɛ", "e")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.strip().lower().replace(" ", "")


def parse_number(value: Any) -> tuple[float, str | None, str | None]:
    if _is_blank(value):
        return np.nan, None, None
    if isinstance(value, bool):
        return np.nan, None, f"invalid number '{value}'"
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value), None, None
    text = str(value).strip().replace(" ", "").replace(" ", "")
    note = None
    if text[:1] in "<>":
        note = f"censored value '{text}' used as {text[1:]}"
        text = text[1:].lstrip("=")
    if "," in text and "." not in text:          # Portuguese decimal comma: 0,25
        text = text.replace(",", ".")
    try:
        number = float(text)
    except ValueError:
        return np.nan, None, f"invalid number '{value}'"
    if not math.isfinite(number):
        return np.nan, None, f"invalid number '{value}'"
    return number, note, None


def parse_sex(value: Any) -> tuple[float, str | None, str | None]:
    if _is_blank(value):
        return np.nan, None, None
    key = _text_key(value)
    if key in SEX_VALUES:
        return float(SEX_VALUES[key]), None, None
    return np.nan, None, f"invalid sex '{value}' (use M or F)"


def parse_binary(value: Any) -> tuple[float, str | None, str | None]:
    if _is_blank(value):
        return np.nan, None, None
    key = _text_key(value)
    if key in {"1.0", "0.0"}:
        key = key[0]
    if key in BINARY_VALUES:
        return float(BINARY_VALUES[key]), None, None
    return np.nan, None, f"invalid yes/no value '{value}'"


def parse_apoe4(value: Any) -> tuple[float, str | None, str | None]:
    if _is_blank(value):
        return np.nan, None, None
    if isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool):
        if float(value) in (0.0, 1.0, 2.0):
            return float(value), None, None
        return np.nan, None, f"invalid APOE e4 allele count '{value}' (0, 1 or 2)"
    key = _text_key(value).replace("apoe", "")
    if key in {"0", "1", "2"}:
        return float(key), None, None
    match = APOE_GENOTYPE.match(key)
    if match:
        return float([match.group(1), match.group(2)].count("4")), None, None
    if key in {"carrier", "yes", "sim", "positive", "positivo", "e4+"}:
        return 1.0, "APOE e4 'carrier' coded as 1 allele", None
    if key in {"noncarrier", "non-carrier", "no", "nao", "negative", "negativo", "e4-"}:
        return 0.0, None, None
    return np.nan, None, f"invalid APOE value '{value}' (use 0/1/2 or e.g. E3/E4)"


PARSERS = {"numeric": parse_number, "sex": parse_sex, "binary": parse_binary, "apoe4": parse_apoe4}


def parse_label(value: Any) -> float:
    if _is_blank(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool):
        return float(value) if float(value) in (0.0, 1.0) else np.nan
    return float(LABEL_VALUES[_text_key(value)]) if _text_key(value) in LABEL_VALUES else np.nan


# ---------------------------------------------------------------------------
# Derived variables
# ---------------------------------------------------------------------------
def anemia_who(hemoglobin_g_dl, is_female):
    """WHO anaemia definition: haemoglobin < 12 g/dL (women) or < 13 g/dL (men). NaN if unknown."""
    hb = np.asarray(hemoglobin_g_dl, dtype=float)
    female = np.asarray(is_female, dtype=float)
    out = np.where(female == 1, hb < 12.0, hb < 13.0).astype(float)
    out[np.isnan(hb) | np.isnan(female)] = np.nan
    return out


def ckd_epi_2021(creatinine_mg_dl, age, is_female):
    """2021 CKD-EPI creatinine equation (race-free), mL/min/1.73 m²."""
    scr = np.asarray(creatinine_mg_dl, dtype=float)
    age = np.asarray(age, dtype=float)
    female = np.asarray(is_female, dtype=float) == 1
    kappa = np.where(female, 0.7, 0.9)
    alpha = np.where(female, -0.241, -0.302)
    ratio = scr / kappa
    return (142.0 * np.minimum(ratio, 1.0) ** alpha * np.maximum(ratio, 1.0) ** -1.200
            * 0.9938 ** age * np.where(female, 1.012, 1.0))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def _match_columns(df: pd.DataFrame, cfg: dict) -> tuple[dict[str, str], list[str], list[str]]:
    lookup: dict[str, str] = {}
    cols = cfg["columns"]
    for alias in [cols["patient_id"], *cols.get("patient_id_aliases", [])]:
        lookup[normalize_name(alias)] = "__id__"
    for alias in [cols["label"], *cols.get("label_aliases", [])]:
        lookup[normalize_name(alias)] = "__label__"
    for spec in feature_specs(cfg):
        for alias in [spec.name, *spec.aliases]:
            lookup[normalize_name(alias)] = spec.name

    found: dict[str, str] = {}
    unrecognized, messages = [], []
    for header in df.columns:
        target = lookup.get(normalize_name(header))
        if target is None:
            if not str(header).startswith("AI "):          # columns added by a previous prediction run
                unrecognized.append(str(header))
        elif target in found:
            messages.append(f"Column '{header}' ignored: '{found[target]}' already provides '{target}'.")
        else:
            found[target] = header
    return found, unrecognized, messages


def _check_range(spec: FeatureSpec, value: float) -> str | None:
    if np.isnan(value):
        return None
    if spec.min is not None and value < spec.min:
        return f"{spec.name} = {value:g} below plausible minimum {spec.min:g} {spec.unit}".strip()
    if spec.max is not None and value > spec.max:
        return f"{spec.name} = {value:g} above plausible maximum {spec.max:g} {spec.unit}".strip()
    return None


def prepare_table(df: pd.DataFrame, cfg: dict, require_label: bool = False) -> PreparedData:
    """Parse and check a raw patient table according to the configuration."""
    if df.empty:
        raise DataError("The file contains no patient rows.")
    found, unrecognized, messages = _match_columns(df, cfg)
    specs = feature_specs(cfg)
    n = len(df)

    if "ptau217" not in found:
        raise DataError("Required column 'ptau217' (plasma p-tau217, pg/mL) was not found.")
    if require_label and "__label__" not in found:
        raise DataError(
            f"Training needs the lumbar-puncture result column '{cfg['columns']['label']}' "
            "(Positive / Negative)."
        )

    # Patient identifiers
    if "__id__" in found:
        ids = []
        for i, value in enumerate(df[found["__id__"]]):
            if _is_blank(value):
                ids.append(f"row_{i + 2}")
                messages.append(f"Excel row {i + 2}: missing patient_id, using 'row_{i + 2}'.")
            else:
                text = str(value).strip()
                ids.append(text[:-2] if re.fullmatch(r"\d+\.0", text) else text)
    else:
        ids = [f"row_{i + 2}" for i in range(n)]
        messages.append("No 'patient_id' column found: rows are identified by their Excel row number.")
    duplicated = sorted({x for x in ids if ids.count(x) > 1})
    if duplicated:
        messages.append(f"Duplicated patient_id values: {', '.join(duplicated[:10])}.")

    row_issues: list[list[str]] = [[] for _ in range(n)]
    row_notes: list[list[str]] = [[] for _ in range(n)]
    table = pd.DataFrame(index=range(n))

    # 1) Read every variable present in the file
    for spec in specs:
        if spec.name not in found:
            table[spec.name] = np.nan
            continue
        parser = PARSERS[spec.type]
        values = np.full(n, np.nan)
        for i, cell in enumerate(df[found[spec.name]]):
            value, note, error = parser(cell)
            if error:
                row_issues[i].append(f"{spec.name}: {error}")
                continue
            if note:
                row_notes[i].append(f"{spec.name}: {note}")
            problem = _check_range(spec, value)
            if problem:
                row_issues[i].append(problem)
                continue
            values[i] = value
        table[spec.name] = values

    # 2) Fill computed variables where they are blank
    for spec in specs:
        if spec.compute is None:
            continue
        target = table[spec.name].to_numpy(dtype=float).copy()
        if spec.compute == "anemia_who":
            computed = anemia_who(table["hemoglobin"], table["sex"])
            note = None
        elif spec.compute == "ckd_epi_2021":
            computed = ckd_epi_2021(table["creatinine"], table["age"], table["sex"])
            computed[table["sex"].isna().to_numpy() | table["age"].isna().to_numpy()] = np.nan
            note = "eGFR computed from creatinine (CKD-EPI 2021)"
        else:
            num, den = spec.ratio_parts
            with np.errstate(divide="ignore", invalid="ignore"):
                computed = table[num].to_numpy(float) / table[den].to_numpy(float)
            computed[~np.isfinite(computed)] = np.nan
            note = None
        fill = np.isnan(target) & ~np.isnan(computed)
        target[fill] = computed[fill]
        for i in np.flatnonzero(fill):
            if note:
                row_notes[i].append(note)
            problem = _check_range(spec, target[i])
            if problem:
                row_issues[i].append(problem + " (computed)")
                target[i] = np.nan
        table[spec.name] = target

    # 3) p-tau217 is mandatory for every patient
    for i, value in enumerate(table["ptau217"]):
        if np.isnan(value) and not any(s.startswith("ptau217") for s in row_issues[i]):
            row_issues[i].append("ptau217 missing (required)")

    # 4) Absent / unrecognised columns
    absent = [s.name for s in specs if s.use_as_feature and s.compute is None and s.name not in found]
    if absent:
        messages.append("Variables not present in this file (treated as missing): " + ", ".join(absent) + ".")
    if unrecognized:
        messages.append(
            "Columns not used (not defined in config.yaml): " + ", ".join(unrecognized)
            + ". To use a new variable, add it to the 'features' list in config.yaml and retrain."
        )

    labels = None
    if "__label__" in found:
        labels = pd.Series([parse_label(v) for v in df[found["__label__"]]], dtype=float)
        bad = [(ids[i], v) for i, v in enumerate(df[found["__label__"]])
               if not _is_blank(v) and np.isnan(labels[i])]
        for pid, v in bad[:20]:
            messages.append(f"Patient {pid}: lumbar-puncture result '{v}' not understood (use Positive/Negative).")
        if require_label and labels.notna().sum() == 0:
            raise DataError("No usable lumbar-puncture results (Positive/Negative) were found.")

    columns_found = {k: str(v) for k, v in found.items() if not k.startswith("__")}
    return PreparedData(source=df.attrs.get("source"), ids=ids, table=table, labels=labels, raw=df,
                        row_issues=row_issues,
                        row_notes=row_notes, messages=messages, columns_found=columns_found,
                        unrecognized_columns=unrecognized)


def load_patient_file(source, cfg: dict, require_label: bool = False, filename: str | None = None) -> PreparedData:
    return prepare_table(read_table(source, filename=filename), cfg, require_label=require_label)


def in_grey_zone(ptau217: np.ndarray | pd.Series, cfg: dict) -> np.ndarray:
    gz = cfg["grey_zone"]
    values = np.asarray(ptau217, dtype=float)
    return (values >= gz["ptau217_lower"]) & (values <= gz["ptau217_upper"])
