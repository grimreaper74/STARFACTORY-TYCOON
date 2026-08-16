"""Capture one fixed v134 south-route AGV view per clean editor process."""

from pathlib import Path
source = Path(__file__).with_name("capture_press_shop_pr003_pr004_coil_agv_v133.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v133", "v134").replace("V133", "V134")
start = code.index("CAPTURES = {")
end = code.index("}\n", start) + 2
code = code[:start] + '''CAPTURES = {
    "overview": ("LB_PR003_PR004_V134_CAM_SouthRouteOverview", "press_shop_v134_coil_agv_south_route_overview.png"),
    "close": ("LB_PR003_PR004_V134_CAM_AGVLoadedClose", "press_shop_v134_coil_agv_loaded_close.png"),
    "turn": ("LB_PR003_PR004_V134_CAM_RouteTurnAndPR004", "press_shop_v134_coil_agv_route_turn_pr004.png"),
}\n''' + code[end:]
code = code.replace('os.environ.get("LB_COIL_AGV_V134_CAPTURE", "loaded")', 'os.environ.get("LB_COIL_AGV_V134_CAPTURE", "overview")')
exec(compile(code, str(source), "exec"), {"__name__":"__main__","__file__":str(source)})
