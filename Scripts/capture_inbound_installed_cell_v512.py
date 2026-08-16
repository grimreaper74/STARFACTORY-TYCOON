from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_operational_readability_v511.py").read_text(encoding="utf-8")
source = source.replace("OperationalReadability_v511", "InstalledCell_v512")
source = source.replace("inbound_coil_delivery_v511", "inbound_coil_delivery_v512")
source = source.replace("V511", "V512")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
