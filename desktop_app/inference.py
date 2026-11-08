"""Prepare handwritten digits and run the bundled classifiers."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from PIL import Image, ImageOps

MODEL_DIR = Path(__file__).resolve().parents[1] / "saved_models"
MODELS = {
    "CNN · Tăng cường mạnh": "cnn.joblib",
    "CNN · Tăng cường nhẹ": "cnn_no_data_au.joblib",
    "Multilayer Perceptron": "mlp.joblib",
    "Logistic Regression": "logistic_regression.joblib",
    "Linear SVM": "svm.joblib",
    "Naive Bayes": "naive_bayes.joblib",
    "Stacking Ensemble": "ensemble.joblib",
    "AdaBoost": "ada.joblib",
}

AUGMENTATION = {
    "CNN · Tăng cường mạnh": "Tăng cường mạnh",
    "CNN · Tăng cường nhẹ": "Tăng cường nhẹ",
    "Multilayer Perceptron": "Không tăng cường",
    "Logistic Regression": "Tăng cường nhẹ",
    "Linear SVM": "Tăng cường nhẹ",
    "Naive Bayes": "Không tăng cường",
    "Stacking Ensemble": "Không tăng cường",
    "AdaBoost": "Không tăng cường",
}


@dataclass(frozen=True)
class ModelResult:
    """Prediction, optional probabilities and any model-specific error."""

    name: str
    digit: int | None = None
    probabilities: tuple[tuple[int, float], ...] = ()
    error: str = ""


def prepare_image(image: Image.Image) -> Image.Image:
    """Center one digit on a 28×28 black canvas with bright foreground."""
    rgba = ImageOps.exif_transpose(image).convert("RGBA")
    rgba.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    alpha = np.asarray(rgba.getchannel("A"))
    if (alpha < 255).any():
        visible = alpha > 0
        if not visible.any():
            raise ValueError("Ảnh trong suốt hoàn toàn.")
        ink = np.asarray(rgba.convert("L"))[visible]
        background = 255 if np.median(ink) < 128 else 0
        base = Image.new("RGBA", rgba.size, (background,) * 3 + (255,))
        rgba = Image.alpha_composite(base, rgba)

    gray = rgba.convert("L")
    pixels = np.asarray(gray)
    border = np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]))
    if np.median(border) > 127:
        gray = ImageOps.invert(gray)
    bounds = gray.point(lambda value: 255 if value > 35 else 0).getbbox()
    if bounds is None:
        raise ValueError("Chưa tìm thấy nét chữ số. Hãy vẽ hoặc tải ảnh rõ nét.")
    crop = gray.crop(bounds)
    factor = 20 / max(crop.size)
    size = tuple(max(1, round(length * factor)) for length in crop.size)
    crop = crop.resize(size, Image.Resampling.LANCZOS)
    weights = np.asarray(crop, dtype=np.float32)
    rows, columns = np.indices(weights.shape)
    mass = weights.sum()
    if mass <= 0:
        raise ValueError("Nét chữ quá mảnh sau khi thu nhỏ ảnh.")
    x = round(13.5 - float((columns * weights).sum() / mass))
    y = round(13.5 - float((rows * weights).sum() / mass))
    output = Image.new("L", (28, 28))
    output.paste(crop, (min(max(x, 0), 28 - crop.width), min(max(y, 0), 28 - crop.height)))
    return output


class ModelStore:
    """Load each trusted bundled checkpoint on its first use."""

    def __init__(self, directory: Path = MODEL_DIR) -> None:
        """Use the saved_models folder next to the application package."""
        self.directory = directory
        self._loaded: dict[str, Any] = {}

    def issue(self, name: str) -> str:
        """Report missing or empty checkpoints before inference."""
        path = self.directory / MODELS[name]
        if not path.is_file():
            return f"Thiếu {path.name}"
        if not path.stat().st_size:
            return f"{path.name} rỗng (0 byte)"
        return ""

    def _probabilities(
        self, model: Any, features: np.ndarray,
    ) -> tuple[tuple[int, float], ...]:
        """Read labeled probabilities only if the model supplies them."""
        method = getattr(model, "predict_proba", None)
        classes = getattr(model, "classes_", None)
        if classes is None:
            classes = getattr(model, "classes", None)
        if not callable(method) or classes is None:
            return ()
        scores = np.asarray(method(features), dtype=float)
        labels = np.asarray(classes).reshape(-1)
        if scores.shape != (1, len(labels)) or not np.isfinite(scores).all():
            return ()
        values = scores[0]
        if np.any((values < 0) | (values > 1)) or not np.isclose(values.sum(), 1, atol=1e-4):
            return ()
        return tuple(sorted(zip(map(int, labels), map(float, values)),
                            key=lambda entry: entry[1], reverse=True))

    def predict(self, image: Image.Image, names: tuple[str, ...]) -> tuple[Image.Image, list[ModelResult]]:
        """Share a prepared image across the selected models, isolating failures."""
        preview = prepare_image(image)
        features = np.asarray(preview, dtype=np.float32).reshape(1, 784) / np.float32(255)
        results = []
        for name in names:
            issue = self.issue(name)
            if issue:
                results.append(ModelResult(name, error=issue))
                continue
            try:
                if name not in self._loaded:
                    self._loaded[name] = joblib.load(self.directory / MODELS[name])
                model = self._loaded[name]
                digit = int(np.asarray(model.predict(features)).item())
                if not 0 <= digit <= 9:
                    raise ValueError(f"Nhãn ngoài khoảng 0–9: {digit}")
            except ModuleNotFoundError as error:
                results.append(ModelResult(name, error=f"Thiếu {error.name}. Xem desktop_app/README.md."))
            except Exception as error:
                results.append(ModelResult(name, error=f"{type(error).__name__}: {error}"))
            else:
                try:
                    probabilities = self._probabilities(model, features)
                except Exception:
                    probabilities = ()
                results.append(ModelResult(name, digit, probabilities))
        return preview, results
