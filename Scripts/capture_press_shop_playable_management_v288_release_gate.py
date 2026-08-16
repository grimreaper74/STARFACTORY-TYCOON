"""Capture a non-overwriting whole-shop visual gate from the exact retained v288 map."""
from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_playable_management_v273.py")
code = source.read_text(encoding="utf-8").replace("v273", "v288_release_gate").replace(
    "V273", "V288_RELEASE_GATE")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288_release_gate",
    "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288")
exec(compile(code, str(source) + "::v288-release-gate", "exec"), globals(), globals())
