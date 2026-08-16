"""Non-overwriting v406 sign source with outward, readable mesh lettering."""
from pathlib import Path

source=Path(__file__).with_name("build_press_shop_train_identity_signs_source_v396.py")
code=source.read_text(encoding="utf-8")
code=code.replace("PhysicalSigns_v396","PhysicalSigns_v406")
code=code.replace("v396","v406")
code=code.replace("-z - 0.055, x + centre_y_mm / 1000.0", "-z - 0.088, -x + centre_y_mm / 1000.0")
if "-z - 0.088, -x + centre_y_mm / 1000.0" not in code:
    raise RuntimeError("v406 readable-letter transform substitution failed")
exec(compile(code,str(source),"exec"),{"__name__":"__main__","__file__":str(source)})
