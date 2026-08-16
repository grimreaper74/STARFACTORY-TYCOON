from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_installed_cell_v564.py").read_text(encoding="utf-8")
source = source.replace("v564", "v567").replace("V564", "V567")
exec(compile(source, str(Path(__file__).parent / "capture_inbound_installed_cell_v564.py"), "exec"), globals(), globals())
