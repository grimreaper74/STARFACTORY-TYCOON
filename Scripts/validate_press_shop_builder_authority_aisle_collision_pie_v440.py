"""Exact v438 standing-player aisle and conservative service-envelope regression."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_train_balanced_aisle_collision_pie_v389.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_TrainBalancedLightingCandidate_v386", "LB_PressShop_BuilderAuthorityCandidate_v438")
code = code.replace("press_shop_train_balanced_aisle_collision_pie_v389.json", "press_shop_builder_authority_aisle_collision_pie_v440.json")
code = code.replace("train-balanced-aisle-collision-pie-v389/v1", "builder-authority-aisle-collision-pie-v440/v1")
exec(compile(code, str(base) + "::v440", "exec"), globals(), globals())
