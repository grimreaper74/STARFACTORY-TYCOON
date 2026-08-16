"""Fresh renderer recheck of unchanged v270 without overwriting earlier evidence."""
from pathlib import Path
source = Path(__file__).with_name("capture_press_shop_mr01_modular_dock_comparison_v270.py")
code = source.read_text(encoding="utf-8").replace("press_shop_mr01_dock_pair_v270.png", "press_shop_mr01_dock_pair_v270_recheck_v275.png")
exec(compile(code, str(source) + "::recheck-v275", "exec"), globals(), globals())
