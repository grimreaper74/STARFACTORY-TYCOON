"""Exact-v438 authority retry after the 1 cm rotated-box numerical tolerance."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_builder_authority_exact_v442.py")
code = base.read_text(encoding="utf-8")
code = code.replace("press_shop_builder_authority_exact_v442.json", "press_shop_builder_authority_exact_v443.json")
code = code.replace("builder-authority-exact-v442/v1", "builder-authority-exact-v443/v1")
code = code.replace("FAIL__V438_AUTHORITY_V442_NOT_RETAINABLE", "FAIL__V438_AUTHORITY_V443_NOT_RETAINABLE")
exec(compile(code, str(base) + "::v443", "exec"), globals(), globals())
