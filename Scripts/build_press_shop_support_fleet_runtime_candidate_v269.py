"""Build route R05 with structural-column clearance in fresh v269."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_support_fleet_runtime_candidate_v268.py")
code = source.read_text(encoding="utf-8").replace("v268", "v269").replace("V268", "V269")
code = code.replace('"route_revision": 4', '"route_revision": 5')
code = code.replace("R04", "R05")
exec(compile(code, str(source) + "::v269-r05-column-clearance", "exec"), globals(), globals())
