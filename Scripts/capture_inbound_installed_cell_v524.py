from pathlib import Path
source = (Path(__file__).parent / "capture_inbound_installed_cell_v522.py").read_text(encoding="utf-8")
source = source.replace("v522", "v524").replace("V522", "V524")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
