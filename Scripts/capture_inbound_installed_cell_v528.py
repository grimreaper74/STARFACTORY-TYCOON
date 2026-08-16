"""Capture the two fixed visual gates for isolated inbound cell v528."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "capture_inbound_installed_cell_v527.py").read_text(encoding="utf-8")
source = source.replace("v527", "v528").replace("V527", "V528").replace("V027_", "V028_")
exec(compile(source, str(root / "capture_inbound_installed_cell_v527.py"), "exec"), globals(), globals())
