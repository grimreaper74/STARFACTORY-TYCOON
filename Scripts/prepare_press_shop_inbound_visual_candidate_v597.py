"""Prepare corrected visual successor v597 from retained technical v586."""
from pathlib import Path
source = (Path(__file__).parent / "prepare_press_shop_inbound_visual_candidate_v596.py").read_text(encoding="utf-8")
source = source.replace("v596", "v597").replace("V596", "V597")
exec(compile(source, str(Path(__file__).parent / "prepare_press_shop_inbound_visual_candidate_v596.py"), "exec"), globals(), globals())
