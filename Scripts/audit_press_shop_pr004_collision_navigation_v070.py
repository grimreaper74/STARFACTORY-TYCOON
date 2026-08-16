"""Adapt the inherited v069 gate to PR-008 Module 07 candidate v070."""
from pathlib import Path
base = Path(__file__).with_name("audit_press_shop_pr004_collision_navigation_v069.py")
code = base.read_text(encoding="utf-8").replace("v069", "v070").replace("Module06", "Module07")
exec(compile(code, str(base) + "::v070-adapter", "exec"), globals(), globals())
