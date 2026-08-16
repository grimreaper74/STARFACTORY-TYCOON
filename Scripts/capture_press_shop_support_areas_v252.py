"""Capture v252 structured support views through transient fixed cameras."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_support_areas_v250.py")
code = source.read_text(encoding="utf-8").replace("v250", "v252").replace("V250", "V252")
exec(compile(code, str(source) + "::v252", "exec"), globals(), globals())
