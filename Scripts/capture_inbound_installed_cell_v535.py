"""Capture fixed visual gates for isolated inbound cell v535."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v534.py").read_text(encoding="utf-8")
source = source.replace("v534", "v535").replace("V534", "V535").replace("V034_", "V035_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v534.py"), "exec"), globals(), globals())
