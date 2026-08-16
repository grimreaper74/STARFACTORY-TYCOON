"""Reuse the exact v364 collision/service gate on fresh v386."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_expanded_aisle_collision_pie_v363.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_ExpandedTrainNavCandidate_v362", "LB_PressShop_TrainBalancedLightingCandidate_v386")
code = code.replace("press_shop_expanded_aisle_collision_pie_v364.json", "press_shop_train_balanced_aisle_collision_pie_v389.json")
code = code.replace("expanded-aisle-collision-pie-v364/v1", "train-balanced-aisle-collision-pie-v389/v1")
exec(compile(code, str(base) + "::v389", "exec"), globals(), globals())
