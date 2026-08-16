from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_installed_cell_v512.py").read_text(encoding="utf-8")
source = source.replace("InstalledCell_v512", "InstalledCell_v513")
source = source.replace("inbound_coil_delivery_v512", "inbound_coil_delivery_v513")
source = source.replace("V512", "V513")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
