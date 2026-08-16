"""Fresh high/wide process successor retaining v518 geometry and exposure recipe."""
from pathlib import Path
import unreal

root=Path(__file__).parent
source=(root/"build_inbound_installed_cell_v518.py").read_text(encoding="utf-8")
source=source.replace("v518","v519").replace("V518","V519").replace("V018_","V019_")
exec(compile(source,str(root/"build_inbound_installed_cell_v518.py"),"exec"),globals(),globals())

actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
camera=next((a for a in actors.get_all_level_actors() if isinstance(a,unreal.CameraActor)),None)
if camera is None:
    raise RuntimeError("Missing v519 camera")
camera.set_actor_label("LB_CAM_InboundCoilDelivery_OperationalReadability_v519")
camera.set_actor_location(unreal.Vector(2850,3050,2050),False,False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(120,160,230)),False)
camera.camera_component.set_editor_properties({"field_of_view":58.0,"aspect_ratio":16/9,"constrain_aspect_ratio":True})

# Pull the moving load slightly toward the open side of the bay while keeping
# trolley, hoist, powered C-hook and carried coil aligned on one vertical datum.
for actor in actors.get_all_level_actors():
    label=actor.get_actor_label()
    if any(label.endswith(token) for token in ("CraneTrolley","HoistBlock","PoweredCHook","CHook_CarriedCoil")):
        loc=actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(-180,620,loc.z),False,False)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v519 high/wide successor")
unreal.log("LINE_BOSS_INBOUND_INSTALLED_CELL_V519_BUILD_PASS")
