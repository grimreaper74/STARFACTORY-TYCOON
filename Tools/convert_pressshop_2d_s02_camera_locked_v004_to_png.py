"""Convert the v004 camera-locked capture to a review PNG."""
from pathlib import Path

import OpenImageIO as oiio

SOURCE = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\PressShop2126\Factorio2p5DFull_v004CameraLockedSprites\02_s02_camera_locked_whitekey093.exr")
OUTPUT = SOURCE.with_name(SOURCE.stem + "_srgb.png")
if not SOURCE.is_file():
    raise RuntimeError("camera-locked EXR is missing")
if OUTPUT.exists():
    raise RuntimeError("refusing to overwrite camera-locked review PNG")
image = oiio.ImageBuf(str(SOURCE))
if image.has_error:
    raise RuntimeError(image.geterror())
converted = oiio.ImageBufAlgo.colorconvert(image, "linear", "sRGB")
if converted.has_error:
    raise RuntimeError(converted.geterror())
if not converted.write(str(OUTPUT)):
    raise RuntimeError(converted.geterror())
print("PRESSSHOP_S02_CAMERA_LOCKED_REVIEW_PNG_WRITTEN", OUTPUT)
