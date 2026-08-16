"""Exact v429 standing-player aisle and conservative service-envelope regression."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_train_balanced_aisle_collision_pie_v389.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_TrainBalancedLightingCandidate_v386", "LB_PressShop_DynamicTrainIdentityCandidate_v429")
code = code.replace("press_shop_train_balanced_aisle_collision_pie_v389.json", "press_shop_dynamic_train_identity_aisle_collision_pie_v432.json")
code = code.replace("train-balanced-aisle-collision-pie-v389/v1", "dynamic-train-identity-aisle-collision-pie-v432/v1")
exec(compile(code, str(base) + "::v432", "exec"), globals(), globals())
