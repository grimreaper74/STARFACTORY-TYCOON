"""Adapt the inherited v066 gate to PR-008 Module 04 candidate v067."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_crane_pie_v066.py")
code = base.read_text(encoding="utf-8").replace("v066", "v067")
code = code.replace("LB_PressShop_PR008Module03Candidate_v067", "LB_PressShop_PR008Module04Candidate_v067")
exec(compile(code, str(base) + "::v067-adapter", "exec"), globals(), globals())
