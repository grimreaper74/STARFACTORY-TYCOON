"""Capture fixed visual gates for isolated inbound cell v545."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v544.py").read_text(encoding="utf-8")
source = source.replace("v544", "v545").replace("V544", "V545").replace("V044_", "V045_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v544.py"), "exec"), globals(), globals())
