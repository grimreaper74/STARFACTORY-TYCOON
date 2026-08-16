"""Short commandlet entry point for the PR-004 v008 pivot repair."""

from pathlib import Path


target = Path(__file__).resolve().with_name("repair_pr004_candidate_v008_assembly_pivots.py")
exec(compile(target.read_text(encoding="utf-8"), str(target), "exec"), globals(), globals())
