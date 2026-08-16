"""Independent clean-scene FBX gate for powered C-hook candidate v034."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_crane_chook_candidate_v033_blender.py")
code = source.read_text(encoding="utf-8")
code = code.replace("CHook/Candidate_v033", "PoweredCHook/Candidate_v034")
code = code.replace("SM_LB_Crane_CHook_Candidate_v033", "SM_LB_Crane_PoweredCHook_Candidate_v034")
code = code.replace("press_shop_crane_chook_candidate_v033_source", "press_shop_crane_powered_chook_candidate_v034_source")
code = code.replace("lb_crane_chook_v033_", "lb_crane_powered_chook_v034_")
code = code.replace("candidate-v033", "powered-chook-candidate-v034")
code = code.replace("v033", "v034")
code = code.replace(
    "2.35 <= dims[0] <= 2.48 and 0.50 <= dims[1] <= 0.62 and\n                  1.95 <= dims[2] <= 2.08 and len(hook.material_slots) == 4",
    "2.70 <= dims[0] <= 2.76 and 1.03 <= dims[1] <= 1.10 and\n                  2.78 <= dims[2] <= 2.87 and len(hook.material_slots) == 7")
exec(compile(code, str(source), "exec"), {"__name__":"__main__","__file__":str(source)})
