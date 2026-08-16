from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_installed_cell_v554.py").read_text(encoding="utf-8")
source = source.replace("v554", "v557").replace("V554", "V557")
exec(compile(source, str(Path(__file__).parent / "capture_inbound_installed_cell_v554.py"), "exec"), globals(), globals())
