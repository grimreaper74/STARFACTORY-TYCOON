"""Build route R03 with visual floor-detail correction in fresh v267."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_support_fleet_runtime_candidate_v266.py")
code = source.read_text(encoding="utf-8").replace("v266", "v267").replace("V266", "V267")
code = code.replace('"route_revision": 2', '"route_revision": 3')
code = code.replace("R02", "R03")
exec(compile(code, str(source) + "::v267-r03-cr-cabinet-clearance", "exec"), globals(), globals())
