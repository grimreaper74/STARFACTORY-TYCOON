"""Build route R04 with visual floor-detail correction in fresh v268."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_support_fleet_runtime_candidate_v267.py")
code = source.read_text(encoding="utf-8").replace("v267", "v268").replace("V267", "V268")
code = code.replace('"route_revision": 3', '"route_revision": 4')
code = code.replace("R03", "R04")
exec(compile(code, str(source) + "::v268-r04-util-divider-clearance", "exec"), globals(), globals())
