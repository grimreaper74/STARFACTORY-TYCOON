"""Build fresh v516 via Unreal level Save As, avoiding v515 duplicate-world lifetime failure."""
from pathlib import Path

source=(Path(__file__).parent/"build_inbound_installed_cell_v515.py").read_text(encoding="utf-8")
source=source.replace("v515","v516").replace("V515","V516")
old='''if library.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing overwrite {MAP}")
if not library.duplicate_asset(SRC, MAP):
    raise RuntimeError("Could not duplicate retained v514 into fresh v516")
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v516")'''
new='''if library.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing overwrite {MAP}")
if not levels.load_level(SRC):
    raise RuntimeError("Could not load retained v514")
if not unreal.EditorLevelLibrary.save_current_level_as(MAP):
    raise RuntimeError("Could not save fresh v516 from retained v514")'''
if old not in source:
    raise RuntimeError("v516 Save As patch anchor not found")
source=source.replace(old,new)
exec(compile(source,str(Path(__file__)),"exec"),globals(),globals())
