"""Adapt the inherited v068 gate to PR-008 Module 06 candidate v069."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_pr005_handoff_pie_v068.py")
code = base.read_text(encoding="utf-8").replace("v068", "v069").replace("Module05", "Module06")
exec(compile(code, str(base) + "::v069-adapter", "exec"), globals(), globals())
