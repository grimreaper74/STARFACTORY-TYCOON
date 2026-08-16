"""Run native service-dock collision ownership audit against v288."""
from pathlib import Path
source = Path(__file__).with_name("audit_press_shop_native_service_docks_collision_v287.py")
code = source.read_text(encoding="utf-8").replace("v287", "v288").replace("V287", "V288")
exec(compile(code, str(source) + "::v288", "exec"), globals(), globals())
