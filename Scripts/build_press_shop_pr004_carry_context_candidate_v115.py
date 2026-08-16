"""Run the shared carry-context builder for isolated v115."""
import os
from pathlib import Path

os.environ["LB_PR004_CARRY_CONTEXT_VERSION"] = "v115"
source = Path(__file__).with_name("build_press_shop_pr004_carry_context_candidate_v114.py")
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"))
