"""Adapt the measured v074 PR-008/PR-009 interface audit to calibrated-lighting v079."""
from pathlib import Path
base = Path(__file__).with_name("inspect_press_shop_pr008_pr009_interface_v074.py")
code = base.read_text(encoding="utf-8").replace(
    "NativeRuntimeCandidate_v074", "CalibratedLightingCandidate_v079")
code = code.replace("v074", "v079").replace("V074", "V079")
exec(compile(code, str(base) + "::v079-adapter", "exec"), globals(), globals())
