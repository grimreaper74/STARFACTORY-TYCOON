"""Non-overwriting v273 capture after all asset/material compilation completes."""
from pathlib import Path
source = Path(__file__).with_name("capture_press_shop_native_service_docks_v273.py")
code = source.read_text(encoding="utf-8").replace("_pair.png", "_pair_compiled_v276.png")
exec(compile(code, str(source) + "::compiled-v276", "exec"), globals(), globals())
