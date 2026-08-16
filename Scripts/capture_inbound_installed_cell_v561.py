from pathlib import Path

source = (Path(__file__).parent / "capture_inbound_installed_cell_v558.py").read_text(encoding="utf-8")
source = source.replace("v558", "v561").replace("V558", "V561")
exec(compile(source, str(Path(__file__).parent / "capture_inbound_installed_cell_v558.py"), "exec"), globals(), globals())
