"""Open Digit Studio or run a smoke check from the command line."""

import argparse
from pathlib import Path
import sys

from PIL import Image, ImageDraw

from .inference import MODELS, ModelStore


def main() -> int:
    """Run the desktop application or verify its runtime and model bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-models", action="store_true")
    mode.add_argument("--check-window", action="store_true")
    parser.add_argument("--report", type=Path, help="Write model check output to a text file.")
    args = parser.parse_args()
    if not args.check_models:
        from .window import DigitStudio

        window = DigitStudio()
        if args.check_window:
            window.root.update_idletasks()
            window._close()
        else:
            window.run()
        return 0

    image = Image.new("L", (100, 100))
    ImageDraw.Draw(image).line((50, 20, 50, 80), fill=255, width=8)
    _, results = ModelStore().predict(image, tuple(MODELS))
    lines = []
    for result in results:
        message = result.error or f"OK · {result.digit} · {len(result.probabilities)} xác suất"
        lines.append(f"{result.name}: {message}")
    report = "\n".join(lines) + "\n"
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    if sys.stdout is not None:
        print(report, end="")
    return int(any(result.error for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
