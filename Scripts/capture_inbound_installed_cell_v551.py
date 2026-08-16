from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_installed_cell_v550.py").read_text(encoding="utf-8")
source = source.replace("v550", "v551").replace("V550", "V551")
exec(compile(source, str(Path(__file__).parent / "capture_inbound_installed_cell_v550.py"), "exec"), globals(), globals())
