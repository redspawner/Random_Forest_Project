"""Loading and validation of ``config.yaml``."""

from __future__ import annotations

import copy
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"

FEATURE_TYPES = {"numeric", "sex", "apoe4", "binary"}
RATIO_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*/\s*([A-Za-z_][A-Za-z0-9_]*)\s*$")


class ConfigError(ValueError):
    """Raised when config.yaml is malformed."""


def normalize_name(name: Any) -> str:
    """Normalise a column header so that small spelling differences still match.

    "p-Tau217 (pg/mL)" -> "ptau217", "Aβ42" -> "ab42", "Idade" -> "idade".
    Text inside brackets (usually units) is ignored.
    """
    text = str(name)
    text = re.sub(r"\(.*?\)|\[.*?\]|\{.*?\}", "", text)
    text = text.replace("β", "b").replace("ß", "b").replace("ε", "e")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", text.lower())


@dataclass
class FeatureSpec:
    name: str
    type: str = "numeric"
    description: str = ""
    unit: str = ""
    min: float | None = None
    max: float | None = None
    example: Any = None
    compute: str | None = None
    use_as_feature: bool = True
    in_template: bool = True
    aliases: list[str] = field(default_factory=list)

    @property
    def ratio_parts(self) -> tuple[str, str] | None:
        if self.compute is None:
            return None
        match = RATIO_PATTERN.match(self.compute)
        return (match.group(1), match.group(2)) if match else None


def feature_specs(cfg: dict) -> list[FeatureSpec]:
    return [FeatureSpec(**spec) for spec in cfg["features"]]


def model_feature_names(cfg: dict) -> list[str]:
    """Variables offered to the model (before dropping columns absent from the data)."""
    return [spec.name for spec in feature_specs(cfg) if spec.use_as_feature]


def load_config(path: str | Path | None = None) -> dict:
    path = Path(path) if path else DEFAULT_CONFIG_PATH
    with open(path, encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict) -> None:
    for section in ("columns", "grey_zone", "decision", "validation", "random_forest", "features"):
        if section not in cfg:
            raise ConfigError(f"config.yaml: missing section '{section}'")

    gz = cfg["grey_zone"]
    if not 0 <= gz["ptau217_lower"] < gz["ptau217_upper"]:
        raise ConfigError("config.yaml: grey_zone.ptau217_lower must be < ptau217_upper")

    dec = cfg["decision"]
    for key in ("target_ppv", "target_npv", "confidence_level"):
        if not 0.5 < float(dec[key]) < 1:
            raise ConfigError(f"config.yaml: decision.{key} must be between 0.5 and 1")
    if not 0 < float(dec["max_missing_fraction"]) <= 1:
        raise ConfigError("config.yaml: decision.max_missing_fraction must be in (0, 1]")

    seen: dict[str, str] = {}
    specs = []
    for raw in cfg["features"]:
        try:
            spec = FeatureSpec(**raw)
        except TypeError as exc:  # unknown key in a feature block
            raise ConfigError(f"config.yaml: invalid feature block {raw}: {exc}") from exc
        if spec.type not in FEATURE_TYPES:
            raise ConfigError(f"config.yaml: feature '{spec.name}' has unknown type '{spec.type}'")
        for alias in [spec.name, *spec.aliases]:
            key = normalize_name(alias)
            if key in seen and seen[key] != spec.name:
                raise ConfigError(
                    f"config.yaml: '{alias}' of feature '{spec.name}' clashes with feature '{seen[key]}'"
                )
            seen[key] = spec.name
        specs.append(spec)

    names = {spec.name for spec in specs}
    if "ptau217" not in names:
        raise ConfigError("config.yaml: a feature named 'ptau217' is required (it defines the grey zone)")
    for spec in specs:
        if spec.compute is None:
            continue
        if spec.compute == "ckd_epi_2021":
            missing = {"creatinine", "age", "sex"} - names
            if missing:
                raise ConfigError(f"config.yaml: ckd_epi_2021 needs features {sorted(missing)}")
            continue
        parts = spec.ratio_parts
        if parts is None:
            raise ConfigError(
                f"config.yaml: feature '{spec.name}': compute must be 'colA / colB' or 'ckd_epi_2021'"
            )
        for part in parts:
            if part not in names:
                raise ConfigError(f"config.yaml: feature '{spec.name}' uses unknown column '{part}'")


def config_snapshot(cfg: dict) -> dict:
    return copy.deepcopy(cfg)
