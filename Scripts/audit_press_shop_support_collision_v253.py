"""Run the conservative support collision screen against v253."""

from pathlib import Path


source = Path(__file__).with_name("audit_press_shop_support_collision_v250.py")
code = source.read_text(encoding="utf-8").replace("v250", "v253").replace("V250", "V253")
exec(compile(code, str(source) + "::v253", "exec"), globals(), globals())
