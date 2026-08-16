"""Adapt the inherited v064 gate to PR-008 Module 02 candidate v065."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_support_crane_pie_v064.py")
code = base.read_text(encoding="utf-8").replace("v064", "v065")
code = code.replace("LB_PressShop_PR008Module01Candidate_v065", "LB_PressShop_PR008Module02Candidate_v065")
exec(compile(code, str(base) + "::v065-adapter", "exec"), globals(), globals())
