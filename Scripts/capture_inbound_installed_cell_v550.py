"""Capture fixed visual gates for isolated inbound cell v550."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v548.py").read_text(encoding="utf-8")
source = source.replace("v548", "v550").replace("V548", "V550").replace("V048_", "V050_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v548.py"), "exec"), globals(), globals())
