"""Capture fixed visual gates for isolated inbound cell v532."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v531.py").read_text(encoding="utf-8")
source = source.replace("v531", "v532").replace("V531", "V532").replace("V031_", "V032_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v531.py"), "exec"), globals(), globals())
