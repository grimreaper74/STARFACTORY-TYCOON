"""Capture fresh live views from exact cumulative release candidate v213."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = source.read_text(encoding="utf-8")
map_needle = '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",'
code = code.replace(
    map_needle,
    map_needle + '\n    "v213": "/Game/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213",')
view_needle = '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),'
code = code.replace(
    view_needle,
    view_needle + '\n'
    '    "cumulative_pr005_service": ("LB_PR005_V053_CAM_LogisticsPlayer", "press_shop_v213_cumulative_pr005_service_runtime.png"),\n'
    '    "cumulative_pr006_connected": ("LB_PR006_V208_CAM_ConnectedRelease", "press_shop_v213_cumulative_pr006_connected_runtime.png"),\n'
    '    "cumulative_pr007_connected": ("LB_PR007_V209_CAM_ConnectedRelease", "press_shop_v213_cumulative_pr007_connected_runtime.png"),\n'
    '    "cumulative_pr008_process": ("LB_PR008_V210_CAM_AuthoredAnchorProcess", "press_shop_v213_cumulative_pr008_process_runtime.png"),\n'
    '    "cumulative_connected_line_v107": ("LB_ENV_V107_CAM_ConnectedLine", "press_shop_v213_cumulative_connected_line_v107_runtime.png"),\n'
    '    "cumulative_whole_line": ("LB_PR005_V046_CAM_PR005WholeLine", "press_shop_v213_cumulative_whole_line_runtime.png"),')
exec(compile(code, str(source) + "::v213-cumulative", "exec"), {"__name__": "__main__", "__file__": str(source)})
