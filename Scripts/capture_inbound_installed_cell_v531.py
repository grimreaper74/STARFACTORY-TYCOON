"""Capture fixed visual gates for isolated inbound cell v531."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v530.py").read_text(encoding="utf-8")
source = source.replace("v530", "v531").replace("V530", "V531").replace("V030_", "V031_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v530.py"), "exec"), globals(), globals())
