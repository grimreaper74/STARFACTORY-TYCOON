"""Read-only effective material control from the earlier green/charcoal v270 evidence."""
from pathlib import Path
source = Path(__file__).with_name("audit_press_shop_native_service_dock_materials_v274.py")
code = source.read_text(encoding="utf-8").replace("v273", "v270").replace("V273", "V270").replace("v274", "v275").replace("V274", "V275")
exec(compile(code, str(source) + "::v270-control-v275", "exec"), globals(), globals())
