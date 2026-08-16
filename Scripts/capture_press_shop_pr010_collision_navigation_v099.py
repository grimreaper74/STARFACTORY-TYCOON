"""v099 adapter for the retained fixed PR-010 camera suite."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr010_detailed_runtime_v098.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR010DetailedRuntimeCandidate_v098",
    "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099")
code = code.replace("v098_pr010_detailed_runtime", "v099_pr010_collision_navigation")
code = code.replace("press_shop_v098_pr010_", "press_shop_v099_pr010_")
code = code.replace("Cairnwell PR-010 v098 detailed remote buffer", "Cairnwell PR-010 v099 collision/navigation candidate")
exec(compile(code, str(base) + "::v099", "exec"), globals(), globals())
