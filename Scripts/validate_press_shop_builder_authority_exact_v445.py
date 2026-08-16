"""Read-only exact-v438 authority validation with Unreal Python's roll/pitch/yaw constructor order."""
from pathlib import Path

base = Path(__file__).with_name("validate_press_shop_builder_authority_exact_v442.py")
code = base.read_text(encoding="utf-8")
code = code.replace("press_shop_builder_authority_exact_v442.json", "press_shop_builder_authority_exact_v445.json")
code = code.replace("builder-authority-exact-v442/v1", "builder-authority-exact-v445/v1")
code = code.replace("FAIL__V438_AUTHORITY_V442_NOT_RETAINABLE", "FAIL__V438_AUTHORITY_V445_NOT_RETAINABLE")
# unreal.Rotator positional construction is roll, pitch, yaw. Earlier validators used
# (0, 90, 0), pitching the complete 57.65 m train vertically and correctly failing the bay.
code = code.replace("rotation=unreal.Rotator(0.0, 90.0, 0.0)", "rotation=unreal.Rotator(0.0, 0.0, 90.0)")
exec(compile(code, str(base) + "::v445", "exec"), globals(), globals())
