"""Capture v251 structured support views through transient fixed cameras."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_support_areas_v250.py")
code = source.read_text(encoding="utf-8").replace("v250", "v251").replace("V250", "V251")
exec(compile(code, str(source) + "::v251", "exec"), globals(), globals())
