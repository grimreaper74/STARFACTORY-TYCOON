"""Adapt the v077 native PR-008 runtime gate to reflection-environment v078."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr008_native_runtime_pie_v077.py")
code = base.read_text(encoding="utf-8").replace(
    "SmoothLayerCandidate_v077", "ReflectionEnvironmentCandidate_v078")
code = code.replace("v077", "v078").replace("V077", "V078")
exec(compile(code, str(base) + "::v078-adapter", "exec"), globals(), globals())
