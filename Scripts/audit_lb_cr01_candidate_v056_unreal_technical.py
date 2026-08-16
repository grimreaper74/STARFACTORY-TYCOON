"""Fresh reload audit adapter for CR01 v056 trim-hierarchy candidate."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
adapter = root / "Scripts/audit_lb_cr01_candidate_v054_unreal_technical.py"
code = adapter.read_text(encoding="utf-8")
required = ("v054", "V054", "shared_paint_binding_count != 39", "Expected 39 fine-scale")
if any(token not in code for token in required):
    raise RuntimeError("v056 audit adapter drift")
code = code.replace("v054", "v056").replace("V054", "V056")
code = code.replace("shared_paint_binding_count != 39", "shared_paint_binding_count != 58")
code = code.replace("Expected 39 fine-scale", "Expected 58 fine-scale")
exec(compile(code, str(adapter) + "::v056-adapter", "exec"), globals(), globals())
