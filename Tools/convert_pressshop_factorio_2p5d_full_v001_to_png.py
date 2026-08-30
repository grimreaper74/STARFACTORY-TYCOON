"""Create a review PNG from the immutable native full-map EXR capture.

This runs in Blender's Python runtime and only writes the PNG named below.
It never loads Unreal or changes a map or asset.
"""
from pathlib import Path

import OpenImageIO as oiio


SOURCE = Path(
    r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\PressShop2126\Factorio2p5DFull_v001\01_full_press_shop_overview.exr"
)
OUTPUT = SOURCE.with_name(SOURCE.stem + "_srgb.png")

if not SOURCE.is_file():
    raise RuntimeError("Full 2.5D source EXR is missing: {}".format(SOURCE))
if OUTPUT.exists():
    raise RuntimeError("Refusing to overwrite review PNG: {}".format(OUTPUT))

image = oiio.ImageBuf(str(SOURCE))
if image.has_error:
    raise RuntimeError(image.geterror())
converted = oiio.ImageBufAlgo.colorconvert(image, "linear", "sRGB")
if converted.has_error:
    raise RuntimeError(converted.geterror())
if not converted.write(str(OUTPUT)):
    raise RuntimeError(converted.geterror())
print("PRESSSHOP_FACTORIO_FULL_REVIEW_PNG_WRITTEN", OUTPUT)
