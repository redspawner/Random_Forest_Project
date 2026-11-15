"""Every interface text has a Portuguese version with the same {placeholders}, and the PT mode works."""

import ast
import os
import string
import subprocess
import sys
from pathlib import Path

from greyzone_rf.i18n_pt import COLUMN_NAMES, PT

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [*ROOT.glob("greyzone_rf/*.py"), ROOT / "app.py", ROOT / "run_app.py", ROOT / "train.py", ROOT / "predict.py"]


def used_texts() -> set[str]:
    texts = set()
    for path in SOURCES:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and getattr(node.func, "id", None) in ("tr", "translate") and node.args
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                texts.add(node.args[0].value)
    return texts


def fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_every_text_is_translated():
    missing = sorted(t for t in used_texts() if t not in PT)
    assert not missing, f"{len(missing)} texts without Portuguese translation: {missing[:5]}"


def test_placeholders_match():
    wrong = [en for en, pt in PT.items() if fields(en) != fields(pt)]
    assert not wrong, wrong


def test_portuguese_mode_end_to_end(tmp_path):
    """Classify the example file and build the template with GREYZONE_LANG=pt (separate process)."""
    code = f"""
import io, pandas as pd
from greyzone_rf.data import load_patient_file
from greyzone_rf.model import load_bundle
from greyzone_rf.predict import annotated_original, predict_prepared, results_to_excel, summarize
from greyzone_rf.template import build_template
from greyzone_rf.report import markdown_report
from greyzone_rf.config import load_config
bundle = load_bundle(r"{ROOT / 'models' / 'default'}")
prepared = load_patient_file(r"{ROOT / 'examples' / 'example_2_new_patients_file.xlsx'}", bundle["config"])
res = predict_prepared(bundle, prepared)
assert set(res["decision"]) <= {{"POSITIVO", "NEGATIVO", "INCONCLUSIVO - referenciar para PL",
                                "NÃO APLICÁVEL - fora da zona cinzenta", "VERIFICAR DADOS"}}, set(res["decision"])
book = pd.ExcelFile(io.BytesIO(annotated_original(res, prepared, bundle)))
assert "Informação da previsão IA" in book.sheet_names
assert "IA decisão" in pd.read_excel(book, sheet_name=book.sheet_names[0]).columns
assert pd.ExcelFile(io.BytesIO(results_to_excel(res, prepared, bundle))).sheet_names[0] == "Resultados"
assert "Relatório de treino" in markdown_report(bundle)
# the Portuguese template must be readable again and give the same patients
tpl = build_template(load_config())
assert pd.ExcelFile(io.BytesIO(tpl)).sheet_names[:3] == ["Doentes", "Dicionário", "Instruções"]
raw = pd.read_excel(r"{ROOT / 'examples' / 'example_2_new_patients_file.xlsx'}")
names = {COLUMN_NAMES!r}
raw = raw.rename(columns={{c: names.get(c, c) for c in raw.columns}}).rename(columns={{"patient_id": names["__id__"]}})
raw.to_excel(r"{tmp_path / 'pt.xlsx'}", sheet_name="Doentes", index=False)
again = predict_prepared(bundle, load_patient_file(r"{tmp_path / 'pt.xlsx'}", bundle["config"]))
assert list(again["decision"]) == list(res["decision"])
print("PT OK", summarize(res))
"""
    env = {**os.environ, "GREYZONE_LANG": "pt"}
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr + out.stdout
    assert "PT OK" in out.stdout
