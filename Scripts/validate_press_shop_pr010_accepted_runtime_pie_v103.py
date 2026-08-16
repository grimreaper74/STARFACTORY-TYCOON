"""Accepted v103 exact-map adapter for PR-010 runtime/collision/save proof."""

from pathlib import Path

base = Path(__file__).with_name("validate_press_shop_pr010_runtime_collision_pie_v099.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099", "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103")
code = code.replace("Saved/Audits/PR010_CollisionNavigation/runtime_collision_pie_audit_v099.json", "Saved/Audits/PR010_Accepted_v103/runtime_collision_pie_audit.json")
code = code.replace("pr010-runtime-collision-pie-v099", "pr010-accepted-runtime-collision-pie-v103")
code = code.replace("PR010_V099", "PR010_V103").replace("V099", "V103")
code = code.replace("__NOT_PROMOTED", "__ACCEPTED_BASELINE")
exec(compile(code, str(base) + "::accepted-v103", "exec"), globals(), globals())
