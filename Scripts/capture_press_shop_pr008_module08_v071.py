"""Capture one detailed PR-008 Module 08 fixed camera per Unreal process."""
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr008_module07_v070.py")
code = base.read_text(encoding="utf-8")
code = code.replace("v070", "v071").replace("V070", "V071")
code = code.replace("Module07", "Module08").replace("module07", "module08")
exec(compile(code, str(base) + "::v071-adapter", "exec"), globals(), globals())
