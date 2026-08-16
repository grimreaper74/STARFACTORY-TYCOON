"""Build isolated actual-robot fit v013 with corrected MR01 v022 authority."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/build_service_dock_actual_robot_fit_candidate_v008.py"
code = base.read_text(encoding="utf-8")
code = code.replace("v008", "v013").replace("V008", "V013")
# The retained CR dock actor's lineage label is v008 even inside later maps.
code = code.replace("LB_DOCK_INTAKE_CR01_v013", "LB_DOCK_INTAKE_CR01_v008")
code = code.replace(
    "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021",
    "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v022/Blueprints/BP_LB_MR01_MaintenanceAMR_v022",
)
code = code.replace("MR01_v021", "MR01_v022").replace('("mr, "MR01", "v021")', '(mr, "MR01", "v022")')
code = code.replace('("mr, "MR01", "v021")', '(mr, "MR01", "v022")')
# The source line is a tuple expression, so cover its exact unquoted form too.
code = code.replace('(mr, "MR01", "v021")', '(mr, "MR01", "v022")')
exec(compile(code, str(base) + "::v013-straight-dock-build", "exec"), globals(), globals())
