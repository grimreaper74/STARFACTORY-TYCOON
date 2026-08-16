"""Adapt the proven v074 native PR-008 runtime gate to isolated visual-cleanup v075."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr008_native_runtime_pie_v074.py")
code = base.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "VisualCleanupCandidate_v075")
code = code.replace("v074", "v075").replace("V074", "V075")
exec(compile(code, str(base) + "::v075-adapter", "exec"), globals(), globals())
