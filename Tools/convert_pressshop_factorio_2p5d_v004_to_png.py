"""Convert the native 2.5D SceneCapture EXR to a user-review PNG."""
from pathlib import Path

import OpenImageIO as oiio


SOURCE = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\PressShop2126\Factorio2p5D_v005\01_fixed_isometric_press_cell.exr")
OUTPUT = SOURCE.with_name("01_fixed_isometric_press_cell_srgb.png")
if not SOURCE.is_file():
    raise RuntimeError("2.5D SceneCapture EXR is missing")
if OUTPUT.exists():
    raise RuntimeError("refusing to overwrite 2.5D review PNG")

image = oiio.ImageBuf(str(SOURCE))
if image.has_error:
    raise RuntimeError(image.geterror())
converted = oiio.ImageBufAlgo.colorconvert(image, "linear", "sRGB")
if converted.has_error:
    raise RuntimeError(converted.geterror())
if not converted.write(str(OUTPUT)):
    raise RuntimeError(converted.geterror())
print("PRESSSHOP_FACTORIO_2P5D_PNG_WRITTEN", OUTPUT)
