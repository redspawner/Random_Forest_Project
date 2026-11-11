"""The shipped default model must exist, load, and match its preserved dataset."""

import json

from greyzone_rf.config import PROJECT_ROOT, load_config
from greyzone_rf.default_model import default_status, file_sha256
from greyzone_rf.model import load_bundle


def test_default_dataset_and_model_are_consistent():
    cfg = load_config()
    status = default_status(cfg)
    assert status["data_exists"], "the preserved default training dataset is missing"
    assert status["model_exists"] and status["loadable"], status["error"]
    manifest = status["manifest"]
    assert manifest["training_file"] == cfg["default_model"]["training_file"]
    assert status["dataset_matches"], "dataset changed since the default model was trained: python train.py --default"
    bundle = load_bundle(status["model_dir"])
    assert bundle["thresholds"] == manifest["thresholds"]
    assert bundle["features"] == manifest["features"]


def test_dataset_card_records_fingerprint():
    cfg = load_config()
    data = PROJECT_ROOT / cfg["default_model"]["training_file"]
    card = (data.parent / "DATASET_CARD.md").read_text(encoding="utf-8")
    assert file_sha256(data) in card
    manifest = json.loads((PROJECT_ROOT / cfg["default_model"]["model_dir"] / "manifest.json").read_text())
    assert manifest["training_file_sha256"] == file_sha256(data)
