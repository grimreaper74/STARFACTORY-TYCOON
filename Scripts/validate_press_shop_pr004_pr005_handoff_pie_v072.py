"""Adapt the inherited v071 gate to PR-008 Module 09 candidate v072."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_pr005_handoff_pie_v071.py")
code = base.read_text(encoding="utf-8").replace("v071", "v072").replace("Module08", "Module09")
exec(compile(code, str(base) + "::v072-adapter", "exec"), globals(), globals())
