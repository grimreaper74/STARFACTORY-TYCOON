"""Build unpromoted PR-007 strip continuity, local guarding and HMI candidate v056."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE=ROOT/"SourceAssets/PR007/StripBridges/Candidate_v001"
RECORDS=json.loads((SOURCE/"pr007_strip_bridge_module_manifest_v001.json").read_text(encoding="utf-8"))
BASE="/Game/LineBoss/Maps/LB_PressShop_PR007WasherLubeCandidate_v055"
MAP="/Game/LineBoss/Maps/LB_PressShop_PR007StripGuardHMICandidate_v056"
DEST="/Game/LineBoss/Stations/Press/PR007/StripBridges/Candidate_v001"
PREFIX="LB_PR007_V056_"
AUDIT=ROOT/"Saved/Audits/press_shop_pr007_strip_guard_hmi_candidate_v056.json"
lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools()
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

tasks=[]
for r in RECORDS:
    t=unreal.AssetImportTask();t.set_editor_properties({"filename":str(SOURCE/r["fbx"]),"destination_path":DEST,"destination_name":"SM_"+r["name"],"automated":True,"replace_existing":True,"replace_existing_settings":True,"save":True})
    o=unreal.FbxImportUI();o.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":False,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH})
    d=o.get_editor_property("static_mesh_import_data");d.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"generate_lightmap_u_vs":True,"auto_generate_collision":True,"remove_degenerates":True})
    t.set_editor_property("options",o);tasks.append(t)
tools.import_asset_tasks(tasks);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
map_file=ROOT/"Content/LineBoss/Maps/LB_PressShop_PR007StripGuardHMICandidate_v056.umap"
if not map_file.exists():
    if not lib.duplicate_asset(BASE,MAP):raise RuntimeError("Could not duplicate v055")
    if not lib.save_asset(MAP,only_if_is_dirty=False):raise RuntimeError("Could not save prepared v056 map")
    unreal.log("LINE_BOSS_PR007_V056_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit
if not levels.load_level(MAP):raise RuntimeError(f"Could not load {MAP}")
for a in list(actors.get_all_level_actors()):
    if a.get_actor_label().startswith(PREFIX):actors.destroy_actor(a)

steel=lib.load_asset("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_RollSteel_v001")
dark=lib.load_asset("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_CharcoalFrame_v001")
yellow=lib.load_asset("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_SafetyYellow_v001")
if not all((steel,dark,yellow)):raise RuntimeError("Missing controlled PR007 materials")

created=[]
for r in RECORDS:
    mesh=lib.load_asset(f"{DEST}/SM_{r['name']}")
    if not mesh:raise RuntimeError(f"Missing imported bridge mesh {r['name']}")
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*r["location_cm"]),unreal.Rotator());a.set_actor_label(PREFIX+r["name"])
    a.tags=[unreal.Name("LB.Asset.Candidate.v056"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Station.PR007"),unreal.Name("LB.Process.StripContinuity")]
    c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_mobility(unreal.ComponentMobility.MOVABLE if r["role"]=="bridge_roll" else unreal.ComponentMobility.STATIC)
    for i,slot in enumerate(mesh.get_editor_property("static_materials")):
        sn=str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name")).lower()
        c.set_material(i,yellow if "yellow" in sn else dark if "charcoal" in sn else steel)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION if r["role"]=="strip_bridge" else unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    c.set_collision_profile_name(unreal.Name("NoCollision" if r["role"]=="strip_bridge" else "BlockAll"));c.set_editor_property("can_ever_affect_navigation",False)
    created.append(a)

GUARD_ROOT="/Game/LineBoss/IndustrialKit/Safety/Barrier_v002"
panel=lib.load_asset(GUARD_ROOT+"/SM_LB_GuardPanel_2000x2400_v002")
post=lib.load_asset(GUARD_ROOT+"/SM_LB_GuardPost_2500_v002")
if not panel or not post:raise RuntimeError("Approved open-mesh guard kit is missing")
guards=[]
def guard(label,mesh,loc):
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(PREFIX+label);a.tags=[unreal.Name("LB.Asset.Candidate.v056"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Station.PR007"),unreal.Name("LB.Safety.OpenMeshGuard")]
    c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);c.set_collision_profile_name(unreal.Name("BlockAll"));c.set_editor_property("can_ever_affect_navigation",True);guards.append(a);return a
for side,y in (("Operator",-2215.0),("Service",-1785.0)):
    for x in (-3425.0,-3225.0):guard(f"Guard_{side}_Upstream_{int(x)}",panel,(x,y,0))
    for x in (-3525.0,-3325.0,-3125.0):guard(f"Post_{side}_Upstream_{int(x)}",post,(x,y,0))
    guard(f"Guard_{side}_Downstream",panel,(-2203.75,y,0))
    for x in (-2303.75,-2103.75):guard(f"Post_{side}_Downstream_{int(x)}",post,(x,y,0))

HMI_ROOT="/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling"
hmi_names=("SM_LB_HMI04_DisplaySurface",)
hmi=[]
for name in hmi_names:
    mesh=lib.load_asset(f"{HMI_ROOT}/{name}")
    if not mesh:raise RuntimeError(f"Missing shared HMI module {name}")
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(-2475,-2500,8),unreal.Rotator());a.set_actor_label(PREFIX+"HMI_"+name.replace("SM_LB_HMI04_",""));a.tags=[unreal.Name("LB.Asset.Candidate.v056"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Station.PR007"),unreal.Name("LB.Module.SharedHMI")]
    c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);c.set_collision_profile_name(unreal.Name("BlockAll"));c.set_editor_property("can_ever_affect_navigation",True);hmi.append(a)

cube_mesh=lib.load_asset("/Engine/BasicShapes/Cube")
def hmi_cube(label,loc,dims,material):
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(PREFIX+"HMI_"+label);a.tags=[unreal.Name("LB.Asset.Candidate.v056"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Station.PR007"),unreal.Name("LB.Module.CompactTouchHMI")]
    a.set_actor_scale3d(unreal.Vector(dims[0]/100,dims[1]/100,dims[2]/100));c=a.static_mesh_component;c.set_static_mesh(cube_mesh);c.set_material(0,material);c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);c.set_collision_profile_name(unreal.Name("BlockAll"));c.set_editor_property("can_ever_affect_navigation",True);hmi.append(a);return a
hmi_cube("TouchBase",(-2475,-2500,12),(60,46,24),dark)
hmi_cube("TouchPost",(-2475,-2500,63),(12,12,78),steel)
hmi_cube("TouchBezel",(-2475,-2507,121),(46,12,38),dark)

def text(label,value,z,size,color):
    a=actors.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(-2475,-2524,z),unreal.Rotator(yaw=-90));a.set_actor_label(PREFIX+"HMI_Text_"+label);a.tags=[unreal.Name("LB.Asset.Candidate.v056"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Station.PR007.HMI")]
    c=a.text_render;c.set_text(value);c.set_world_size(size);c.set_text_render_color(color);c.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER);c.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property("can_ever_affect_navigation",False);return a
hmi_text=[text("Brand","CAIRNWELL / MOORCROSS",130,2.6,unreal.Color(45,205,155,255)),text("Station","PR-007  WASH + LUBE",121,3.2,unreal.Color(225,235,232,255)),text("State","READY | WASH 2.4 bar | LUBE READY",112,2.15,unreal.Color(95,225,170,255))]

def camera(label,loc,target,fov):
    a=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(PREFIX+"CAM_"+label);a.tags=[unreal.Name("LB.Camera.Validation"),unreal.Name("LB.Camera.Fixed.PR007.v056"),unreal.Name("LB.Asset.CandidateNotPromoted")];a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(a.get_actor_location(),unreal.Vector(*target)),False);a.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16/9,"constrain_aspect_ratio":True});return a
cameras=[camera("ConnectedStrip",(-3900,-3450,650),(-2700,-2000,125),58),camera("OperatorGuardHMI",(-2600,-3150,300),(-2550,-2250,125),48),camera("ElevatedLine",(-3800,-3900,900),(-2600,-2000,120),62)]

if not levels.save_current_level():raise RuntimeError(f"Could not save {MAP}")
lib.save_directory(DEST,only_if_is_dirty=False,recursive=True)
payload={"$schema":"line-boss/audit/press-shop-pr007-strip-guard-hmi-candidate-v056/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"DIMENSIONED_STRIP_CONTINUITY_GUARD_AND_HMI_ASSEMBLY_PASS__RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED","map":MAP,"base_map":BASE,"bridge_module_count":len(created),"guard_actor_count":len(guards),"open_mesh_panel_count":6,"guard_post_count":10,"hmi_module_count":len(hmi),"hmi_text_row_count":len(hmi_text),"upstream_gap_cm":512.5,"downstream_gap_cm":257.5,"strip_width_cm":150,"fixed_cameras":[a.get_actor_label() for a in cameras],"promotion_authorized":False}
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2),encoding="utf-8");unreal.log(f"LINE_BOSS_PR007_V056_BUILD_PASS bridges={len(created)} guards={len(guards)} hmi={len(hmi)}");unreal.SystemLibrary.quit_editor()
