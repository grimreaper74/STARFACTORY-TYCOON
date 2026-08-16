"""Capture one CR01 v055 identity fixed camera per process."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
adapter = root / "Scripts/capture_lb_cr01_v054_fixed_cameras.py"
code = adapter.read_text(encoding="utf-8")
if "v054" not in code or "FinePaintVisual" not in code:
    raise RuntimeError("v055 capture adapter drift")
for old, new in (("FinePaintVisual", "IdentityVisual"), ("finepaint", "identity"), ("FinePaint", "Identity"), ("v054", "v055"), ("V054", "V055")):
    code = code.replace(old, new)
exec(compile(code, str(adapter) + "::v055-adapter", "exec"), globals(), globals())
