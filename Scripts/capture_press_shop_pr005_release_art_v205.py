"""Capture one inherited fixed PR005 camera on release-art candidate v205."""

import os
from pathlib import Path

os.environ["LB_PR005_V196_CAPTURE"] = os.environ.get(
    "LB_PR005_V205_CAPTURE", "operator_player")
source = Path(__file__).with_name("capture_press_shop_pr005_release_art_v199.py")
code = source.read_text(encoding="utf-8").replace("v199", "v205").replace("V199", "V205")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
