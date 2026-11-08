"""Bundle the GUI, trained models, and their inference dependencies."""

from pathlib import Path
import sys

root = Path(SPECPATH)
hidden_imports = [
    "src.algorithm.CNN",
    "src.algorithm.Ensemble",
    "src.algorithm.Logistic_Regression",
    "src.algorithm.MLP",
    "src.algorithm.NaiveBayes",
    "src.algorithm.SVM",
    "sklearn.ensemble",
    "sklearn.neighbors",
    "sklearn.tree",
]

analysis = Analysis(
    [str(root / "desktop_app" / "launcher.py")],
    pathex=[str(root)],
    datas=[(str(root / "saved_models" / "*.joblib"), "saved_models")],
    hiddenimports=hidden_imports,
    excludes=["IPython", "notebook", "pytest", "torchvision"],
)
python_archive = PYZ(analysis.pure)
executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="DigitStudio",
    console=sys.platform.startswith("linux"),
    upx=False,
)
distribution = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    name="DigitStudio",
    upx=False,
)
if sys.platform == "darwin":
    app = BUNDLE(
        distribution,
        name="DigitStudio.app",
        bundle_identifier="vn.digitstudio.desktop",
        info_plist={"CFBundleDisplayName": "Digit Studio"},
    )
