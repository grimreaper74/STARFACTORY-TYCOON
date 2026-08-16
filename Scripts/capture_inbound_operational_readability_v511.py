from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_operational_readability_v510.py").read_text(encoding="utf-8")
source = source.replace("OperationalReadability_v510", "OperationalReadability_v511")
source = source.replace("inbound_coil_delivery_v510", "inbound_coil_delivery_v511")
source = source.replace("V510", "V511")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
