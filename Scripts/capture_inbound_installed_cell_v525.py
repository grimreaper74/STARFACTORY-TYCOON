from pathlib import Path
source = (Path(__file__).parent / "capture_inbound_installed_cell_v524.py").read_text(encoding="utf-8")
source = source.replace("v524", "v525").replace("V524", "V525")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
