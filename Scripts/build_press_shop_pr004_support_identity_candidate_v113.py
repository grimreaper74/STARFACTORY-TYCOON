"""Run the shared compact support-identity builder for isolated v113."""
import os
from pathlib import Path

os.environ["LB_PR004_SUPPORT_IDENTITY_VERSION"] = "v113"
source = Path(__file__).with_name("build_press_shop_pr004_support_identity_candidate_v111.py")
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"))
