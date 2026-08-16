"""Capture one CR01 v061 functional-authority fixed camera per process."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/capture_lb_cr01_v054_fixed_cameras.py"
code = base.read_text(encoding="utf-8")
if "v054" not in code or "FinePaintVisual" not in code:
    raise RuntimeError("v061 capture adapter drift")
for old, new in (
    ("FinePaintVisual", "FunctionalAuthority"),
    ("finepaint_visual", "functional_authority_scrubber"),
    ("finepaint-visual", "functional-authority-scrubber"),
    ("fine-paint candidate", "functional-authority scrubber candidate"),
    ("v054", "v061"),
    ("V054", "V061"),
):
    code = code.replace(old, new)
exec(compile(code, str(base) + "::v061-adapter", "exec"), globals(), globals())
