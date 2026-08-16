"""Build clean v207 after preserving the stopped v206 material-slot intake."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_pr006_release_art_candidate_v206.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v206", "v207").replace("V206", "V207")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
