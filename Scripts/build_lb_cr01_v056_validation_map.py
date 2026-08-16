"""Build CR01 v056 restrained-trim fixed-camera comparison map."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
adapter = root / "Scripts/build_lb_cr01_v054_validation_map.py"
code = adapter.read_text(encoding="utf-8")
if "v054" not in code or "FinePaintVisual" not in code or 'return paint["MarkingWarmWhite_Restored"]' not in code:
    raise RuntimeError("v056 visual-map adapter drift")
code = code.replace("FinePaintVisual", "TrimHierarchyVisual")
code = code.replace('return paint["MarkingWarmWhite_Restored"]', 'return paint["ServiceGrey_Restored"]')
code = code.replace("v054", "v056").replace("V054", "V056")
exec(compile(code, str(adapter) + "::v056-adapter", "exec"), globals(), globals())
