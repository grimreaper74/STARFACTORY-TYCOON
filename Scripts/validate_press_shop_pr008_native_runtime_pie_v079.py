"""Adapt the proven v074 native PR-008 runtime gate to calibrated-lighting v079."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr008_native_runtime_pie_v074.py")
code = base.read_text(encoding="utf-8").replace(
    "NativeRuntimeCandidate_v074", "CalibratedLightingCandidate_v079")
code = code.replace("v074", "v079").replace("V074", "V079")
exec(compile(code, str(base) + "::v079-adapter", "exec"), globals(), globals())
