"""Adapt the measured v074 PR-008/PR-009 interface audit to smooth-layer v077."""
from pathlib import Path
base = Path(__file__).with_name("inspect_press_shop_pr008_pr009_interface_v074.py")
code = base.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "SmoothLayerCandidate_v077")
code = code.replace("v074", "v077").replace("V074", "V077")
exec(compile(code, str(base) + "::v077-adapter", "exec"), globals(), globals())
