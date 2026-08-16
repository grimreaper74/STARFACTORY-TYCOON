"""Capture fixed crane-side v515 process evidence."""
from pathlib import Path

source=(Path(__file__).parent/"capture_inbound_installed_cell_v514.py").read_text(encoding="utf-8")
source=source.replace("InstalledCell_v514","InstalledCell_v515")
source=source.replace("inbound_coil_delivery_v514","inbound_coil_delivery_v515")
source=source.replace("V514","V515")
exec(compile(source,str(Path(__file__)),"exec"),globals(),globals())
