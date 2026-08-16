"""Rebuild the corrected visible complete cells as a fresh direct child of v273."""
from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr006_pr008_visible_complete_cell_candidate_v287.py")
code = source.read_text(encoding="utf-8").replace("v287", "v288").replace("V287", "V288")
exec(compile(code, str(source) + "::fresh-direct-child-v288", "exec"), globals(), globals())
