"""Capture fixed visual gates for isolated inbound cell v537."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v535.py").read_text(encoding="utf-8")
source = source.replace("v535", "v537").replace("V535", "V537").replace("V035_", "V037_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v535.py"), "exec"), globals(), globals())
