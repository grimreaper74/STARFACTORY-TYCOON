"""Reuse the exact v388 whole-shop navigation gate on fresh direct-v386 child v420."""
from pathlib import Path

base = Path(__file__).with_name("validate_press_shop_train_balanced_whole_nav_pie_v388.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_TrainBalancedLightingCandidate_v386", "LB_PressShop_DynamicTrainIdentityCandidate_v420")
code = code.replace("press_shop_train_balanced_whole_nav_pie_v388.json", "press_shop_dynamic_train_identity_whole_nav_pie_v422.json")
code = code.replace("train-balanced-whole-nav-pie-v388/v1", "dynamic-train-identity-whole-nav-pie-v422/v1")
exec(compile(code, str(base) + "::v422", "exec"), globals(), globals())
