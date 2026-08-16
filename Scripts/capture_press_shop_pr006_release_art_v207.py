"""Capture live fixed PR-006 release-art views on exact v207."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = source.read_text(encoding="utf-8")
needle = '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",'
code = code.replace(
    needle,
    needle + '\n    "v207": "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v207",',
)
view_needle = '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),'
code = code.replace(
    view_needle,
    view_needle + '\n'
    '    "pr006_release_operator": ("LB_PR006_V207_CAM_OperatorRelease", "press_shop_v207_pr006_operator_release_runtime.png"),\n'
    '    "pr006_release_drive": ("LB_PR006_V207_CAM_DriveRelease", "press_shop_v207_pr006_drive_release_runtime.png"),\n'
    '    "pr006_release_connected": ("LB_PR006_V207_CAM_ConnectedRelease", "press_shop_v207_pr006_connected_release_runtime.png"),',
)
code = code.replace(
    '("v057", "v058", "v059", "v060", "v061")',
    '("v057", "v058", "v059", "v060", "v061", "v207")',
)
code = code.replace(
    '("v060", "v061")',
    '("v060", "v061", "v207")',
)
code = code.replace(
    'CANDIDATE == "v061"',
    'CANDIDATE in ("v061", "v207")',
)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
