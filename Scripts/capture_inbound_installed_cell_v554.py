from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_installed_cell_v552.py").read_text(encoding="utf-8")
source = source.replace("v552", "v554").replace("V552", "V554")
exec(compile(source, str(Path(__file__).parent / "capture_inbound_installed_cell_v552.py"), "exec"), globals(), globals())
