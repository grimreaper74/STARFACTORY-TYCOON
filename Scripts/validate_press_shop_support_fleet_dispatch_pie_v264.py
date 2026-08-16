"""Run the four-unit route cycle against route-revision-2 child v264."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_support_fleet_dispatch_pie_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v264").replace("V263", "V264")
code = code.replace('"route_revision": 1', '"route_revision": 2')
exec(compile(code, str(source) + "::v264-route-r02", "exec"), globals(), globals())
