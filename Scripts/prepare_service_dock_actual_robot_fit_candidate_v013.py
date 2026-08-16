"""Prepare fresh isolated dock-fit v013 directly from retained dock-family v005."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/prepare_service_dock_actual_robot_fit_candidate_v008.py"
code = base.read_text(encoding="utf-8")
code = code.replace("v008", "v013").replace("V008", "V013")
exec(compile(code, str(base) + "::v013-straight-dock-prepare", "exec"), globals(), globals())
