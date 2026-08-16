"""Capture fixed visual gates for isolated inbound cell v530."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v529.py").read_text(encoding="utf-8")
source = source.replace("v529", "v530").replace("V529", "V530").replace("V029_", "V030_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v529.py"), "exec"), globals(), globals())
