"""v099 adapter for the PR-010 authority, dimension and branding static gate."""
from pathlib import Path

base = Path(__file__).with_name("audit_press_shop_pr010_detailed_runtime_static_v098.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR010DetailedRuntimeCandidate_v098",
    "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099")
code = code.replace("pr010_static_gate_v098.json", "pr010_static_gate_v099.json")
code = code.replace("Saved/Audits/PR010_DetailedRuntime", "Saved/Audits/PR010_CollisionNavigation")
code = code.replace("pr010-detailed-runtime-static-v098", "pr010-collision-navigation-static-v099")
code = code.replace("PR010_V098", "PR010_V099")
exec(compile(code, str(base) + "::v099", "exec"), globals(), globals())
