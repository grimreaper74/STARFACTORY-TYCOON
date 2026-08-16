"""Fresh reload audit adapter for CR01 v055 identity-plaque candidate."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
adapter = root / "Scripts/audit_lb_cr01_candidate_v054_unreal_technical.py"
code = adapter.read_text(encoding="utf-8")
for old, new in (("v054", "v055"), ("V054", "V055")):
    if old not in code:
        raise RuntimeError(f"v055 audit adapter drift: missing {old!r}")
    code = code.replace(old, new)
exec(compile(code, str(adapter) + "::v055-adapter", "exec"), globals(), globals())
