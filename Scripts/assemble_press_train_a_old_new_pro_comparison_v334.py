"""Assemble immutable current/rebuilt/Pro Train A visual evidence after v333 capture.

This is an external evidence compositor only. It does not open Unreal, modify a map,
or promote a candidate. It deliberately refuses to overwrite prior evidence.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = PROJECT / "Saved/ValidationScreenshots/PressShopIntegration/v333_train_a_old_new_ingame_wide"
OLD_IMAGE = CAPTURE_DIR / "train_a_old_ingame_wide.png"
NEW_IMAGE = CAPTURE_DIR / "train_a_new_ingame_wide.png"
PRO_IMAGE = Path(r"C:\Users\greg_\Downloads\a_high_resolution_infographic_engineering_referenc.png")
OUT_DIR = PROJECT / "Saved/ValidationScreenshots/PressShopIntegration/v334_train_a_old_new_pro_comparison"
OUT_IMAGE = OUT_DIR / "train_a_current_rebuilt_pro_comparison_v334.png"
OUT_AUDIT = PROJECT / "Saved/Audits/PressTrains/press_train_a_current_rebuilt_pro_comparison_v334.json"

CANVAS = (1920, 1440)
PANEL = (1860, 400)
MARGIN_X = 30
TOP = 72
GAP = 52
BG = (18, 22, 24)
FG = (238, 242, 240)
ACCENT = (136, 194, 74)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def fit_panel(path: Path) -> Image.Image:
    with Image.open(path) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        return ImageOps.fit(source, PANEL, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def main() -> None:
    required = (OLD_IMAGE, NEW_IMAGE, PRO_IMAGE)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing comparison source(s): " + "; ".join(missing))
    if OUT_IMAGE.exists() or OUT_AUDIT.exists():
        raise FileExistsError("Refusing to overwrite existing v334 evidence")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", CANVAS, BG)
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.load_default(size=28)
    label_font = ImageFont.load_default(size=22)
    note_font = ImageFont.load_default(size=16)
    draw.text((MARGIN_X, 22), "PRESS TRAIN A - CURRENT / REBUILT / PRO REFERENCE", fill=FG, font=title_font)

    panels = (
        ("1  CURRENT RETAINED IN-GAME LINE (v301)", OLD_IMAGE),
        ("2  REBUILT IN-GAME VISUAL REVIEW (v330/v333 - NOT PROMOTED)", NEW_IMAGE),
        ("3  PRO VISUAL MODELLING REFERENCE (DIMENSIONS TBC)", PRO_IMAGE),
    )
    sources = []
    for index, (label, path) in enumerate(panels):
        y = TOP + index * (PANEL[1] + GAP)
        draw.text((MARGIN_X, y), label, fill=ACCENT, font=label_font)
        canvas.paste(fit_panel(path), (MARGIN_X, y + 28))
        sources.append({"label": label, "path": str(path), "sha256": sha256(path)})

    note = "Visual comparison only. Rebuilt line requires collision, navigation, runtime-authority and regression gates before promotion."
    draw.text((MARGIN_X, CANVAS[1] - 28), note, fill=FG, font=note_font)
    canvas.save(OUT_IMAGE, format="PNG", optimize=True)

    audit = {
        "$schema": "cairnwell/audit/press-train-a-current-rebuilt-pro-comparison-v334/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "EVIDENCE_ASSEMBLED__MANUAL_VISUAL_DECISION_REQUIRED__NOT_PROMOTED",
        "sources": sources,
        "output": {"path": str(OUT_IMAGE), "sha256": sha256(OUT_IMAGE)},
        "promotion_authorized": False,
        "required_next_gates": [
            "manual_current_vs_rebuilt_vs_pro_visual_decision",
            "authoritative_collision_mapping",
            "navigation_regression",
            "press_train_runtime_authority_regression",
            "whole_press_shop_management_regression",
        ],
    }
    OUT_AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
