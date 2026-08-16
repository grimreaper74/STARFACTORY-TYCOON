"""Capture one live-PIE single-berth or overview view from v258."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_support_fleet_runtime_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v258").replace("V255", "V258")
old = '''VIEWS = {
    "mr01": "LB_SUPPORT_FLEET_CAM_MR01_v258",
    "cr01": "LB_SUPPORT_FLEET_CAM_CR01_v258",
    "overview": "LB_SUPPORT_FLEET_CAM_OVERVIEW_v258",
}'''
new = '''VIEWS = {
    "mr01_01": "LB_SUPPORT_FLEET_CAM_MR01_01_v258",
    "mr01_02": "LB_SUPPORT_FLEET_CAM_MR01_02_v258",
    "cr01_01": "LB_SUPPORT_FLEET_CAM_CR01_01_v258",
    "cr01_02": "LB_SUPPORT_FLEET_CAM_CR01_02_v258",
    "overview": "LB_SUPPORT_FLEET_CAM_OVERVIEW_v258",
}'''
if old not in code:
    raise RuntimeError("Could not patch v258 capture view table")
code = code.replace(old, new)
exec(compile(code, str(source) + "::v258-single-berth", "exec"), globals(), globals())
