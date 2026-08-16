"""Run the four-unit route R03 cycle against v267."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_support_fleet_dispatch_pie_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v267").replace("V263", "V267")
code = code.replace('"route_revision": 1', '"route_revision": 3')
exec(compile(code, str(source) + "::v267-r03", "exec"), globals(), globals())
