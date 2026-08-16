"""Capture one detailed PR-008 Module 07 fixed camera per Unreal process."""
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr008_module06_v069.py")
code = base.read_text(encoding="utf-8")
code = code.replace("v069", "v070").replace("V069", "V070")
code = code.replace("Module06", "Module07").replace("module06", "module07")
exec(compile(code, str(base) + "::v070-adapter", "exec"), globals(), globals())
