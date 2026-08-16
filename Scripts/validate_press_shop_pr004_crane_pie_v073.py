"""Adapt the inherited v072 gate to PR-008 Module 10 candidate v073."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_crane_pie_v072.py")
code = base.read_text(encoding="utf-8").replace("v072", "v073").replace("Module09", "Module10")
exec(compile(code, str(base) + "::v073-adapter", "exec"), globals(), globals())
