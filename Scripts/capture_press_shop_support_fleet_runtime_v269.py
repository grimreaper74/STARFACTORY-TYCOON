"""Capture fresh v269 fleet evidence using inherited v260 fixed cameras."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_support_fleet_runtime_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v269").replace("V255", "V269")
old = '''VIEWS = {
    "mr01": "LB_SUPPORT_FLEET_CAM_MR01_v269",
    "cr01": "LB_SUPPORT_FLEET_CAM_CR01_v269",
    "overview": "LB_SUPPORT_FLEET_CAM_OVERVIEW_v269",
}'''
new = '''VIEWS = {
    "mr01_01": "LB_SUPPORT_FLEET_CAM_MR01_01_v260",
    "mr01_02": "LB_SUPPORT_FLEET_CAM_MR01_02_v260",
    "cr01_01": "LB_SUPPORT_FLEET_CAM_CR01_01_v260",
    "cr01_02": "LB_SUPPORT_FLEET_CAM_CR01_02_v260",
    "overview": "LB_SUPPORT_FLEET_CAM_OVERVIEW_v260",
}'''
if old not in code:
    raise RuntimeError("Could not patch v269 inherited camera table")
code = code.replace(old, new)
exec(compile(code, str(source) + "::v269-inherited-v260-cameras", "exec"), globals(), globals())
