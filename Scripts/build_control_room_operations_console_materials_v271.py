"""Create exposure-compensated PBR console materials; preserve v270 unchanged."""

from pathlib import Path


source = Path(__file__).with_name("build_control_room_operations_console_materials_v270.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v270", "v271").replace("V270", "V271")
code = code.replace("(0.004, 0.010, 0.008)", "(0.00008, 0.00020, 0.00014)")
code = code.replace("(0.012, 0.016, 0.017)", "(0.00014, 0.00018, 0.00020)")
exec(compile(code, str(source) + "::v271", "exec"), globals(), globals())
