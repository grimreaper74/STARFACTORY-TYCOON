"""Fresh visual successor to v514; preserves v514 intake and immutable v438."""
from pathlib import Path
import json
import unreal

SRC = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v514"
MAP = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v515"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_installed_cell_build_v515.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing overwrite {MAP}")
if not library.duplicate_asset(SRC, MAP):
    raise RuntimeError("Could not duplicate retained v514 into fresh v515")
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v515")

# The old camera-facing backdrop becomes an occluder from the crane-side view.
for actor in list(actors.get_all_level_actors()):
    label = actor.get_actor_label()
    if "Backdrop" in label:
        actors.destroy_actor(actor)
    elif "LB_INBOUND_V014_" in label:
        actor.set_actor_label(label.replace("LB_INBOUND_V014_", "LB_INBOUND_V015_"))

materials = {
    "yellow": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_SafetyYellow_v001"),
    "dark": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001"),
    "steel": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_BrushedSteel_v001"),
    "rubber": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Rubber_v001"),
    "green": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_GreenLamp_v001"),
}
if any(value is None for value in materials.values()):
    raise RuntimeError("Missing controlled inbound material instances")

remapped=[]
for actor in actors.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor) or "InboundCrane" not in str(actor.static_mesh_component.static_mesh):
        continue
    mesh=actor.static_mesh_component.static_mesh
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        name=str(slot.get_editor_property("material_slot_name")).lower()
        key=("yellow" if "ral1023" in name else "dark" if "darksteel" in name else
             "steel" if "machinedsteel" in name else "rubber" if "rubber" in name else
             "green" if "statusgreen" in name else None)
        if key:
            actor.static_mesh_component.set_material(index, materials[key])
            remapped.append([actor.get_actor_label(),index,key])

# Add a simple sealed rear wall behind the lorry, keeping the crane-side process
# view open and readable. This is review context only, not production authority.
cube=library.load_asset("/Engine/BasicShapes/Cube.Cube")
wall=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,-1450,390),unreal.Rotator())
wall.set_actor_label("LB_INBOUND_V015_RearFactoryWall")
wall.set_actor_scale3d(unreal.Vector(18,.18,8))
wall.static_mesh_component.set_static_mesh(cube)
wall.static_mesh_component.set_material(0,materials["dark"])
wall.tags=[unreal.Name("LB.Environment.ReviewOnly")]

camera=next((a for a in actors.get_all_level_actors() if isinstance(a,unreal.CameraActor)),None)
if camera is None:
    raise RuntimeError("Missing retained fixed camera")
camera.set_actor_label("LB_CAM_InboundCoilDelivery_OperationalReadability_v515")
camera.set_actor_location(unreal.Vector(2350,2650,1380),False,False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(100,250,220)),False)
camera.camera_component.set_editor_properties({"field_of_view":50.0,"aspect_ratio":16/9,"constrain_aspect_ratio":True})

def rect(label,location,target,intensity,width,height):
    light=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(*location),unreal.Rotator())
    light.set_actor_label(label)
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(),unreal.Vector(*target)),False)
    light.rect_light_component.set_editor_properties({"intensity":intensity,"attenuation_radius":4500.0,
        "source_width":width,"source_height":height})
    light.tags=[unreal.Name("LB.Environment.ReviewOnly")]

rect("LB_INBOUND_V015_Light_ProcessSide",(1500,1800,1250),(0,300,250),850,1000,600)
rect("LB_INBOUND_V015_Light_LorryFill",(-900,-500,900),(0,-150,200),700,800,450)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v515")
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"status":"VISUAL_REVIEW_REQUIRED__NOT_PROMOTED","map":MAP,
    "source_map":SRC,"controlled_material_remaps":remapped,"backdrop_occluder_removed":True,
    "authority_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_INSTALLED_CELL_V515_BUILD_PASS")
