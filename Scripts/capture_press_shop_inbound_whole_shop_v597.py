"""Single-shot interior whole-shop evidence capture for v597."""
from pathlib import Path
source = (Path(__file__).parent / "capture_press_shop_inbound_whole_shop_v596.py").read_text(encoding="utf-8")
source = source.replace("v596", "v597").replace("V596", "V597")
exec(compile(source, str(Path(__file__).parent / "capture_press_shop_inbound_whole_shop_v596.py"), "exec"), globals(), globals())
