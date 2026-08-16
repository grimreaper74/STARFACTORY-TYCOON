"""Fresh v023 direct from v017 using verified UE 5.8 reflected nav properties."""

from pathlib import Path

source = Path(__file__).resolve().parent / "build_press_train_a_physical_gameplay_candidate_v022.py"
code = source.read_text(encoding="utf-8").replace("v022", "v023").replace("V022", "V023")
code = code.replace('"strictly_static"', '"bStrictlyStatic"')
code = code.replace('"auto_spawn_missing_nav_data"', '"bAutoSpawnMissingNavData"')
code = code.replace('"spawn_nav_data_in_nav_bounds_level"', '"bSpawnNavDataInNavBoundsLevel"')
exec(compile(code, str(source) + "::v023", "exec"), globals(), globals())
