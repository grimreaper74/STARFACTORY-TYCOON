"""Exact v205 PR005 state-driven spatial-audio wrapper."""

from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr005_audio_runtime_pie_v198.py")
code = source.read_text(encoding="utf-8").replace("v198", "v205").replace("V198", "V205")
code = code.replace("PR005AudioRuntimeCandidate_v205", "PR005ReleaseArtCandidate_v205")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
