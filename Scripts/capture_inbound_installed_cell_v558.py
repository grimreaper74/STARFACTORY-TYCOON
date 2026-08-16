from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_installed_cell_v557.py").read_text(encoding="utf-8")
source = source.replace("v557", "v558").replace("V557", "V558")
exec(compile(source, str(Path(__file__).parent / "capture_inbound_installed_cell_v557.py"), "exec"), globals(), globals())
