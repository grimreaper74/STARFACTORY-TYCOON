"""Capture one CR01 v058 functional-authority fixed camera per editor process."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
adapter = root / "Scripts/capture_lb_cr01_v054_fixed_cameras.py"
code = adapter.read_text(encoding="utf-8")
if "v054" not in code or "FinePaintVisual" not in code:
    raise RuntimeError("v058 capture adapter drift")
code = code.replace("FinePaintVisual", "FunctionalAuthority")
code = code.replace("finepaint_visual", "functional_authority")
code = code.replace("finepaint-visual", "functional-authority")
code = code.replace("fine-paint candidate", "functional-authority candidate")
code = code.replace("v054", "v058").replace("V054", "V058")
exec(compile(code, str(adapter) + "::v058-adapter", "exec"), globals(), globals())

