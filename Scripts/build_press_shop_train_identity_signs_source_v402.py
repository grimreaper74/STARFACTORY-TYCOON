"""Non-overwriting v402 correction of the physical sign lettering projection.

The v396 source family is preserved.  This executes the audited generator with a
new output/version namespace and moves raised lettering fully beyond the inset
panel face, correcting the visual failure proven in v398/v400 screenshots.
"""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_train_identity_signs_source_v396.py")
code = source.read_text(encoding="utf-8")
code = code.replace("PhysicalSigns_v396", "PhysicalSigns_v402")
code = code.replace("v396", "v402")
code = code.replace("-z - 0.055", "-z - 0.088")
if "-z - 0.088" not in code:
    raise RuntimeError("v402 lettering projection substitution failed")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
