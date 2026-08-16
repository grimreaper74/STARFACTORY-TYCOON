"""Adapt the inherited v065 gate to PR-008 Module 03 candidate v066."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_navigation_pie_v065.py")
code = base.read_text(encoding="utf-8").replace("v065", "v066")
code = code.replace("LB_PressShop_PR008Module02Candidate_v066", "LB_PressShop_PR008Module03Candidate_v066")
exec(compile(code, str(base) + "::v066-adapter", "exec"), globals(), globals())
