"""Build direct, labelled Unreal-vs-Pro evidence boards for the v005 isolation study."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageStat
import json

ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/press_train_a_assembly_integration_v005"
REFERENCE_DIR = ROOT / "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals"
AUDIT_DIR = ROOT / "Saved/Audits/PressTrains"

FONT = ImageFont.truetype("arial.ttf", 26)
SMALL = ImageFont.truetype("arial.ttf", 19)
WHITE = (235, 239, 241)
AMBER = (255, 194, 0)
RED = (255, 96, 80)
BG = (18, 22, 24)


def fit(image, size):
    image = image.convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (5, 7, 8))
    canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def board(reference_name, unreal_names, output_name, title):
    width, height = 2560, 1440
    canvas = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(canvas)
    draw.text((36, 24), title, fill=WHITE, font=FONT)
    draw.text((36, 62), "Direct evidence only — identical scale/angle is not claimed", fill=AMBER, font=SMALL)

    ref = fit(Image.open(REFERENCE_DIR / reference_name), (1210, 1220))
    canvas.paste(ref, (36, 122))
    draw.text((36, 96), "PRO REFERENCE", fill=WHITE, font=SMALL)

    cell_w, cell_h = 610, 580
    positions = [(1302, 122), (1926, 122), (1302, 744), (1926, 744)]
    for name, pos in zip(unreal_names, positions):
        image = fit(Image.open(CAPTURE_DIR / name), (cell_w, cell_h))
        canvas.paste(image, pos)
        draw.text((pos[0], pos[1] - 26), name.replace("press_train_a_assembly_v005_", "").replace(".png", ""), fill=WHITE, font=SMALL)

    draw.rectangle((1290, 1320, 2520, 1410), fill=(35, 22, 20))
    draw.text((1310, 1335), "REVIEW: ITERATE — technical import passes; exposure, fill and camera occlusion fail visual gate.", fill=RED, font=SMALL)
    canvas.save(CAPTURE_DIR / output_name, quality=95)


def luminance_stats():
    rows = []
    for path in sorted(CAPTURE_DIR.glob("press_train_a_assembly_v005_*.png")):
        if "comparison" in path.name or "_vs_pro_" in path.name:
            continue
        image = Image.open(path).convert("L")
        stat = ImageStat.Stat(image)
        histogram = image.histogram()
        total = image.width * image.height
        shadow = sum(histogram[:32]) / total
        rows.append({
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "resolution_px": [image.width, image.height],
            "mean_luminance_0_255": round(stat.mean[0], 3),
            "pixels_below_32_fraction": round(shadow, 5),
        })
    return rows


board(
    "SHEET_04_PRESS_TRAINS_SHARED_ARCHITECTURE_4K.png",
    [
        "press_train_a_assembly_v005_hero.png",
        "press_train_a_assembly_v005_operator_side.png",
        "press_train_a_assembly_v005_overhead.png",
        "press_train_a_assembly_v005_loaded_cart.png",
    ],
    "press_train_a_assembly_v005_vs_pro_sheet04.png",
    "PRESS TRAIN A ASSEMBLY INTEGRATION v005 — UNREAL / PRO SHEET 04",
)

board(
    "SHEET_05_PRESS_TRAIN_A_4K.png",
    [
        "press_train_a_assembly_v005_hero.png",
        "press_train_a_assembly_v005_s01.png",
        "press_train_a_assembly_v005_s07.png",
        "press_train_a_assembly_v005_mechanics.png",
    ],
    "press_train_a_assembly_v005_vs_pro_sheet05.png",
    "PRESS TRAIN A ASSEMBLY INTEGRATION v005 — UNREAL / PRO SHEET 05",
)

(AUDIT_DIR / "press_train_a_assembly_integration_capture_metrics_v005.json").write_text(
    json.dumps({"capture_set": "v005", "status": "VISUAL_GATE_FAIL", "images": luminance_stats()}, indent=2) + "\n",
    encoding="utf-8",
)
print("PASS: created two direct Pro comparison boards and capture metrics")
