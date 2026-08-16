"""Run the whole playable-management PIE gate against exact v295."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

def expand(path):
    text = path.read_text(encoding="utf-8")
    source_match = re.search(r'with_name\("([^"]+)"\)', text)
    if source_match is None:
        return text
    inner = expand(path.with_name(source_match.group(1)))
    for old, new in re.findall(r'\.replace\("([^"]+)",\s*"([^"]+)"\)', text):
        inner = inner.replace(old, new)
    return inner

code = expand(HERE / "validate_press_shop_playable_management_pie_v288.py")
old_map = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
new_map = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295"
if old_map not in code:
    raise RuntimeError("expanded v288 management validator no longer contains expected map")
code = code.replace(old_map, new_map)
code = code.replace("press_shop_playable_management_pie_v288", "press_shop_playable_management_pie_v295")
exec(compile(code, str(HERE / "validate_press_shop_playable_management_pie_v288.py") + "::exact-v295", "exec"), {"__name__": "__main__", "__file__": str(HERE / "validate_press_shop_playable_management_pie_v295.py")})
