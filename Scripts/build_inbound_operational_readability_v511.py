"""Build fresh isolated v511 using the corrected v510 geometry and AGV-side process view."""
from pathlib import Path

source = (Path(__file__).parent / "build_inbound_operational_readability_v510.py").read_text(encoding="utf-8")
source = source.replace("OperationalReadability_v510", "OperationalReadability_v511")
source = source.replace("LB_INBOUND_V010_", "LB_INBOUND_V011_")
source = source.replace("V510", "V511")
source = source.replace("unreal.Vector(-2450, -2850, 1500)", "unreal.Vector(2700, -2100, 1325)")
source = source.replace("unreal.Vector(180, 260, 170)", "unreal.Vector(160, 260, 180)")
source = source.replace('"field_of_view": 56.0', '"field_of_view": 52.0')
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
