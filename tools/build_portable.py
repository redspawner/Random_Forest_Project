"""Build a portable Windows bundle that needs NOTHING installed on the target computer.

    python tools/build_portable.py                  # -> dist/GreyZoneTriage_portable_win64.zip
    python tools/build_portable.py --lang pt        # -> dist/TriagemZonaCinzenta_portatil_win64.zip (Portuguese)

The bundle contains:
    START_APP.bat           double-click to start the drag-and-drop app
    python/                 a private, complete Windows Python (official build, from NuGet)
                            with all libraries already installed (exact versions of
                            requirements-pinned.txt, so the shipped model loads as-is)
    app/                    the project (code, config.yaml, template, examples, default model)

It can be built on Windows, macOS or Linux: Windows libraries are downloaded as ready-made
"wheels" for the Windows 64-bit platform. Internet is needed only while building.
"""

from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY_VERSION = "3.13.17"            # must match the Python minor version of requirements-pinned.txt
NUGET = "https://api.nuget.org/v3-flatcontainer/python/{v}/python.{v}.nupkg"
EXCLUDE_TOP = {".github", "tools", "tests", "dist", ".venv", "pytest.ini", "install.sh", "run_app.sh",
               "install.bat", "run_app.bat"}

START_BAT = r"""@echo off
REM Grey-zone AD triage - portable version. Nothing needs to be installed.
cd /d "%~dp0app"
echo Grey-zone AD triage - portable version
echo The browser opens by itself as soon as the app is ready (first start: up to 1 minute).
"%~dp0python\python.exe" run_app.py
pause
"""

TRAIN_BAT = r"""@echo off
REM Re-train the default model from the dataset named in app\config.yaml (default_model).
cd /d "%~dp0app"
"%~dp0python\python.exe" train.py --default
pause
"""

START_BAT_PT = r"""@echo off
chcp 65001 >nul
REM Triagem DA na zona cinzenta - versão portátil. Não é preciso instalar nada.
cd /d "%~dp0app"
echo Triagem DA na zona cinzenta - versão portátil
echo O navegador abre sozinho assim que a aplicação estiver pronta (primeiro arranque: até 1 minuto).
"%~dp0python\python.exe" run_app.py
pause
"""

TRAIN_BAT_PT = r"""@echo off
chcp 65001 >nul
REM Volta a treinar o modelo padrão com o conjunto de dados indicado em app\config.yaml (default_model).
cd /d "%~dp0app"
"%~dp0python\python.exe" train.py --default
pause
"""

README_TXT_PT = """Triagem DA na zona cinzenta (Random Forest) - VERSÃO PORTÁTIL PARA WINDOWS
===========================================================================

1. Extraia a pasta completa (botão direito no .zip -> Extrair tudo). Não a execute a partir
   de dentro do zip. Um caminho curto, como C:\\TriagemZonaCinzenta, funciona melhor.
2. Faça duplo clique em INICIAR_APLICACAO.bat. Espere por
   "==> A aplicação está pronta: http://127.0.0.1:8501"; o navegador abre sozinho
   (o primeiro arranque pode demorar até um minuto).
   (Se o Windows SmartScreen avisar: "Mais informações" -> "Executar mesmo assim".)
3. Mantenha a janela preta aberta enquanto usa a aplicação; feche-a para parar.
   Se disser que a porta 8501 está ocupada, há outra cópia aberta: a aplicação usa
   simplesmente a porta seguinte (ou feche a outra janela preta / termine "python.exe"
   no Gestor de Tarefas).

Nada é instalado no computador e nada é enviado pela internet:
o Python e todas as bibliotecas estão dentro da pasta "python".

Outros ficheiros:
  RETREINAR_MODELO_PADRAO.bat  volta a treinar o modelo padrão (app\\config.yaml -> default_model)
  app\\examples\\               ficheiros de exemplo (treino / novos doentes / resultado)
  app\\config.yaml              definições (language: pt = português, en = inglês)
  app\\README.md                documentação técnica completa (em inglês)

O modelo de ficheiro Excel em português descarrega-se no separador
"Modelo de ficheiro e ajuda" da aplicação. Os ficheiros com nomes de colunas em
inglês também são aceites.

Protótipo de investigação para fins de ensino - não é um dispositivo médico.
"""

README_TXT = """Grey-zone AD triage (Random Forest) - PORTABLE WINDOWS VERSION
==============================================================

1. Extract the whole folder (right-click the .zip -> Extract All). Do not run it from
   inside the zip. A short path such as C:\\GreyZoneTriage works best.
2. Double-click START_APP.bat. Wait for "==> The app is ready: http://127.0.0.1:8501";
   the browser then opens by itself (first start can take up to a minute).
   (If Windows SmartScreen warns: "More info" -> "Run anyway".)
3. Keep the black window open while using the app; close it to stop.
   If it says port 8501 is busy, another copy is still open: it simply uses the next port
   (or close the other black window / end "python.exe" in Task Manager).

Nothing is installed on the computer and nothing is sent over the internet:
Python and all libraries are inside the "python" folder.

Other files:
  RETRAIN_DEFAULT_MODEL.bat  re-train the default model (app\\config.yaml -> default_model)
  app\\examples\\             example training / new-patient / output files
  app\\README.md              full documentation;  app\\docs\\PROJECT_GUIDE.md  step-by-step guide

Research prototype for teaching purposes - not a medical device.
"""


