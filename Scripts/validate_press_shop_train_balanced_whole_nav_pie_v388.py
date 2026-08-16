"""Reuse the exact v368 whole-shop navigation gate on fresh v386."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_expanded_whole_nav_pie_v368.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367", "LB_PressShop_TrainBalancedLightingCandidate_v386")
code = code.replace("press_shop_expanded_whole_nav_pie_v368.json", "press_shop_train_balanced_whole_nav_pie_v388.json")
code = code.replace("expanded-whole-nav-pie-v368/v1", "train-balanced-whole-nav-pie-v388/v1")
exec(compile(code, str(base) + "::v388", "exec"), globals(), globals())
