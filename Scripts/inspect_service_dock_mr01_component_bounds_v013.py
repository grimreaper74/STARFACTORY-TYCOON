"""Read-only component-bound decomposition for straight-dock MR01 v022 in map v013."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/inspect_service_dock_mr01_component_bounds_v010.py"
code = base.read_text(encoding="utf-8")
code = code.replace("v008", "v013").replace("V008", "V013")
code = code.replace("MR01_v021", "MR01_v022")
code = code.replace("v010", "v013").replace("V010", "V013")
exec(compile(code, str(base) + "::v013-straight-dock-bounds", "exec"), globals(), globals())
