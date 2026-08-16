"""Run the four-unit route cycle against floor-detail-corrected child v266."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_support_fleet_dispatch_pie_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v266").replace("V263", "V266")
code = code.replace('"route_revision": 1', '"route_revision": 2')
exec(compile(code, str(source) + "::v266-r02-floor-detail-collision", "exec"), globals(), globals())
