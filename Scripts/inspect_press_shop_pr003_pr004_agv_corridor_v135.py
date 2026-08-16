"""Read-only actor/bounds inventory for the exact v135 AGV corridor."""

from pathlib import Path

source = Path(__file__).with_name("inspect_press_shop_pr003_pr004_agv_corridor_v124.py")
code = source.read_text(encoding="utf-8")
code = code.replace("retained v124", "isolated runtime v135")
code = code.replace("LB_PressShop_PR003Sheet2LayoutCandidate_v124", "LB_PressShop_PR003PR004CoilAGVRuntimeCandidate_v135")
code = code.replace("agv_corridor_inspection_v124", "agv_corridor_inspection_v135")
code = code.replace("inspection-v124", "inspection-v135")
exec(compile(code, str(source), "exec"), {"__name__":"__main__","__file__":str(source)})
