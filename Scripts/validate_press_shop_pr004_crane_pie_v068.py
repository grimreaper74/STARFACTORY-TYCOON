"""Adapt the inherited v066 gate to PR-008 Module 05 candidate v068."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_crane_pie_v066.py")
code = base.read_text(encoding="utf-8").replace("v066", "v068")
code = code.replace("LB_PressShop_PR008Module03Candidate_v068", "LB_PressShop_PR008Module05Candidate_v068")
exec(compile(code, str(base) + "::v068-adapter", "exec"), globals(), globals())
