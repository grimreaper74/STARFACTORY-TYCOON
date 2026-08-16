"""Run the conservative support collision screen against v252."""

from pathlib import Path


source = Path(__file__).with_name("audit_press_shop_support_collision_v250.py")
code = source.read_text(encoding="utf-8").replace("v250", "v252").replace("V250", "V252")
exec(compile(code, str(source) + "::v252", "exec"), globals(), globals())
