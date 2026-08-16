"""Capture fixed visual gates for isolated inbound cell v540."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v539.py").read_text(encoding="utf-8")
source = source.replace("v539", "v540").replace("V539", "V540").replace("V039_", "V040_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v539.py"), "exec"), globals(), globals())
