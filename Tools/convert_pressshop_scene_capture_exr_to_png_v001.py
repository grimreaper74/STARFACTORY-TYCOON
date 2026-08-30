"""Convert a native Unreal SceneCapture EXR to a review PNG without touching UE assets."""
from pathlib import Path

import OpenImageIO as oiio

SOURCE = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\PressShop2126\CompactV003_s02_portal_lightingprobe_v043_dx12\02_s02_portal_press_scene_capture.exr")
OUTPUT = SOURCE.with_name(SOURCE.stem + "_srgb.png")
if not SOURCE.is_file():
    raise RuntimeError("SceneCapture EXR is missing")
if OUTPUT.exists():
    raise RuntimeError("Refusing to overwrite scene-capture review PNG")

image = oiio.ImageBuf(str(SOURCE))
if image.has_error:
    raise RuntimeError(image.geterror())
converted = oiio.ImageBufAlgo.colorconvert(image, "linear", "sRGB")
if converted.has_error:
    raise RuntimeError(converted.geterror())
if not converted.write(str(OUTPUT)):
    raise RuntimeError(converted.geterror())
print("PRESSSHOP_SCENE_CAPTURE_PNG_WRITTEN", OUTPUT)
