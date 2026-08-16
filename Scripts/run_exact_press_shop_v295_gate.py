"""Run one inherited v288 gate against exact v295, selected by environment."""
import os, re
from pathlib import Path
HERE = Path(__file__).resolve().parent
GATES = {
    "dock_collision": "audit_press_shop_native_service_docks_collision_v288.py",
    "pr009_navigation": "validate_press_shop_pr009_integrated_navigation_pie_v288.py",
    "pr010_navigation": "validate_press_shop_pr010_navigation_pie_v288.py",
}
gate = os.environ.get("LB_V295_GATE", "").lower()
if gate not in GATES: raise RuntimeError(f"unknown LB_V295_GATE={gate}")
def expand(path):
    text = path.read_text(encoding="utf-8"); source_match = re.search(r'with_name\("([^"]+)"\)', text)
    if source_match is None: return text
    inner = expand(path.with_name(source_match.group(1)))
    for old, new in re.findall(r'\.replace\("([^"]+)",\s*"([^"]+)"\)', text): inner = inner.replace(old, new)
    return inner
source = HERE / GATES[gate]; code = expand(source)
old_map = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
new_map = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295"
if old_map not in code: raise RuntimeError(f"expanded {source.name} lacks expected v288 map")
code = code.replace(old_map, new_map).replace("v288", "v295").replace("V288", "V295")
exec(compile(code, str(source) + f"::exact-v295-{gate}", "exec"), {"__name__": "__main__", "__file__": str(Path(__file__))})
