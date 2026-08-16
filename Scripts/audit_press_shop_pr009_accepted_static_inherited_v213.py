"""Run accepted PR009 static-authority audit on cumulative v213."""
from pathlib import Path
source = Path(__file__).with_name("audit_press_shop_pr009_accepted_static_inherited_v210.py")
code = source.read_text(encoding="utf-8").replace("v210", "v213").replace("V210", "V213")
exec(compile(code, str(source) + "::v213", "exec"), globals(), globals())
