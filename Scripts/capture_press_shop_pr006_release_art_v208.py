"""Capture live fixed PR-006 release-art views on exact v208."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_pr006_release_art_v207.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v207", "v208").replace("V207", "V208")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
