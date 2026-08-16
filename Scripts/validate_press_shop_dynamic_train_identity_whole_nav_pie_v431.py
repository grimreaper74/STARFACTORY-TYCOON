"""Exact v429 whole-shop navigation regression."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_train_balanced_whole_nav_pie_v388.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_TrainBalancedLightingCandidate_v386", "LB_PressShop_DynamicTrainIdentityCandidate_v429")
code = code.replace("press_shop_train_balanced_whole_nav_pie_v388.json", "press_shop_dynamic_train_identity_whole_nav_pie_v431.json")
code = code.replace("train-balanced-whole-nav-pie-v388/v1", "dynamic-train-identity-whole-nav-pie-v431/v1")
exec(compile(code, str(base) + "::v431", "exec"), globals(), globals())
