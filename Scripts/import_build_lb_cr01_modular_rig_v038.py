"""Import and assemble the pivot-correct CR01 v038 modular runtime candidate."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE=ROOT/"SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v038_ModularRig"
DEST="/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v038_ModularRig"
MAP="/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_ModularRig_v038"
SEQ_DIR=DEST+"/Sequences"; SEQ_NAME="LS_LB_CR01_CleaningCycle_v038"; SEQ_PATH=SEQ_DIR+"/"+SEQ_NAME
AUDIT=ROOT/"Saved/Audits/lb_cr01_modular_rig_v038.json"
asset_lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools()
if asset_lib.does_asset_exist(MAP): raise RuntimeError("Preserve existing v038 evidence; validation map already exists")

fbx_files=sorted(SOURCE.glob("*.fbx"))
if len(fbx_files)!=16: raise RuntimeError(f"Expected 16 modular FBXs, found {len(fbx_files)}")
if not asset_lib.does_directory_exist(DEST):
    tasks=[]
    for fbx in fbx_files:
        task=unreal.AssetImportTask(); task.set_editor_properties({"filename":str(fbx),"destination_path":DEST,"automated":True,"replace_existing":False,"save":True})
        opts=unreal.FbxImportUI(); opts.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH})
        opts.get_editor_property("static_mesh_import_data").set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"force_front_x_axis":True,"transform_vertex_to_absolute":False,"generate_lightmap_u_vs":True,"auto_generate_collision":False,"remove_degenerates":True})
        task.set_editor_property("options",opts); tasks.append(task)
    tools.import_asset_tasks(tasks); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

mesh_paths=[p for p in asset_lib.list_assets(DEST,recursive=False,include_folder=False) if isinstance(unreal.load_asset(p),unreal.StaticMesh)]
meshes={unreal.load_asset(p).get_name().removesuffix("_XForward_v038"):unreal.load_asset(p) for p in mesh_paths}
required=("SM_LB_CR01_BodyStatic","SM_FrontBrushLift","SM_FrontBrushSpin","SM_ScrubDeckLift","SM_ScrubDisc_L","SM_ScrubDisc_R","SM_SideBrushArm_L","SM_SideBrushArm_R","SM_SideBrushSpin_L","SM_SideBrushSpin_R","SM_SqueegeeLift","SM_SqueegeeYaw","SM_LB_CR01_Condition_Mothballed_Body","SM_LB_CR01_Condition_Mothballed_Squeegee","SM_LB_CR01_Condition_Restored_Body","SM_LB_CR01_Condition_Restored_Squeegee")
missing=[n for n in required if n not in meshes]
if missing: raise RuntimeError(f"Missing imported modules: {missing}; got {sorted(meshes)}")

levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors_api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.new_level(MAP): raise RuntimeError(f"Could not create {MAP}")
pivots={
 "SM_LB_CR01_BodyStatic":(0,0,0), "SM_LB_CR01_Condition_Mothballed_Body":(0,0,0), "SM_LB_CR01_Condition_Restored_Body":(0,0,0),
 "SM_FrontBrushLift":(63.5,0,16.5), "SM_FrontBrushSpin":(63.5,0,12.5),
 "SM_ScrubDeckLift":(4,0,18.5), "SM_ScrubDisc_L":(4,-17.5,7.5), "SM_ScrubDisc_R":(4,17.5,7.5),
 "SM_SideBrushArm_L":(45,-33,15.5), "SM_SideBrushArm_R":(45,33,15.5),
 "SM_SideBrushSpin_L":(52,-50,8), "SM_SideBrushSpin_R":(52,50,8),
 "SM_SqueegeeLift":(-69,0,16.5), "SM_SqueegeeYaw":(-69,0,10),
 "SM_LB_CR01_Condition_Mothballed_Squeegee":(-69,0,10), "SM_LB_CR01_Condition_Restored_Squeegee":(-69,0,10),
}
actors={}
for name in required:
    a=actors_api.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*pivots[name]),unreal.Rotator()); a.set_actor_label("LB_CR01_V038_"+name)
    c=a.get_editor_property("static_mesh_component"); c.set_static_mesh(meshes[name]); c.set_editor_property("mobility",unreal.ComponentMobility.MOVABLE)
    a.set_editor_property("tags",[unreal.Name("LB.SupportRobot.LB-CR01"),unreal.Name("LB.Asset.Candidate.v038"),unreal.Name("LB.Condition.Restored") if "Restored" in name else unreal.Name("LB.Condition.Mothballed") if "Mothballed" in name else unreal.Name("LB.Runtime.Module")])
    if "Restored" in name: c.set_editor_property("visible",False); c.set_editor_property("hidden_in_game",True)
    actors[name]=a

def attach(child,parent):
    child.attach_to_actor(parent,unreal.Name(),unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
attach(actors["SM_FrontBrushSpin"],actors["SM_FrontBrushLift"])
attach(actors["SM_ScrubDisc_L"],actors["SM_ScrubDeckLift"]); attach(actors["SM_ScrubDisc_R"],actors["SM_ScrubDeckLift"])
attach(actors["SM_SideBrushSpin_L"],actors["SM_SideBrushArm_L"]); attach(actors["SM_SideBrushSpin_R"],actors["SM_SideBrushArm_R"])
attach(actors["SM_SqueegeeYaw"],actors["SM_SqueegeeLift"]); attach(actors["SM_LB_CR01_Condition_Mothballed_Squeegee"],actors["SM_SqueegeeYaw"]); attach(actors["SM_LB_CR01_Condition_Restored_Squeegee"],actors["SM_SqueegeeYaw"])

cube=unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
floor=actors_api.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-3),unreal.Rotator()); floor.set_actor_label("LB_CR01_V038_ValidationFloor"); floor.get_editor_property("static_mesh_component").set_static_mesh(cube); floor.set_actor_scale3d(unreal.Vector(5,5,.05))
sun=actors_api.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,400),unreal.Rotator(-42,-35,0)); sun.set_actor_label("LB_CR01_V038_KeyLight"); sun.get_editor_property("directional_light_component").set_editor_property("intensity",2.0)
sky=actors_api.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,300),unreal.Rotator()); sky.set_actor_label("LB_CR01_V038_SkyLight"); sky.get_editor_property("light_component").set_editor_property("intensity",.55)
for label,loc,intensity in (("FillLeft",(0,-270,150),500),("FillRight",(0,270,150),500),("FillFront",(270,-180,210),420)):
    light=actors_api.spawn_actor_from_class(unreal.PointLight,unreal.Vector(*loc),unreal.Rotator()); light.set_actor_label("LB_CR01_V038_"+label); light.get_editor_property("point_light_component").set_editor_properties({"intensity":intensity,"attenuation_radius":650})
for label,loc,fov in (("Oblique",(330,-350,225),48.0),("Left",(0,-430,120),43.0),("Right",(0,430,120),43.0),("Top",(0,0,575),47.0)):
    cam=actors_api.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator()); cam.set_actor_label("LB_CR01_V038_CAM_"+label); cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*loc),unreal.Vector(0,0,48)),False); cam.get_editor_property("camera_component").set_editor_property("field_of_view",fov)

# Six-second looping cleaning proof: lift modules lower, side arms deploy and all brushes spin.
seq=tools.create_asset(SEQ_NAME,SEQ_DIR,unreal.LevelSequence,unreal.LevelSequenceFactoryNew()); seq.set_display_rate(unreal.FrameRate(30,1)); seq.set_playback_start(0); seq.set_playback_end(180)
def animate(actor,translation_keys=None,rotation_keys=None):
    binding=seq.add_possessable(actor); track=binding.add_track(unreal.MovieScene3DTransformTrack); section=track.add_section(); section.set_range(0,180); channels=section.get_all_channels(); base=actor.get_actor_location(); rot=actor.get_actor_rotation(); scale=actor.get_actor_scale3d(); values=[base.x,base.y,base.z,rot.roll,rot.pitch,rot.yaw,scale.x,scale.y,scale.z]
    for i,ch in enumerate(channels[:9]):
        keys=(translation_keys.get(i,((0,values[i]),(180,values[i]))) if translation_keys and i<3 else rotation_keys.get(i-3,((0,values[i]),(180,values[i]))) if rotation_keys and 3<=i<6 else ((0,values[i]),(180,values[i])))
        for frame,value in keys: ch.add_key(unreal.FrameNumber(frame),float(value),interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
for name,drop in (("SM_FrontBrushLift",8),("SM_ScrubDeckLift",12),("SM_SqueegeeLift",10)):
    a=actors[name]; z=a.get_actor_location().z; animate(a,{2:((0,z),(45,z),(75,z-drop),(150,z-drop),(180,z))})
animate(actors["SM_SideBrushArm_L"],rotation_keys={2:((0,0),(45,0),(75,-65),(150,-65),(180,0))}); animate(actors["SM_SideBrushArm_R"],rotation_keys={2:((0,0),(45,0),(75,65),(150,65),(180,0))})
for name,turns in (("SM_FrontBrushSpin",-6),("SM_ScrubDisc_L",8),("SM_ScrubDisc_R",-8),("SM_SideBrushSpin_L",6),("SM_SideBrushSpin_R",-6)):
    animate(actors[name],rotation_keys={2:((0,0),(45,0),(150,360*turns),(180,360*turns))})
asset_lib.save_loaded_asset(seq,only_if_is_dirty=False)
seq_actor=actors_api.spawn_actor_from_class(unreal.LevelSequenceActor,unreal.Vector(),unreal.Rotator()); seq_actor.set_actor_label("LB_CR01_V038_CleaningCycle"); seq_actor.set_sequence(seq); seq_actor.set_editor_property("playback_settings",unreal.MovieSceneSequencePlaybackSettings(auto_play=True,loop_count=unreal.MovieSceneSequenceLoopCount(-1),play_rate=1.0))
if not levels.save_current_level(): raise RuntimeError("Could not save v038 map")
result={"status":"IMPORT_AND_RUNTIME_SEQUENCE_PASS__VISUAL_GATE_PENDING","source":str(SOURCE),"destination":DEST,"map":MAP,"sequence":SEQ_PATH,"mesh_count":len(mesh_paths),"module_actor_count":len(actors),"condition_default":"MOTHBALLED","restored_components_hidden":2,"runtime_seconds":6.0,"pivot_correct_modules":11,"fixed_cameras":["LB_CR01_V038_CAM_"+x for x in ("Oblique","Left","Right","Top")],"remaining_gates":["fresh fixed-camera Unreal screenshots","visual comparison against Pro","collision/navigation","gameplay state integration"]}
AUDIT.parent.mkdir(parents=True,exist_ok=True); AUDIT.write_text(json.dumps(result,indent=2),encoding='utf-8'); unreal.log("LINE_BOSS_LB_CR01_V038_IMPORT_RUNTIME_PASS")
