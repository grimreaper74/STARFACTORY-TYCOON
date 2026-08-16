"""Capture one CR01 v063 branded scrubber fixed camera per process."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/capture_lb_cr01_v054_fixed_cameras.py"
code = base.read_text(encoding="utf-8")
if "v054" not in code or "FinePaintVisual" not in code:
    raise RuntimeError("v063 capture adapter drift")
for old, new in (
    ("FinePaintVisual", "FunctionalAuthority"),
    ("finepaint_visual", "functional_authority_branded_scrubber"),
    ("finepaint-visual", "functional-authority-branded-scrubber"),
    ("fine-paint candidate", "functional-authority branded scrubber candidate"),
    ("v054", "v063"),
    ("V054", "V063"),
):
    code = code.replace(old, new)
exec(compile(code, str(base) + "::v063-adapter", "exec"), globals(), globals())
