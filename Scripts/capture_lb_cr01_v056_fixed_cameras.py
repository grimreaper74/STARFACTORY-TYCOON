"""Capture one CR01 v056 restrained-trim fixed camera per process."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
adapter = root / "Scripts/capture_lb_cr01_v054_fixed_cameras.py"
code = adapter.read_text(encoding="utf-8")
if "v054" not in code or "FinePaintVisual" not in code:
    raise RuntimeError("v056 capture adapter drift")
code = code.replace("FinePaintVisual", "TrimHierarchyVisual")
code = code.replace("finepaint_visual", "trim_hierarchy_visual")
code = code.replace("finepaint-visual", "trim-hierarchy-visual")
code = code.replace("v054", "v056").replace("V054", "V056")
exec(compile(code, str(adapter) + "::v056-adapter", "exec"), globals(), globals())
