"""Fresh camera-mirrored successor to the Pro-aligned v520 geometry."""
from pathlib import Path
import unreal

root=Path(__file__).parent
source=(root/"build_inbound_installed_cell_v520.py").read_text(encoding="utf-8")
source=source.replace("v520","v521").replace("V520","V521").replace("V020_","V021_")
exec(compile(source,str(root/"build_inbound_installed_cell_v520.py"),"exec"),globals(),globals())
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
camera=next((a for a in actors.get_all_level_actors() if isinstance(a,unreal.CameraActor)),None)
if camera is None:
    raise RuntimeError("Missing v521 camera")
camera.set_actor_label("LB_CAM_InboundCoilDelivery_OperationalReadability_v521")
camera.set_actor_location(unreal.Vector(-2850,-3300,1750),False,False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(0,0,230)),False)
camera.camera_component.set_editor_properties({"field_of_view":52.0,"aspect_ratio":16/9,"constrain_aspect_ratio":True})
if not levels.save_current_level():
    raise RuntimeError("Failed saving v521 mirrored process camera")
unreal.log("LINE_BOSS_INBOUND_INSTALLED_CELL_V521_BUILD_PASS")
