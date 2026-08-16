"""Run the four-unit route R05 cycle against four-native-dock candidate v273."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_support_fleet_dispatch_pie_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v273").replace("V263", "V273")
code = code.replace('"route_revision": 1', '"route_revision": 5')
exec(compile(code, str(source) + "::v273-r05", "exec"), globals(), globals())
