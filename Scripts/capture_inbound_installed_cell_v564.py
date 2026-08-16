from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_installed_cell_v561.py").read_text(encoding="utf-8")
source = source.replace("v561", "v564").replace("V561", "V564")
exec(compile(source, str(Path(__file__).parent / "capture_inbound_installed_cell_v561.py"), "exec"), globals(), globals())
