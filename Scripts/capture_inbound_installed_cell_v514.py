"""Capture the fixed v514 inbound installed-cell process camera."""
from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_installed_cell_v512.py").read_text(encoding="utf-8")
source = source.replace("InstalledCell_v512", "InstalledCell_v514")
source = source.replace("inbound_coil_delivery_v512", "inbound_coil_delivery_v514")
source = source.replace("V512", "V514")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
