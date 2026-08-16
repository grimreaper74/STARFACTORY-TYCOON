"""Single-shot process evidence capture for v597."""
from pathlib import Path
source = (Path(__file__).parent / "capture_press_shop_inbound_handoff_v596.py").read_text(encoding="utf-8")
source = source.replace("v596", "v597").replace("V596", "V597")
source = source.replace("LB_CAM_InboundRelease_Handoff_v597", "LB_CAM_InboundRelease_Process_v597")
source = source.replace("inbound_handoff_to_pr003.png", "inbound_process_context.png")
source = source.replace("HANDOFF_CAPTURE", "PROCESS_CAPTURE")
exec(compile(source, str(Path(__file__).parent / "capture_press_shop_inbound_handoff_v596.py"), "exec"), globals(), globals())
