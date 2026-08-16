"""Import and assemble unpromoted PR-007 washer/lube candidate v055."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

PROJECT=Path(unreal.Paths.project_dir()); SOURCE=PROJECT/"SourceAssets/PR007/WasherLubeUnit/Candidate_v001"
RECORDS=json.loads((SOURCE/"pr007_washer_lube_module_manifest_v001.json").read_text(encoding="utf-8"))
BASE="/Game/LineBoss/Maps/LB_PressShop_PR006LevellerCandidate_v054"; MAP="/Game/LineBoss/Maps/LB_PressShop_PR007WasherLubeCandidate_v055"
DEST="/Game/LineBoss/Stations/Press/PR007/Candidate_v001"; MAT=DEST+"/Materials"; PREFIX="LB_PR007_V055_"
DATUM=unreal.Vector(-2700,-2000,0); AUDIT=PROJECT/"Saved/Audits/press_shop_pr007_washer_lube_candidate_v055.json"
lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools(); mel=unreal.MaterialEditingLibrary
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def make_mat(name,c,m,r):
    path=f"{MAT}/{name}"; a=lib.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(name,MAT,unreal.Material,unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(a); base=mel.create_material_expression(a,unreal.MaterialExpressionConstant3Vector,-340,-70);base.set_editor_property("constant",unreal.LinearColor(*c,1))
    metal=mel.create_material_expression(a,unreal.MaterialExpressionConstant,-340,45);metal.set_editor_property("r",m);rough=mel.create_material_expression(a,unreal.MaterialExpressionConstant,-340,150);rough.set_editor_property("r",r)
    mel.connect_material_property(base,"",unreal.MaterialProperty.MP_BASE_COLOR);mel.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC);mel.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS);mel.recompile_material(a);lib.save_loaded_asset(a,only_if_is_dirty=False);return a
M={"frame":make_mat("M_PR007_CharcoalFrame_v001",(.045,.052,.058),.70,.42),"stainless":make_mat("M_PR007_Stainless_v001",(.29,.315,.32),.90,.38),"panel":make_mat("M_PR007_ServicePanel_v001",(.18,.195,.195),.62,.48),"yellow":make_mat("M_PR007_SafetyYellow_v001",(.72,.36,.014),.32,.49),"blue":make_mat("M_PR007_WashBlue_v001",(.018,.11,.23),.54,.42),"green":make_mat("M_PR007_LubeGreen_v001",(.02,.18,.11),.40,.45),"glass":make_mat("M_PR007_Window_v001",(.018,.042,.05),.58,.24),"steel":make_mat("M_PR007_RollSteel_v001",(.29,.315,.325),.92,.29),"white":make_mat("M_PR007_Label_v001",(.68,.70,.67),.12,.60),"red":make_mat("M_PR007_EStop_v001",(.48,.007,.003),.14,.42)}
def pick(n):
    q=n.lower()
    if "estopbutton" in q:return M["red"]
    if "window" in q:return M["glass"]
    if any(x in q for x in ("washpump","washheader","drain")):return M["blue"]
    if any(x in q for x in ("lubepump","lubeheader","beacon")):return M["green"]
    if any(x in q for x in ("roll","strip","nozzle","handle","filter")):return M["steel"]
    if any(x in q for x in ("hood","tank","duct","tray")):return M["stainless"]
    if any(x in q for x in ("identityplate",)):return M["white"]
    if any(x in q for x in ("estopstation",)):return M["yellow"]
    if any(x in q for x in ("chamber",)):return M["panel"]
    return M["frame"]

tasks=[]
for r in RECORDS:
    t=unreal.AssetImportTask();t.set_editor_properties({"filename":str(SOURCE/r["fbx"]),"destination_path":DEST,"destination_name":"SM_"+r["name"],"automated":True,"replace_existing":True,"replace_existing_settings":True,"save":True})
    o=unreal.FbxImportUI();o.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":False,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH});d=o.get_editor_property("static_mesh_import_data");d.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"force_front_x_axis":False,"generate_lightmap_u_vs":True,"auto_generate_collision":True,"remove_degenerates":True});t.set_editor_property("options",o);tasks.append(t)
tools.import_asset_tasks(tasks)
if not lib.does_asset_exist(MAP) and not lib.duplicate_asset(BASE,MAP):raise RuntimeError("Could not duplicate v054")
if not levels.load_level(MAP):raise RuntimeError(f"Could not load {MAP}")
for a in list(actors.get_all_level_actors()):
    if a.get_actor_label().startswith(PREFIX):actors.destroy_actor(a)
created=[]
for r in RECORDS:
    mesh=lib.load_asset(f"{DEST}/SM_{r['name']}");loc=r["location_m"];world=DATUM+unreal.Vector(loc[0]*100,loc[1]*100,loc[2]*100)
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,world,unreal.Rotator());a.set_actor_label(PREFIX+r["name"]);a.tags=[unreal.Name("LB.Asset.Candidate.v055"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Station.PR007"),unreal.Name("LB.Machine.Modular")]
    c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_mobility(unreal.ComponentMobility.MOVABLE if any(x in r["name"] for x in ("Hood","Roll","PumpMotor")) else unreal.ComponentMobility.STATIC);c.set_material(0,pick(r["name"]));c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);c.set_collision_profile_name(unreal.Name("BlockAll"));c.set_editor_property("can_ever_affect_navigation",False);created.append(a)

def text(label,value,z,size,color):
    a=actors.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(-2610,-2175,z),unreal.Rotator(yaw=-90));a.set_actor_label(PREFIX+label);a.tags=[unreal.Name("LB.Asset.Candidate.v055"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Station.PR007.Identity")];c=a.get_editor_property("text_render");c.set_text(value);c.set_world_size(size);c.set_text_render_color(color);c.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER);c.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property("can_ever_affect_navigation",False);return a
identity=[text("Identity_Cairnwell","CAIRNWELL AUTOMOTIVE",242,4.2,unreal.Color(35,82,72,255)),text("Identity_Station","PR-007  STRIP WASH / LUBE",234,5.6,unreal.Color(25,30,32,255)),text("Identity_Circuit","WASH A/B   LUBE A/B",226,3.5,unreal.Color(38,43,45,255))]
def spot(label,loc,target,intensity,color):
    a=actors.spawn_actor_from_class(unreal.SpotLight,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(PREFIX+label);a.tags=[unreal.Name("LB.Lighting.Candidate"),unreal.Name("LB.Lighting.PR007.Task"),unreal.Name("LB.Asset.CandidateNotPromoted")];a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(a.get_actor_location(),unreal.Vector(*target)),False);a.spot_light_component.set_editor_properties({"intensity":intensity,"attenuation_radius":1750.0,"inner_cone_angle":30.0,"outer_cone_angle":58.0,"source_radius":65.0,"soft_source_radius":120.0,"cast_shadows":False,"light_color":unreal.Color(*color,255)});return a
lights=[spot("OperatorTask",(-3300,-3000,950),(-2700,-2000,145),1000,(224,233,244)),spot("ServiceTask",(-2100,-1050,900),(-2700,-2000,135),800,(244,225,202))]
def camera(label,loc,target,fov):
    a=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(PREFIX+"CAM_"+label);a.tags=[unreal.Name("LB.Camera.Validation"),unreal.Name("LB.Camera.Fixed.PR007.v055"),unreal.Name("LB.Asset.CandidateNotPromoted")];a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(a.get_actor_location(),unreal.Vector(*target)),False);a.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16/9,"constrain_aspect_ratio":True});return a
cameras=[camera("Operator",(-2050,-3000,380),(-2700,-2000,145),49),camera("Service",(-2100,-1050,420),(-2700,-2000,140),51),camera("ConnectedLine",(-3700,-3900,820),(-2850,-2000,130),62)]
if not levels.save_current_level():raise RuntimeError(f"Could not save {MAP}")
lib.save_directory(DEST,only_if_is_dirty=False,recursive=True)
payload={"$schema":"line-boss/audit/press-shop-pr007-washer-lube-candidate-v055/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"MODULAR_PR007_WASHER_LUBE_IMPORTED_AND_ASSEMBLED__FULL_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED","map":MAP,"base_map":BASE,"station_datum_cm":[-2700,-2000,0],"module_count":len(created),"moving_module_count":sum(1 for a in created if a.static_mesh_component.get_editor_property("mobility")==unreal.ComponentMobility.MOVABLE),"native_identity":[a.get_actor_label() for a in identity],"task_lights":[a.get_actor_label() for a in lights],"fixed_cameras":[a.get_actor_label() for a in cameras],"hmi_included":False,"guarding_included":False,"runtime_controller_included":False,"promotion_authorized":False}
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2),encoding="utf-8");unreal.log(f"LINE_BOSS_PR007_V055_IMPORT_BUILD_PASS modules={len(created)}");unreal.SystemLibrary.quit_editor()
