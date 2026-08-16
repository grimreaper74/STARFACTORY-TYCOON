"""Capture isolated service-dock v013 with the corrected MR01 v022 authority."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/capture_service_dock_actual_robot_fit_v008.py"
code = base.read_text(encoding="utf-8")
code = code.replace("v008", "v013").replace("V008", "V013")
code = code.replace("MR01_v021", "MR01_v022")
exec(compile(code, str(base) + "::v013-straight-dock-capture", "exec"), globals(), globals())
