"""Run the four-unit route R04 cycle against v268."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_support_fleet_dispatch_pie_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v268").replace("V263", "V268")
code = code.replace('"route_revision": 1', '"route_revision": 4')
exec(compile(code, str(source) + "::v268-r04", "exec"), globals(), globals())