LANGS = {
    "en": {"folder": "GreyZoneTriage", "zip": "GreyZoneTriage_portable_win64",
           "start": ("START_APP.bat", START_BAT), "train": ("RETRAIN_DEFAULT_MODEL.bat", TRAIN_BAT),
           "readme": ("README_FIRST.txt", README_TXT)},
    "pt": {"folder": "TriagemZonaCinzenta", "zip": "TriagemZonaCinzenta_portatil_win64",
           "start": ("INICIAR_APLICACAO.bat", START_BAT_PT), "train": ("RETREINAR_MODELO_PADRAO.bat", TRAIN_BAT_PT),
           "readme": ("LEIA_PRIMEIRO.txt", README_TXT_PT)},
}


def run(cmd: list[str]) -> None:
    print("  $", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def download(url: str) -> bytes:
    print(f"  downloading {url}", flush=True)
    with urllib.request.urlopen(url, timeout=300) as response:
        return response.read()


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
        files = [Path(line) for line in out.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):      # not a git checkout: copy everything sensible
        files = [p.relative_to(ROOT) for p in ROOT.rglob("*") if p.is_file()]
    return [f for f in files if f.parts[0] not in EXCLUDE_TOP and "__pycache__" not in f.parts]


def set_language(app: Path, lang: str) -> None:
    """Switch the bundled app to another interface language."""
    config = app / "config.yaml"
    text = config.read_text(encoding="utf-8")
    if "\nlanguage: en\n" not in text:
        raise SystemExit("config.yaml has no 'language: en' line")
    config.write_text(text.replace("\nlanguage: en\n", f"\nlanguage: {lang}\n"), encoding="utf-8")
    # The figures and text report of the shipped model are regenerated in the new language the
    # first time the "Model report" tab is opened.
    for model in (app / "models").glob("default*"):          # the shipped model of every type
        for item in [*model.glob("*.png"), model / "report.md"]:
            item.unlink(missing_ok=True)
    print(f"  interface language: {lang}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--python", default=PY_VERSION, help=f"Windows Python version (default {PY_VERSION})")
    parser.add_argument("--out", default=str(ROOT / "dist"), help="output folder (default dist/)")
    parser.add_argument("--no-zip", action="store_true", help="leave the folder, do not create the .zip")
    parser.add_argument("--lang", choices=sorted(LANGS), default="en",
                        help="interface language of the bundle: en (default) or pt (European Portuguese)")
    args = parser.parse_args()
    names = LANGS[args.lang]

    out = Path(args.out)
    bundle = out / names["folder"]
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / "python").mkdir(parents=True)

    print("1/4 Windows Python", args.python)
    with zipfile.ZipFile(io.BytesIO(download(NUGET.format(v=args.python)))) as nupkg:
        for member in nupkg.namelist():
            if member.startswith("tools/") and not member.endswith("/"):
                target = bundle / "python" / member[len("tools/"):]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(nupkg.read(member))

    print("2/4 libraries (Windows 64-bit wheels, exact pinned versions)")
    pins = [line for line in (ROOT / "requirements-pinned.txt").read_text().splitlines()
            if line.strip() and not line.startswith("#") and not line.lower().startswith("pytest")]
    req = out / "_portable_requirements.txt"
    req.write_text("\n".join(pins) + "\n")
    major_minor = ".".join(args.python.split(".")[:2])
    run([sys.executable, "-m", "pip", "install", "--quiet", "--no-compile", "--disable-pip-version-check",
         "--target", str(bundle / "python" / "Lib" / "site-packages"),
         "--platform", "win_amd64", "--python-version", major_minor, "--implementation", "cp",
         "--only-binary=:all:", "-r", str(req)])
    req.unlink()

    print("3/4 project files")
    files = tracked_files()
    for rel in files:
        dest = bundle / "app" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)
    print(f"  {len(files)} files")
    for key in ("start", "train"):
        name, text = names[key]
        (bundle / name).write_text(text.replace("\n", "\r\n"), encoding="utf-8")     # UTF-8 without BOM
    name, text = names["readme"]
    (bundle / name).write_text(text.replace("\n", "\r\n"), encoding="utf-8-sig")
    if args.lang != "en":
        set_language(bundle / "app", args.lang)

    if args.no_zip:
        print(f"Done: {bundle}")
        return
    print("4/4 zip")
    archive = shutil.make_archive(str(out / names["zip"]), "zip", root_dir=out, base_dir=names["folder"])
    size = Path(archive).stat().st_size / 1e6
    print(f"Done: {archive}  ({size:.0f} MB)")


if __name__ == "__main__":
    main()
