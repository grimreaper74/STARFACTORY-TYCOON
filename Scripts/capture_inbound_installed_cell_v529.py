"""Capture fixed visual gates for isolated inbound cell v529."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v528.py").read_text(encoding="utf-8")
source = source.replace("v528", "v529").replace("V528", "V529").replace("V028_", "V029_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v528.py"), "exec"), globals(), globals())
