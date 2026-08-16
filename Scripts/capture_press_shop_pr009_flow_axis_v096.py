"""Capture the six fixed v096 cameras using the proven v095 capture implementation."""
from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_pr009_enclosure_release_v095.py")
code = source.read_text(encoding="utf-8").replace("V095", "V096").replace("v095", "v096")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR009EnclosureReleaseCandidate_v096",
    "/Game/LineBoss/Maps/LB_PressShop_PR009FlowAxisCorrectionCandidate_v096")
exec(compile(code, str(source) + "::v096-flow-axis", "exec"), globals(), globals())
