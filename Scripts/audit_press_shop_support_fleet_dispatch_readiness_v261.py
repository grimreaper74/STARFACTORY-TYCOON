"""Run the exact dispatch-readiness matrix against nav-coverage child v261."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_support_fleet_dispatch_readiness_v260.py")
code = source.read_text(encoding="utf-8").replace("v260", "v261").replace("V260", "V261")
exec(compile(code, str(source) + "::v261", "exec"), globals(), globals())
