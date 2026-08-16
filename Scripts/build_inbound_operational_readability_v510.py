"""Build fresh isolated v510 with a truly unobstructed Coil AGV handoff lane."""
from pathlib import Path

source = (Path(__file__).parent / "build_inbound_operational_readability_v509.py").read_text(encoding="utf-8")
source = source.replace("OperationalReadability_v509", "OperationalReadability_v510")
source = source.replace("LB_INBOUND_V009_", "LB_INBOUND_V010_")
source = source.replace("V509", "V510")
source = source.replace("(760, 260, 37)", "(1180, 520, 37)")
source = source.replace("(760, 260, 45)", "(1180, 520, 45)")
source = source.replace("(760, 260, 83)", "(1180, 520, 83)")
source = source.replace("(760, 260, 185)", "(1180, 520, 185)")
source = source.replace("unreal.Vector(-2350, -2700, 1450)", "unreal.Vector(-2450, -2850, 1500)")
source = source.replace("unreal.Vector(100, 230, 170)", "unreal.Vector(180, 260, 170)")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
