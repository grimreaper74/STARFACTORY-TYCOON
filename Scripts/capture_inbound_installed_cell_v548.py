"""Capture fixed visual gates for isolated inbound cell v548."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v540.py").read_text(encoding="utf-8")
source = source.replace("v540", "v548").replace("V540", "V548").replace("V040_", "V048_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v540.py"), "exec"), globals(), globals())
