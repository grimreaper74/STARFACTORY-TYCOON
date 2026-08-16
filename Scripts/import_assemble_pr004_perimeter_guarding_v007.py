"""Assemble the existing 2.4 m PR-004 perimeter kit in Candidate_v007."""

from pathlib import Path


source_path = Path(__file__).resolve().with_name("import_assemble_pr004_perimeter_guarding_v002.py")
source = source_path.read_text(encoding="utf-8")
source = source.replace("Candidate_v004", "Candidate_v007")
source = source.replace("candidate_v004", "candidate_v007")
source = source.replace("pr004_perimeter_guarding_candidate_v002.json", "pr004_perimeter_guarding_candidate_v007.json")
source = source.replace("CANDIDATE_V002_PASS", "CANDIDATE_V007_PASS")
exec(compile(source, str(source_path), "exec"), globals(), globals())
unreal.SystemLibrary.quit_editor()
