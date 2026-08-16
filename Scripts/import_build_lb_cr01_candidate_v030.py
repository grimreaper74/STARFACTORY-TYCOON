"""Import the dimension-locked CR01 v030 enclosure candidate into Unreal."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE=ROOT/"SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v030/LB_CR01_FullRobot_LOD0_XForward_v030.fbx"
DEST="/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v030/LOD0"
MAP="/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v030"
AUDIT=ROOT/"Saved/Audits/lb_cr01_candidate_v030_unreal_import.json"
EXPECTED=[152.0,98.0,112.0]
if not SOURCE.exists(): raise RuntimeError(f"Missing {SOURCE}")
if unreal.EditorAssetLibrary.does_asset_exist(MAP) or unreal.EditorAssetLibrary.does_directory_exist(DEST):
    raise RuntimeError("v030 destination already exists; preserve candidate evidence")

task=unreal.AssetImportTask(); task.set_editor_properties({"filename":str(SOURCE),"destination_path":DEST,"automated":True,"replace_existing":False,"save":True})
opts=unreal.FbxImportUI(); opts.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH})
opts.get_editor_property("static_mesh_import_data").set_editor_properties({"combine_meshes":False,"convert_scene":True,"convert_scene_unit":True,"force_front_x_axis":True,"generate_lightmap_u_vs":True,"auto_generate_collision":False,"remove_degenerates":True})
task.set_editor_property("options",opts)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

mesh_paths=[]
for path in unreal.EditorAssetLibrary.list_assets(DEST,recursive=False,include_folder=False):
    if isinstance(unreal.load_asset(path),unreal.StaticMesh): mesh_paths.append(path)
if len(mesh_paths)<560: raise RuntimeError(f"Incomplete modular import: {len(mesh_paths)}")
bounds=[unreal.load_asset(path).get_bounding_box() for path in mesh_paths]
minimum=[min(box.min.to_tuple()[axis] for box in bounds) for axis in range(3)]
maximum=[max(box.max.to_tuple()[axis] for box in bounds) for axis in range(3)]
size=[maximum[axis]-minimum[axis] for axis in range(3)]
bounds_pass=all(abs(a-e)<=0.2 for a,e in zip(size,EXPECTED))
if not bounds_pass: raise RuntimeError(f"v030 bounds failed: {size}")

levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.new_level(MAP): raise RuntimeError(f"Could not create {MAP}")
moving_tokens=("WHEEL","CASTER","BRUSH","SCRUB","SQUEEGEE","HOPPER","DOOR","LATCH","LID","LIFT","PIVOT","HINGE")
created=[]
for path in mesh_paths:
    mesh=unreal.load_asset(path); name=mesh.get_name()
    actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(),unreal.Rotator()); actor.set_actor_label("LB_CR01_V030_"+name)
    component=actor.get_editor_property("static_mesh_component"); component.set_static_mesh(mesh)
    mover=any(token in name.upper() for token in moving_tokens)
    component.set_editor_property("mobility",unreal.ComponentMobility.MOVABLE if mover else unreal.ComponentMobility.STATIC)
    actor.set_editor_property("tags",[unreal.Name("LB.SupportRobot.LB-CR01"),unreal.Name("LB.Asset.Candidate.v030"),unreal.Name("LB.Motion.Mover" if mover else "LB.Motion.Static")])
    created.append((name,mover))

cube=unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-3),unreal.Rotator()); floor.set_actor_label("LB_CR01_V030_ValidationFloor"); floor.get_editor_property("static_mesh_component").set_static_mesh(cube); floor.set_actor_scale3d(unreal.Vector(5,5,0.05))
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,400),unreal.Rotator(-42,-35,0)); sun.set_actor_label("LB_CR01_V030_KeyLight"); sun.get_editor_property("directional_light_component").set_editor_property("intensity",2.2)
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,300),unreal.Rotator()); sky.set_actor_label("LB_CR01_V030_SkyLight"); sky.get_editor_property("light_component").set_editor_property("intensity",0.5)
for label,location,intensity in (("FillLeft",unreal.Vector(0,-270,150),650),("FillRight",unreal.Vector(0,270,150),650),("FillFront",unreal.Vector(270,-180,210),500)):
    light=actors.spawn_actor_from_class(unreal.PointLight,location,unreal.Rotator()); light.set_actor_label("LB_CR01_V030_"+label); light.get_editor_property("point_light_component").set_editor_properties({"intensity":intensity,"attenuation_radius":650})
camera_specs=(("Oblique",unreal.Vector(330,-350,225),48.0),("Left",unreal.Vector(0,-430,120),43.0),("Right",unreal.Vector(0,430,120),43.0),("Top",unreal.Vector(0,0,575),47.0))
for label,location,fov in camera_specs:
    camera=actors.spawn_actor_from_class(unreal.CameraActor,location,unreal.Rotator()); camera.set_actor_label("LB_CR01_V030_CAM_"+label); camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location,unreal.Vector(0,0,48)),False); camera.get_editor_property("camera_component").set_editor_property("field_of_view",fov)
if not levels.save_current_level(): raise RuntimeError("Could not save v030 map")
result={"status":"CANDIDATE_NOT_PROMOTED__VISUAL_AND_RUNTIME_GATES_REQUIRED","source":str(SOURCE),"destination":DEST,"map":MAP,"mesh_count":len(mesh_paths),"mover_count":sum(1 for _,m in created if m),"aggregate_bounds_cm":{"min":minimum,"max":maximum,"size":size},"bounds_pass":bounds_pass,"fixed_cameras":["LB_CR01_V030_CAM_"+item[0] for item in camera_specs]}
AUDIT.parent.mkdir(parents=True,exist_ok=True); AUDIT.write_text(json.dumps(result,indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_LB_CR01_V030_IMPORT_PASS meshes={len(mesh_paths)} bounds={size}")
