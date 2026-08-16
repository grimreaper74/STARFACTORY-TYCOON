"""Restore visible donor cells with exact Unreal Rotator ordering in a fresh v273 child."""
from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr006_pr008_visible_complete_cell_candidate_v286.py")
wrapper = source.read_text(encoding="utf-8").replace("v286", "v287").replace("V286", "V287")
wrapper = wrapper.replace(
    'unreal.Rotator(*row["rotation"])',
    'unreal.Rotator(row["rotation"][2], row["rotation"][0], row["rotation"][1])',
)
wrapper = wrapper.replace(
    'unreal.Rotator(*rotation)',
    'unreal.Rotator(rotation[2], rotation[0], rotation[1])',
)
exec(compile(wrapper, str(source) + "::rotator-correct-visible-complete-cell-v287", "exec"), globals(), globals())
