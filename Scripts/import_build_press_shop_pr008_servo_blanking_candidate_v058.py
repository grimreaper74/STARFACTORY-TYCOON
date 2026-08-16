"""Import and assemble unpromoted PR-008 servo-feed/cut/pre-punch candidate v058."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

PROJECT=Path(unreal.Paths.project_dir());SOURCE=PROJECT/"SourceAssets/PR008/ServoBlankingLine/Candidate_v001"
RECORDS=json.loads((SOURCE/"pr008_servo_blanking_module_manifest_v001.json").read_text(encoding="utf-8"))
BASE="/Game/LineBoss/Maps/LB_PressShop_PR007RuntimeCandidate_v057";MAP="/Game/LineBoss/Maps/LB_PressShop_PR008ServoBlankingCandidate_v058"
DEST="/Game/LineBoss/Stations/Press/PR008/Candidate_v001";MAT=DEST+"/Materials";PREFIX="LB_PR008_V058_"
DATUM=unreal.Vector(-500,-2000,0);AUDIT=PROJECT/"Saved/Audits/press_shop_pr008_servo_blanking_candidate_v058.json"
lib=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def asset_name(source_name):
    return source_name.replace("+","P").replace("-","M").replace(".","_")

def make_mat(name,c,m,r):
    path=f"{MAT}/{name}";a=lib.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(name,MAT,unreal.Material,unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(a);base=mel.create_material_expression(a,unreal.MaterialExpressionConstant3Vector,-340,-70);base.set_editor_property("constant",unreal.LinearColor(*c,1))
    metal=mel.create_material_expression(a,unreal.MaterialExpressionConstant,-340,45);metal.set_editor_property("r",m);rough=mel.create_material_expression(a,unreal.MaterialExpressionConstant,-340,150);rough.set_editor_property("r",r)
    mel.connect_material_property(base,"",unreal.MaterialProperty.MP_BASE_COLOR);mel.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC);mel.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS);mel.recompile_material(a);lib.save_loaded_asset(a,only_if_is_dirty=False);return a
M={"frame":make_mat("M_PR008_FoundryCharcoal_v001",(.045,.052,.058),.72,.43),"panel":make_mat("M_PR008_ServiceGrey_v001",(.18,.195,.205),.62,.48),"yellow":make_mat("M_PR008_SafetyYellow_v001",(.72,.36,.014),.30,.49),"steel":make_mat("M_PR008_WorkedSteel_v001",(.29,.315,.325),.92,.29),"strip":make_mat("M_PR008_StripSteel_v001",(.38,.405,.415),.94,.24),"blue":make_mat("M_PR008_ServoBlue_v001",(.018,.11,.23),.58,.42),"green":make_mat("M_PR008_CairnwellGreen_v001",(.02,.16,.13),.42,.45),"glass":make_mat("M_PR008_InspectionGlass_v001",(.018,.042,.05),.50,.24),"white":make_mat("M_PR008_Identity_v001",(.68,.70,.67),.12,.60),"red":make_mat("M_PR008_EStop_v001",(.48,.007,.003),.12,.42)}
def pick(n):
    q=n.lower()
    if "estop" in q and "button" in q:return M["red"]
    if any(x in q for x in ("window","camerahead")):return M["glass"]
    if any(x in q for x in ("feedservo","encoder","hydraulicmotor","prepunchcylinder")):return M["blue"]
    if "beacon" in q:return M["green"]
    if any(x in q for x in ("roll","strip","die","bolster","beam","filter","blank")):return M["steel"] if "strip" not in q and "blank" not in q else M["strip"]
    if "identityplate" in q:return M["white"]
    if any(x in q for x in ("slide","sensorbridge","camerabridge","estop")):return M["yellow"]
    if any(x in q for x in ("housing","crown","cabinet","tank")):return M["panel"]
    return M["frame"]

tasks=[]
for r in RECORDS:
    t=unreal.AssetImportTask();t.set_editor_properties({"filename":str(SOURCE/r["fbx"]),"destination_path":DEST,"destination_name":"SM_"+asset_name(r["name"]),"automated":True,"replace_existing":True,"replace_existing_settings":True,"save":True})
    o=unreal.FbxImportUI();o.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":False,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH});d=o.get_editor_property("static_mesh_import_data");d.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"generate_lightmap_u_vs":True,"auto_generate_collision":True,"remove_degenerates":True});t.set_editor_property("options",o);tasks.append(t)
tools.import_asset_tasks(tasks);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
map_file=PROJECT/"Content/LineBoss/Maps/LB_PressShop_PR008ServoBlankingCandidate_v058.umap"
if not map_file.exists():
    if not lib.duplicate_asset(BASE,MAP):raise RuntimeError("Could not duplicate v057")
    if not lib.save_asset(MAP,only_if_is_dirty=False):raise RuntimeError("Could not save prepared v058 map")
    unreal.log("LINE_BOSS_PR008_V058_PREPARE_PASS__RERUN_FOR_POPULATION");unreal.SystemLibrary.quit_editor();raise SystemExit
if not levels.load_level(MAP):raise RuntimeError(f"Could not load {MAP}")
for a in list(actors.get_all_level_actors()):
    if a.get_actor_label().startswith(PREFIX):actors.destroy_actor(a)
created=[]
moving_terms=("Roll","Servo","Encoder","TelescopeBeam","PressSlide","PrePunchCylinder","GuillotineBeam","HydraulicMotor","DischargeBlank")
for r in RECORDS:
    mesh=lib.load_asset(f"{DEST}/SM_{asset_name(r['name'])}")
    if not mesh:raise RuntimeError(f"Missing imported mesh {r['name']}")
    loc=r["location_m"];world=DATUM+unreal.Vector(loc[0]*100,loc[1]*100,loc[2]*100)
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,world,unreal.Rotator());a.set_actor_label(PREFIX+r["name"]);a.tags=[unreal.Name("LB.Asset.Candidate.v058"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Station.PR008"),unreal.Name("LB.Machine.Modular")]
    c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_mobility(unreal.ComponentMobility.MOVABLE if any(x in r["name"] for x in moving_terms) else unreal.ComponentMobility.STATIC);c.set_material(0,pick(r["name"]));c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION if any(x in r["name"] for x in ("ThreadedStrip","DischargeBlank")) else unreal.CollisionEnabled.QUERY_AND_PHYSICS);c.set_collision_profile_name(unreal.Name("NoCollision" if any(x in r["name"] for x in ("ThreadedStrip","DischargeBlank")) else "BlockAll"));c.set_editor_property("can_ever_affect_navigation",False);created.append(a)
def text(label,value,z,size,color):
    a=actors.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(-445,-2208,z),unreal.Rotator(yaw=-90));a.set_actor_label(PREFIX+label);a.tags=[unreal.Name("LB.Asset.Candidate.v058"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Station.PR008.Identity")];c=a.text_render;c.set_text(value);c.set_world_size(size);c.set_text_render_color(color);c.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER);c.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property("can_ever_affect_navigation",False);return a
identity=[text("Identity_Cairnwell","CAIRNWELL AUTOMOTIVE",334,4.4,unreal.Color(35,82,72,255)),text("Identity_Station","PR-008  SERVO BLANKING",322,5.4,unreal.Color(25,30,32,255)),text("Identity_Process","FEED / PRE-PUNCH / CUT",311,3.7,unreal.Color(38,43,45,255))]
def spot(label,loc,target,intensity,color):
    a=actors.spawn_actor_from_class(unreal.SpotLight,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(PREFIX+label);a.tags=[unreal.Name("LB.Lighting.Candidate"),unreal.Name("LB.Lighting.PR008.Task"),unreal.Name("LB.Asset.CandidateNotPromoted")];a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(a.get_actor_location(),unreal.Vector(*target)),False);a.spot_light_component.set_editor_properties({"intensity":intensity,"attenuation_radius":1900.0,"inner_cone_angle":30.0,"outer_cone_angle":58.0,"source_radius":65.0,"soft_source_radius":120.0,"cast_shadows":False,"light_color":unreal.Color(*color,255)});return a
lights=[spot("OperatorTask",(-1200,-3200,1050),(-500,-2000,170),1100,(224,233,244)),spot("DriveTask",(250,-850,950),(-450,-1900,160),850,(244,225,202))]
def camera(label,loc,target,fov):
    a=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(PREFIX+"CAM_"+label);a.tags=[unreal.Name("LB.Camera.Validation"),unreal.Name("LB.Camera.Fixed.PR008.v058"),unreal.Name("LB.Asset.CandidateNotPromoted")];a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(a.get_actor_location(),unreal.Vector(*target)),False);a.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16/9,"constrain_aspect_ratio":True});return a
cameras=[camera("Operator",(-1450,-3450,560),(-500,-2000,170),54),camera("Drive",(450,-700,570),(-500,-2000,165),55),camera("ConnectedLine",(-3300,-4300,1150),(-1100,-2000,140),62)]
if not levels.save_current_level():raise RuntimeError(f"Could not save {MAP}")
lib.save_directory(DEST,only_if_is_dirty=False,recursive=True)
payload={"$schema":"line-boss/audit/press-shop-pr008-servo-blanking-candidate-v058/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"MODULAR_PR008_SERVO_BLANKING_IMPORTED_AND_ASSEMBLED__FULL_RUNTIME_GUARD_HMI_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED","map":MAP,"base_map":BASE,"station_datum_cm":[-500,-2000,0],"source_envelope_m":[10.4,5.56,4.49],"module_count":len(created),"moving_module_count":sum(1 for a in created if a.static_mesh_component.get_editor_property("mobility")==unreal.ComponentMobility.MOVABLE),"processes":["loop_control","servo_feed","telescopic_support","pre_punch","cut","outfeed_handoff"],"native_identity":[a.get_actor_label() for a in identity],"task_lights":[a.get_actor_label() for a in lights],"fixed_cameras":[a.get_actor_label() for a in cameras],"hmi_included":False,"guarding_included":False,"runtime_controller_included":False,"promotion_authorized":False}
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2),encoding="utf-8");unreal.log(f"LINE_BOSS_PR008_V058_IMPORT_BUILD_PASS modules={len(created)}");unreal.SystemLibrary.quit_editor()
