"""Run dispatch readiness against widened nav child v262."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_support_fleet_dispatch_readiness_v260.py")
code = source.read_text(encoding="utf-8").replace("v260", "v262").replace("V260", "V262")
code = code.replace("cross_aisle = (-3300.0, 4200.0, 25.0)", "cross_aisle = (-3300.0, 3000.0, 25.0)")
exec(compile(code, str(source) + "::v262-south-cross-aisle", "exec"), globals(), globals())
