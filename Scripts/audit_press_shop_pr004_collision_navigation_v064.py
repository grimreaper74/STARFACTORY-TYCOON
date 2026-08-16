"""Run collision/navigation audit against PR-008 Module 01 candidate v064."""
from pathlib import Path
base = Path(__file__).with_name("audit_press_shop_pr004_collision_navigation_v063.py")
code = base.read_text(encoding="utf-8").replace("v063", "v064")
code = code.replace("LB_PressShop_PR008ProEntryLoopCandidate_v064", "LB_PressShop_PR008Module01Candidate_v064")
exec(compile(code, str(base) + "::v064-adapter", "exec"), globals(), globals())
