from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_operational_readability_v509.py").read_text(encoding="utf-8")
source = source.replace("OperationalReadability_v509", "OperationalReadability_v510")
source = source.replace("inbound_coil_delivery_v509", "inbound_coil_delivery_v510")
source = source.replace("V509", "V510")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
