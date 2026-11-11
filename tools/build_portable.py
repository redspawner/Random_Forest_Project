"""Build a portable Windows bundle that needs NOTHING installed on the target computer.

    python tools/build_portable.py                  # -> dist/GreyZoneTriage_portable_win64.zip

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
echo Starting the app... your browser will open at http://localhost:8501
echo Keep this window open while you use the app. Close it to stop.
"%~dp0python\python.exe" run_app.py
pause
"""

TRAIN_BAT = r"""@echo off
REM Re-train the default model from the dataset named in app\config.yaml (default_model).
cd /d "%~dp0app"
"%~dp0python\python.exe" train.py --default
pause
"""

README_TXT = """Grey-zone AD triage (Random Forest) - PORTABLE WINDOWS VERSION
==============================================================

1. Extract the whole folder (right-click the .zip -> Extract All). Do not run it from
   inside the zip. A short path such as C:\\GreyZoneTriage works best.
2. Double-click START_APP.bat. Your browser opens at http://localhost:8501.
   (If Windows SmartScreen warns: "More info" -> "Run anyway".)
3. Keep the black window open while using the app; close it to stop.

Nothing is installed on the computer and nothing is sent over the internet:
Python and all libraries are inside the "python" folder.

Other files:
  RETRAIN_DEFAULT_MODEL.bat  re-train the default model (app\\config.yaml -> default_model)
  app\\examples\\             example training / new-patient / output files
  app\\README.md              full documentation;  app\\docs\\PROJECT_GUIDE.md  step-by-step guide

Research prototype for teaching purposes - not a medical device.
"""


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--python", default=PY_VERSION, help=f"Windows Python version (default {PY_VERSION})")
    parser.add_argument("--out", default=str(ROOT / "dist"), help="output folder (default dist/)")
    parser.add_argument("--no-zip", action="store_true", help="leave the folder, do not create the .zip")
    args = parser.parse_args()

    out = Path(args.out)
    bundle = out / "GreyZoneTriage"
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
    (bundle / "START_APP.bat").write_text(START_BAT.replace("\n", "\r\n"), encoding="ascii")
    (bundle / "RETRAIN_DEFAULT_MODEL.bat").write_text(TRAIN_BAT.replace("\n", "\r\n"), encoding="ascii")
    (bundle / "README_FIRST.txt").write_text(README_TXT.replace("\n", "\r\n"), encoding="utf-8")

    if args.no_zip:
        print(f"Done: {bundle}")
        return
    print("4/4 zip")
    archive = shutil.make_archive(str(out / "GreyZoneTriage_portable_win64"), "zip", root_dir=out,
                                  base_dir="GreyZoneTriage")
    size = Path(archive).stat().st_size / 1e6
    print(f"Done: {archive}  ({size:.0f} MB)")


if __name__ == "__main__":
    main()
