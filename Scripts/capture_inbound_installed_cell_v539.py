"""Capture fixed visual gates for isolated inbound cell v539."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v538.py").read_text(encoding="utf-8")
source = source.replace("v538", "v539").replace("V538", "V539").replace("V038_", "V039_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v538.py"), "exec"), globals(), globals())
