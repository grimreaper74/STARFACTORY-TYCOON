"""Safely named entrypoint for the exact v295 gate selector."""
from pathlib import Path
source = Path(__file__).with_name("run_exact_press_shop_v295_gate.py")
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
