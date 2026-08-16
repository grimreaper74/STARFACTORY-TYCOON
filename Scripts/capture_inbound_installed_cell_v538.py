"""Capture fixed visual gates for isolated inbound cell v538."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v537.py").read_text(encoding="utf-8")
source = source.replace("v537", "v538").replace("V537", "V538").replace("V037_", "V038_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v537.py"), "exec"), globals(), globals())
