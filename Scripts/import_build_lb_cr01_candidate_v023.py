"""Import LB-CR01 v023 LOD0 components and build an isolated UE 5.8 evidence map."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE=ROOT/"SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v023/LB_CR01_FullRobot_LOD0_v023.fbx"
DEST="/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v023/LOD0"
MAP="/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v023"
AUDIT=ROOT/"Saved/Audits/lb_cr01_candidate_v023_unreal_import.json"

if not SOURCE.exists(): raise RuntimeError(f"Missing source {SOURCE}")
if unreal.EditorAssetLibrary.does_asset_exist(MAP) or unreal.EditorAssetLibrary.does_directory_exist(DEST):
    raise RuntimeError("v023 evidence destination already exists; preserve candidate evidence")

task=unreal.AssetImportTask(); task.set_editor_properties({"filename":str(SOURCE),"destination_path":DEST,"automated":True,"replace_existing":False,"save":True})
opts=unreal.FbxImportUI(); opts.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH})
data=opts.get_editor_property("static_mesh_import_data")
data.set_editor_properties({"combine_meshes":False,"convert_scene":True,"convert_scene_unit":True,"force_front_x_axis":False,"generate_lightmap_u_vs":True,"auto_generate_collision":False,"remove_degenerates":True})
task.set_editor_property("options",opts)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

mesh_paths=[]
for p in unreal.EditorAssetLibrary.list_assets(DEST,recursive=False,include_folder=False):
    a=unreal.load_asset(p)
    if isinstance(a,unreal.StaticMesh): mesh_paths.append(p)
if len(mesh_paths)<450: raise RuntimeError(f"Modular import incomplete: {len(mesh_paths)} meshes")

levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.new_level(MAP): raise RuntimeError(f"Could not create {MAP}")
created=[]
moving_tokens=("WHEEL","CASTER","BRUSH","SCRUB","SQUEEGEE","HOPPER","DOOR","LATCH","LID","LIFT","PIVOT")
for p in mesh_paths:
    mesh=unreal.load_asset(p); actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(),unreal.Rotator())
    name=mesh.get_name(); actor.set_actor_label("LB_CR01_V023_"+name)
    comp=actor.get_editor_property("static_mesh_component"); comp.set_static_mesh(mesh)
    mover=any(t in name.upper() for t in moving_tokens); comp.set_editor_property("mobility",unreal.ComponentMobility.MOVABLE if mover else unreal.ComponentMobility.STATIC)
    actor.set_editor_property("tags",[unreal.Name("LB.SupportRobot.LB-CR01"),unreal.Name("LB.Asset.Candidate.v023"),unreal.Name("LB.Motion.Mover" if mover else "LB.Motion.Static")])
    created.append({"mesh":p,"mover":mover})

cube=unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-3),unreal.Rotator()); floor.set_actor_label("LB_CR01_V023_ValidationFloor"); floor.get_editor_property("static_mesh_component").set_static_mesh(cube); floor.set_actor_scale3d(unreal.Vector(5,5,.05))
datum=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(130,80,90),unreal.Rotator()); datum.set_actor_label("LB_CR01_V023_1800mm_Datum"); datum.get_editor_property("static_mesh_component").set_static_mesh(cube); datum.set_actor_scale3d(unreal.Vector(.1,.1,1.8))

sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,400),unreal.Rotator(-42,-35,0)); sun.set_actor_label("LB_CR01_V023_KeyLight"); sun.get_editor_property("directional_light_component").set_editor_property("intensity",3.2)
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,300),unreal.Rotator()); sky.set_actor_label("LB_CR01_V023_SkyLight"); sky.get_editor_property("light_component").set_editor_property("intensity",.45)
for label,loc,intensity,color in (("FillFront",unreal.Vector(260,-260,260),900,unreal.Color(255,225,205,255)),("FillRear",unreal.Vector(-220,220,190),550,unreal.Color(190,215,255,255))):
    light=actors.spawn_actor_from_class(unreal.PointLight,loc,unreal.Rotator()); light.set_actor_label("LB_CR01_V023_"+label); c=light.get_editor_property("point_light_component"); c.set_editor_properties({"intensity":intensity,"attenuation_radius":650,"light_color":color})

cameras=(("Oblique",unreal.Vector(285,-320,215),unreal.Vector(0,0,48),46.),("Side",unreal.Vector(0,-360,105),unreal.Vector(0,0,48),42.),("Top",unreal.Vector(0,0,420),unreal.Vector(0,0,30),36.))
for label,loc,target,fov in cameras:
    cam=actors.spawn_actor_from_class(unreal.CameraActor,loc,unreal.Rotator()); cam.set_actor_label("LB_CR01_V023_CAM_"+label); cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,target),False); cam.get_editor_property("camera_component").set_editor_property("field_of_view",fov)

if not levels.save_current_level(): raise RuntimeError("Could not save v023 evidence map")
bounds=[unreal.load_asset(p).get_bounding_box() for p in mesh_paths]
minimum=[min(b.min.to_tuple()[i] for b in bounds) for i in range(3)]; maximum=[max(b.max.to_tuple()[i] for b in bounds) for i in range(3)]; size=[maximum[i]-minimum[i] for i in range(3)]
result={"status":"CANDIDATE_NOT_PROMOTED__UNREAL_VISUAL_REVIEW_REQUIRED","source":str(SOURCE),"destination":DEST,"map":MAP,"mesh_count":len(mesh_paths),"mover_count":sum(x["mover"] for x in created),"aggregate_bounds_cm":{"min":minimum,"max":maximum,"size":size},"authoritative_envelope_cm":[152,98,112],"bounds_tolerance_cm":.2,"bounds_pass":all(abs(a-b)<=.2 for a,b in zip(size,[152,98,112])),"fixed_cameras":["LB_CR01_V023_CAM_"+x[0] for x in cameras]}
AUDIT.parent.mkdir(parents=True,exist_ok=True); AUDIT.write_text(json.dumps(result,indent=2),encoding='utf-8')
unreal.log(f"LINE_BOSS_LB_CR01_V023_IMPORT_PASS meshes={len(mesh_paths)} movers={result['mover_count']} bounds={size}")
