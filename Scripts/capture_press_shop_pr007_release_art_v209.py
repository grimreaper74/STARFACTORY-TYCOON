"""Capture live fixed PR-007 release-art views on exact v209."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = source.read_text(encoding="utf-8")
needle = '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",'
code = code.replace(
    needle,
    needle + '\n    "v209": "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209",',
)
view_needle = '    "pr007_runtime_service_motion": ("LB_PR007_V057_CAM_RuntimeServiceMotion", "press_shop_v057_pr007_runtime_service_motion.png"),'
code = code.replace(
    view_needle,
    view_needle + '\n'
    '    "pr007_release_operator": ("LB_PR007_V209_CAM_OperatorRelease", "press_shop_v209_pr007_operator_release_runtime.png"),\n'
    '    "pr007_release_drive": ("LB_PR007_V209_CAM_DriveRelease", "press_shop_v209_pr007_drive_release_runtime.png"),\n'
    '    "pr007_release_connected": ("LB_PR007_V209_CAM_ConnectedRelease", "press_shop_v209_pr007_connected_release_runtime.png"),',
)
code = code.replace(
    '("v057", "v058", "v059", "v060", "v061")',
    '("v057", "v058", "v059", "v060", "v061", "v209")',
)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
