"""The default ("out of the box") model and the dataset it is trained on.

config.yaml -> default_model:
    training_file  the preserved training dataset (a file in the repository)
    model_dir      where the shipped model lives (committed to the repository)

A file ``manifest.json`` next to the model records exactly which dataset was used
(path, SHA-256 fingerprint, number of patients) and the library versions, so the
provenance of the shipped model can always be checked.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from .config import PROJECT_ROOT, load_config
from .data import load_patient_file
from .model import load_bundle, save_bundle, train_model
from .report import write_report


def _paths(cfg: dict) -> tuple[Path, Path]:
    section = cfg.get("default_model") or {}
    data = PROJECT_ROOT / section.get("training_file", "data/default_training/synthetic_training_dataset.xlsx")
    model = PROJECT_ROOT / section.get("model_dir", "models/default")
    return data, model


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def train_default(cfg: dict | None = None, progress=None, nested: bool | None = None) -> dict:
    """Train the default model from the configured dataset and write the manifest."""
    cfg = cfg or load_config()
    data_path, model_dir = _paths(cfg)
    if not data_path.exists():
        raise FileNotFoundError(f"Default training dataset not found: {data_path}")
    prepared = load_patient_file(data_path, cfg, require_label=True)
    bundle = train_model(prepared, cfg, nested=nested, progress=progress, source_name=data_path.name)
    save_bundle(bundle, model_dir)
    write_report(bundle, model_dir)
    manifest = {
        "trained": bundle["created"],
        "training_file": str(data_path.relative_to(PROJECT_ROOT)),
        "training_file_sha256": file_sha256(data_path),
        "rows_in_file": prepared.n,
        "training_patients": bundle["report"]["cohort"]["n_train"],
        "thresholds": bundle["thresholds"],
        "features": bundle["features"],
        "versions": bundle["versions"],
        "written": dt.datetime.now().isoformat(timespec="seconds"),
    }
    (model_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return bundle


def default_status(cfg: dict | None = None) -> dict:
    """What is the state of the shipped model? Never raises."""
    cfg = cfg or load_config()
    data_path, model_dir = _paths(cfg)
    status = {"data_path": data_path, "model_dir": model_dir, "data_exists": data_path.exists(),
              "model_exists": (model_dir / "model.joblib").exists(), "loadable": False,
              "manifest": None, "dataset_matches": None, "error": None}
    manifest_path = model_dir / "manifest.json"
    if manifest_path.exists():
        status["manifest"] = json.loads(manifest_path.read_text(encoding="utf-8"))
        if status["data_exists"]:
            status["dataset_matches"] = file_sha256(data_path) == status["manifest"]["training_file_sha256"]
    if status["model_exists"]:
        try:
            load_bundle(model_dir)
            status["loadable"] = True
        except Exception as exc:  # e.g. incompatible scikit-learn version
            status["error"] = f"{type(exc).__name__}: {exc}"
    return status
