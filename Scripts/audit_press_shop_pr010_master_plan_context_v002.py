"""Capture the corrected accepted PR-009 v096 context around PR-010."""
from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr010_master_plan_context_v001.py")
code = source.read_text(encoding="utf-8").replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v095",
    "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v096").replace(
    "pr010_master_plan_context_v001.json", "pr010_master_plan_context_v002.json").replace(
    "pr010-master-plan-context-v001/v1", "pr010-master-plan-context-v002/v1").replace(
    "CONTEXT_CAPTURED__ROTATION_REQUIRES_MEASURED_INTERPRETATION__NOT_PROMOTED",
    "PASS__ACCEPTED_PR009_V096_CONTEXT__PR010_YAW_MINUS_90_AND_HANDOFF_RESOLVED__NOT_PROMOTED")
exec(compile(code, str(source) + "::accepted-v096", "exec"), globals(), globals())
