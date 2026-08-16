"""Adapt the inherited v070 gate to PR-008 Module 08 candidate v071."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_navigation_pie_v070.py")
code = base.read_text(encoding="utf-8").replace("v070", "v071").replace("Module07", "Module08")
exec(compile(code, str(base) + "::v071-adapter", "exec"), globals(), globals())
