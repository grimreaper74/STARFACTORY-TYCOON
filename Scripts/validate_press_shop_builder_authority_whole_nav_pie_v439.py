"""Exact v438 whole-shop navigation regression."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_train_balanced_whole_nav_pie_v388.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_TrainBalancedLightingCandidate_v386", "LB_PressShop_BuilderAuthorityCandidate_v438")
code = code.replace("press_shop_train_balanced_whole_nav_pie_v388.json", "press_shop_builder_authority_whole_nav_pie_v439.json")
code = code.replace("train-balanced-whole-nav-pie-v388/v1", "builder-authority-whole-nav-pie-v439/v1")
exec(compile(code, str(base) + "::v439", "exec"), globals(), globals())
