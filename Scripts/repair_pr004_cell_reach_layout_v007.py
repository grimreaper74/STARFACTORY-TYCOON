"""Apply the proven PR-004 reach/rack correction to isolated Candidate_v007."""

from pathlib import Path


source_path = Path(__file__).resolve().with_name("repair_pr004_cell_reach_layout_v004.py")
source = source_path.read_text(encoding="utf-8")
source = source.replace("Candidate_v004", "Candidate_v007")
source = source.replace("candidate_v004", "candidate_v007")
source = source.replace("_v004.json", "_v007.json")
source = source.replace("/v004/v1", "/v007/v1")
source = source.replace("film_count != 11", "film_count != 14")
source = source.replace("film={film_count}/11", "film={film_count}/14")
source = source.replace("LINE_BOSS_PR004_REACH_LAYOUT_V004_PASS", "LINE_BOSS_PR004_REACH_LAYOUT_V007_PASS")
exec(compile(source, str(source_path), "exec"), globals(), globals())
unreal.SystemLibrary.quit_editor()
