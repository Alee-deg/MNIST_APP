"""Verify a native PyInstaller build and archive it for distribution."""

import platform
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Smoke-test the executable, then package it for the current platform."""
    system = platform.system()
    arch = platform.machine().lower()
    arch = {"amd64": "x86_64", "aarch64": "arm64"}.get(arch, arch)
    dist = ROOT / "dist"
    output = ROOT / "packages"
    output.mkdir(exist_ok=True)
    stem = f"DigitStudio-{system.lower()}-{arch}"

    bundle = dist / ("DigitStudio.app" if system == "Darwin" else "DigitStudio")
    if system == "Darwin":
        executable = bundle / "Contents" / "MacOS" / "DigitStudio"
    elif system == "Windows":
        executable = bundle / "DigitStudio.exe"
    else:
        executable = bundle / "DigitStudio"

    report = output / f"{stem}-model-check.txt"
    report.unlink(missing_ok=True)
    result = subprocess.run(
        [str(executable), "--check-models", "--report", str(report)],
        cwd=output,
        timeout=120,
        check=False,
    )
    if report.is_file():
        print(report.read_text(encoding="utf-8"), end="")
    if result.returncode or not report.is_file():
        raise SystemExit("The packaged model check failed. See the model report.")

    if system == "Darwin":
        # ditto preserves framework symlinks and macOS bundle metadata.
        subprocess.run(
            ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
             str(bundle), str(output / f"{stem}.zip")],
            check=True,
        )
    elif system == "Windows":
        shutil.make_archive(str(output / stem), "zip", dist, bundle.name)
    else:
        with tarfile.open(output / f"{stem}.tar.gz", "w:gz") as archive:
            archive.add(bundle, arcname=bundle.name)


if __name__ == "__main__":
    main()
