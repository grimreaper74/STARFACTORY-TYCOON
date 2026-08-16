"""Fresh Pro-aligned left-to-right inbound process layout; v438 remains untouched."""
from pathlib import Path
import unreal

root=Path(__file__).parent
source=(root/"build_inbound_installed_cell_v517.py").read_text(encoding="utf-8")
source=source.replace("v517","v520").replace("V517","V520").replace("V017_","V020_")
exec(compile(source,str(root/"build_inbound_installed_cell_v517.py"),"exec"),globals(),globals())

actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def find(suffix):
    return next((a for a in actors.get_all_level_actors() if a.get_actor_label().endswith(suffix)),None)
def place(suffix,loc,yaw=None):
    actor=find(suffix)
    if actor is None:
        raise RuntimeError(f"Missing v520 actor {suffix}")
    actor.set_actor_location(unreal.Vector(*loc),False,False)
    if yaw is not None:
        actor.set_actor_rotation(unreal.Rotator(0,0,yaw),False)
    return actor

# Rotate the dock/lorry group from the inherited north-south review into the
# Pro reference's readable left-to-right process sequence.
place("LorryCab",(-1580,0,152),90)
place("CoilTrailer",(-720,0,188),-90)
place("DockGuidesAndRestraint",(-720,0,35),-90)
place("EntranceDockEnvelope",(-1330,0,244),-90)
place("DockControlAndSignals",(-1120,-330,125),-90)

# Installed crane and moving load occupy the protected central bay.
place("StaticRunwayFrame",(0,0,0),0)
place("MovingBridge",(0,0,652),0)
place("CraneTrolley",(0,0,715),0)
place("HoistBlock",(0,0,500),0)
place("PoweredCHook",(0,0,315),90)
place("CHook_CarriedCoil",(0,-50,256),0)

# Fixed set-down and AGV handoff continue to the right of the crane bay.
place("ReceivingSaddle",(760,0,70),0)
place("IdentityScanner",(760,-260,93),0)
place("AGVHandoffGuides",(1280,0,37),0)
place("AGV_Chassis",(1280,0,45),0)
place("AGV_Deck",(1280,0,83),0)
place("AGV_LoadedCoil",(1280,0,185),0)

wall=find("RearFactoryWall")
wall.set_actor_location(unreal.Vector(0,1050,390),False,False)
floor=find("Floor")
floor.set_actor_location(unreal.Vector(0,0,-12),False,False)
floor.set_actor_scale3d(unreal.Vector(24,20,.24))

camera=next((a for a in actors.get_all_level_actors() if isinstance(a,unreal.CameraActor)),None)
if camera is None:
    raise RuntimeError("Missing v520 camera")
camera.set_actor_label("LB_CAM_InboundCoilDelivery_OperationalReadability_v520")
camera.set_actor_location(unreal.Vector(2850,-3300,1850),False,False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(0,0,230)),False)
camera.camera_component.set_editor_properties({"field_of_view":56.0,"aspect_ratio":16/9,"constrain_aspect_ratio":True})

# Re-aim review lights onto the new linear material-flow axis.
for actor in actors.get_all_level_actors():
    if isinstance(actor,unreal.RectLight):
        actor.rect_light_component.set_editor_property("intensity",actor.rect_light_component.get_editor_property("intensity")*.62)
light=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(0,-900,1200),unreal.Rotator())
light.set_actor_label("LB_INBOUND_V020_Light_LinearProcessFill")
light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(),unreal.Vector(0,0,200)),False)
light.rect_light_component.set_editor_properties({"intensity":650.0,"attenuation_radius":4500.0,"source_width":1600.0,"source_height":700.0})
light.tags=[unreal.Name("LB.Environment.ReviewOnly")]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v520 Pro-aligned process layout")
unreal.log("LINE_BOSS_INBOUND_INSTALLED_CELL_V520_BUILD_PASS")
