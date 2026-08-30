"""Convert the no-save S02 sprite-art EXR capture into an sRGB review PNG."""
from pathlib import Path

import OpenImageIO as oiio

SOURCE = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\PressShop2126\Factorio2p5DFull_v002SpriteArt\01_s02_sprite_art_overview.exr")
OUTPUT = SOURCE.with_name(SOURCE.stem + "_srgb.png")
if not SOURCE.is_file():
    raise RuntimeError("S02 sprite-art EXR is missing")
if OUTPUT.exists():
    raise RuntimeError("Refusing to overwrite sprite-art review PNG")
image = oiio.ImageBuf(str(SOURCE))
if image.has_error:
    raise RuntimeError(image.geterror())
converted = oiio.ImageBufAlgo.colorconvert(image, "linear", "sRGB")
if converted.has_error:
    raise RuntimeError(converted.geterror())
if not converted.write(str(OUTPUT)):
    raise RuntimeError(converted.geterror())
print("PRESSSHOP_S02_SPRITE_REVIEW_PNG_WRITTEN", OUTPUT)
