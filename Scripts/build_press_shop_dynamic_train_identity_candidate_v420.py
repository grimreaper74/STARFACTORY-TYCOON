"""Fresh direct-v386 dynamic identity with clean board and west-facing text."""
from pathlib import Path
source=Path(__file__).with_name("build_press_shop_dynamic_train_identity_candidate_v418.py")
code=source.read_text(encoding="utf-8").replace("PhysicalSigns_v411","PhysicalSigns_v397").replace("_v410","_v396").replace("v418","v420")
code=code.replace("unreal.TextRenderActor,unreal.Vector(1106,y,850),unreal.Rotator())","unreal.TextRenderActor,unreal.Vector(1106,y,850),unreal.Rotator(yaw=180.0))")
exec(compile(code,str(source),"exec"),{"__name__":"__main__","__file__":str(source)})
