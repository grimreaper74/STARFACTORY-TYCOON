"""Read-only material/component probe adapter for CR01 v056."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/probe_lb_cr01_v053_materials_branding.py"
code = base.read_text(encoding="utf-8")
code = code.replace("v053", "v056").replace("V053", "V056")
exec(compile(code, str(base) + "::v056-adapter", "exec"), globals(), globals())
