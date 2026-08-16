"""Single-shot handoff evidence capture for v597."""
from pathlib import Path
source = (Path(__file__).parent / "capture_press_shop_inbound_handoff_v596.py").read_text(encoding="utf-8")
source = source.replace("v596", "v597").replace("V596", "V597")
exec(compile(source, str(Path(__file__).parent / "capture_press_shop_inbound_handoff_v596.py"), "exec"), globals(), globals())
