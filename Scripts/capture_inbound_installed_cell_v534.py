"""Capture fixed visual gates for isolated inbound cell v534."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v532.py").read_text(encoding="utf-8")
source = source.replace("v532", "v534").replace("V532", "V534").replace("V032_", "V034_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v532.py"), "exec"), globals(), globals())
