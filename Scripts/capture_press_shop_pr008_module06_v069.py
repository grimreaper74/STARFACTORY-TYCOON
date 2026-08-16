"""Capture one detailed PR-008 Module 06 fixed camera per Unreal process."""
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr008_module05_v068.py")
code = base.read_text(encoding="utf-8")
code = code.replace("v068", "v069").replace("V068", "V069")
code = code.replace("Module05", "Module06").replace("module05", "module06")
exec(compile(code, str(base) + "::v069-adapter", "exec"), globals(), globals())
