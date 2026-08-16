"""Direct fixed-camera capture for v518."""
from pathlib import Path
source=(Path(__file__).parent/"capture_inbound_installed_cell_v517.py").read_text(encoding="utf-8")
source=source.replace("v517","v518").replace("V517","V518")
exec(compile(source,str(Path(__file__)),"exec"),globals(),globals())
