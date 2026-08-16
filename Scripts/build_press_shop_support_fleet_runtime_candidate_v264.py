"""Install route-revision-2 fleet authority directly into a fresh v262 child."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_support_fleet_runtime_candidate_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v264").replace("V263", "V264")
code = code.replace('"route_revision": 1', '"route_revision": 2')
exec(compile(code, str(source) + "::v264-route-r02-direct-v262", "exec"), globals(), globals())
