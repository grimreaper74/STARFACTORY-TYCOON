"""Import and stage Coil AGV v001 in an isolated direct child of retained v124.

This is a visual/clearance candidate only. One existing physical coil moves from
CS-06 to the AGV, so the scene still contains exactly twelve PR003 coils: eleven
stored and one in transfer. Crane gameplay authority is deliberately untouched.
"""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVCandidate_v133"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001"
CHASSIS_ASSET = DEST + "/SM_LB_CoilAGV_Chassis_Candidate_v001"
DECK_ASSET = DEST + "/SM_LB_CoilAGV_LiftDeck_Candidate_v001"
PREFIX = "LB_PR003_PR004_V133_"
PROJECT = Path(unreal.Paths.project_dir())
SOURCE = PROJECT / "SourceAssets/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr003_pr004_coil_agv_build_v133.json"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


base_package = PROJECT / "Content/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124.umap"
base_hash_before = sha256(base_package)

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
imports = []
for name in ("SM_LB_CoilAGV_Chassis_Candidate_v001", "SM_LB_CoilAGV_LiftDeck_Candidate_v001"):
    fbx = SOURCE / f"{name}.fbx"
    if not fbx.is_file():
        raise RuntimeError(f"Missing canonical AGV source: {fbx}")
    asset_path = DEST + "/" + name
    if library.does_asset_exist(asset_path):
        library.delete_asset(asset_path)
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename":str(fbx), "destination_path":DEST, "destination_name":name,
                                "automated":True, "replace_existing":True, "replace_existing_settings":True, "save":True})
    options = unreal.FbxImportUI()
    options.set_editor_properties({"import_mesh":True, "import_materials":True, "import_textures":False,
                                   "mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,
                                   "automated_import_should_detect_type":False})
    options.static_mesh_import_data.set_editor_properties({"combine_meshes":True, "generate_lightmap_u_vs":True,
                                                            "auto_generate_collision":True, "import_uniform_scale":100.0})
    task.options = options
    imports.append(task)
tools.import_asset_tasks(imports)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

chassis_mesh = library.load_asset(CHASSIS_ASSET)
deck_mesh = library.load_asset(DECK_ASSET)
if chassis_mesh is None or deck_mesh is None:
    raise RuntimeError("AGV module import failed")
chassis_bounds = chassis_mesh.get_bounds().box_extent * 2.0
deck_bounds = deck_mesh.get_bounds().box_extent * 2.0
if not (359.0 <= chassis_bounds.x <= 363.0 and 220.0 <= chassis_bounds.y <= 224.0 and 81.0 <= chassis_bounds.z <= 83.0):
    raise RuntimeError(f"AGV chassis bounds failed: {chassis_bounds}")
if not (244.0 <= deck_bounds.x <= 246.0 and 203.0 <= deck_bounds.y <= 206.0 and 76.0 <= deck_bounds.z <= 78.0):
    raise RuntimeError(f"AGV deck bounds failed: {deck_bounds}")

# A previously interrupted commandlet can leave this owned candidate as the
# editor startup world. Load the immutable parent before deleting/rebuilding it.
if not levels.load_level(BASE):
    raise RuntimeError(f"Could not load retained parent {BASE} before candidate rebuild")
unreal.SystemLibrary.collect_garbage()
if library.does_asset_exist(MAP):
    if not library.delete_asset(MAP):
        raise RuntimeError(f"Could not remove previous owned candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"Could not create isolated v133 from {BASE}")


def tags(*values):
    return [unreal.Name(value) for value in values]


def spawn_mesh(label, mesh, location, rotation=unreal.Rotator(), collision=True, nav=False):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), rotation)
    actor.set_actor_label(PREFIX + label)
    actor.tags = tags("LB.Asset.Candidate.v133", "LB.Asset.CandidateNotPromoted", "LB.OwnerDirectedRevision.CoilAGV")
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.MOVABLE if label.startswith("AGV") else unreal.ComponentMobility.STATIC)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("BlockAll" if collision else "NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", nav)
    return actor


AGV = (-5545.0, -2000.0)
chassis = spawn_mesh("AGV01_Chassis", chassis_mesh, (AGV[0],AGV[1],29.0))
chassis.tags = tags("LB.Asset.Candidate.v133", "LB.Asset.CandidateNotPromoted", "LB.OwnerDirectedRevision.CoilAGV",
                    "LB.Vehicle.CoilAGV", "LB.Vehicle.AGVID.AGV-01", "LB.Route.PR003.PR004",
                    "LB.Payload.DesignTarget.40000kg.TBC", "LB.Runtime.Authority.NotYetBound")
deck = spawn_mesh("AGV01_LiftDeck", deck_mesh, (AGV[0],AGV[1],64.0))
deck.tags = tags("LB.Asset.Candidate.v133", "LB.Asset.CandidateNotPromoted", "LB.Vehicle.CoilAGV.LiftDeck",
                 "LB.Motion.AGVDockLift", "LB.Motion.Range.80mm.TBC", "LB.Runtime.Authority.NotYetBound")

# Move the existing CS-06 coil rather than duplicate it. Runtime crane source
# CS-10 and every crane/controller tag remain unchanged.
all_actors = list(actors_api.get_all_level_actors())
coil = next((a for a in all_actors if a.get_actor_label() == "LB_INT_FRONT_CS-06_PackagedMasterCoil_v024"), None)
if coil is None:
    raise RuntimeError("Missing inherited CS-06 packaged coil")
coil_before = coil.get_actor_location()
coil.set_actor_location(unreal.Vector(AGV[0], AGV[1], 156.0), False, False)
coil.set_actor_rotation(unreal.Rotator(yaw=0.0), False)
coil.tags = tags(*[str(t) for t in coil.tags], "LB.Asset.Candidate.v133", "LB.Inventory.InTransfer",
                 "LB.Inventory.Source.CS-06", "LB.Vehicle.AGVID.AGV-01")
coil.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
coil.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
coil.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))
coil.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)

hidden_source_labels = []
for actor in all_actors:
    label = actor.get_actor_label()
    if "CS-06" not in label or label == "LB_INT_FRONT_CS-06_CoilSaddle" or "BayMark" in label:
        continue
    if actor is coil:
        continue
    if "COIL_LABEL" in label or "COIL_TRACE" in label or "COIL_BARCODE" in label:
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
        actor.tags = tags(*[str(t) for t in actor.tags], "LB.Asset.Candidate.v133", "LB.Inventory.SourceLabel.SupersededDuringTransfer")
        hidden_source_labels.append(label)

cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
route_material = library.load_asset("/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v106/Materials/M_CA_MW_LogisticsRoute_v105")
yellow_material = library.load_asset("/Game/LineBoss/Materials/M_LB_SafetyYellow")
if cube is None or route_material is None or yellow_material is None:
    raise RuntimeError("Missing controlled route primitives/materials")


def floor_bar(label, location, dimensions, material, collision=False):
    actor = spawn_mesh(label, cube, location, collision=collision, nav=collision)
    actor.set_actor_scale3d(unreal.Vector(dimensions[0]/100.0,dimensions[1]/100.0,dimensions[2]/100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.tags = tags(*[str(t) for t in actor.tags], "LB.Route.CoilAGV.TBC")
    return actor


# 3.2 m candidate route is marked, not asserted as approved engineering data.
route = [floor_bar("RouteBoundaryNorth", (-6260,-1840,8.7), (1880,8,1.0), yellow_material),
         floor_bar("RouteBoundarySouth", (-6260,-2160,8.7), (1880,8,1.0), yellow_material)]
for index, x in enumerate((-7040,-6760,-6480,-6200,-5920,-5640), start=1):
    route.append(floor_bar(f"RouteCentreDash_{index:02d}", (x,-2000,8.75), (145,10,1.1), route_material))

# Dock witness lines and positive wheel-stop blocks outside the PR004 west boundary.
dock = [floor_bar("DockWitnessWest", (-5730,-2000,8.8), (8,300,1.2), yellow_material),
        floor_bar("DockWitnessEast", (-5340,-2000,8.8), (8,300,1.2), yellow_material),
        floor_bar("DockWitnessNorth", (-5535,-1850,8.8), (390,8,1.2), yellow_material),
        floor_bar("DockWitnessSouth", (-5535,-2150,8.8), (390,8,1.2), yellow_material),
        floor_bar("DockStopNorth", (-5330,-2080,18.0), (28,28,20), yellow_material, True),
        floor_bar("DockStopSouth", (-5330,-1920,18.0), (28,28,20), yellow_material, True)]

text_actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(-5900,-2300,12.0), unreal.Rotator(pitch=-90,yaw=-90))
text_actor.set_actor_label(PREFIX + "CS06_InTransfer")
text_actor.tags = tags("LB.Asset.Candidate.v133","LB.Asset.CandidateNotPromoted","LB.Inventory.CS-06.InTransfer")
text_actor.text_render.set_text("CS-06  IN TRANSFER")
text_actor.text_render.set_world_size(22.0)
text_actor.text_render.set_text_render_color(unreal.Color(255,190,30,255))
text_actor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
text_actor.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
text_actor.text_render.set_editor_property("can_ever_affect_navigation", False)


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = tags("LB.Camera.Validation","LB.Camera.Fixed.CoilAGV.v133","LB.Asset.Candidate.v133","LB.Asset.CandidateNotPromoted")
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    comp = actor.camera_component
    comp.set_editor_properties({"field_of_view":fov,"aspect_ratio":16.0/9.0,"constrain_aspect_ratio":True,"post_process_blend_weight":1.0})
    pp = comp.get_editor_property("post_process_settings")
    pp.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,
                              "override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,
                              "auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,
                              "override_auto_exposure_bias":True,"auto_exposure_bias":0.15})
    comp.set_editor_property("post_process_settings", pp)
    return actor


cameras = [camera("LoadedApproach", (-6680,-930,560), (-5620,-2000,115), 47.0),
           camera("DockAndPR004", (-6180,-1050,520), (-5350,-1980,110), 42.0),
           camera("RouteOverview", (-6450,-2000,1750), (-6200,-2000,0), 58.0)]

visible_coils = [a for a in actors_api.get_all_level_actors()
                 if "LB.Material.PackagedCoil" in {str(t) for t in a.tags}
                 and any(str(t).startswith("LB.PR003.Layout.Slot.") for t in a.tags)
                 and not a.get_editor_property("hidden")]
stored = [a for a in visible_coils if "LB.Inventory.InTransfer" not in {str(t) for t in a.tags}]
failures = []
if len(visible_coils) != 12:
    failures.append(f"expected exactly 12 visible packaged coils, found {len(visible_coils)}")
if len(stored) != 11:
    failures.append(f"expected eleven stored packaged coils, found {len(stored)}")
if abs(coil.get_actor_location().x - AGV[0]) > 0.1 or abs(coil.get_actor_location().y - AGV[1]) > 0.1:
    failures.append("CS-06 coil is not centred on AGV")
if failures:
    raise RuntimeError("; ".join(failures))
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

base_hash_after = sha256(base_package)
if base_hash_after != base_hash_before:
    raise RuntimeError("Retained v124 package changed while building isolated v133")

payload = {
    "$schema":"cairnwell/audit/press-shop-pr003-pr004-coil-agv-build-v133/v1",
    "generated_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS__ISOLATED_OWNER_DIRECTED_COIL_AGV_VISUAL_CLEARANCE_CANDIDATE_BUILT__RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_map":BASE,"map":MAP,"authority":"Docs/PRESS_SHOP_FRONT_END_COIL_AGV_REVISION_AUTHORITY.md",
    "source_assets":{"chassis":CHASSIS_ASSET,"lift_deck":DECK_ASSET},
    "import_bounds_cm":{"chassis":[chassis_bounds.x,chassis_bounds.y,chassis_bounds.z],"lift_deck":[deck_bounds.x,deck_bounds.y,deck_bounds.z]},
    "agv_dock_location_cm":[AGV[0],AGV[1]],"route_width_cm":320.0,"route_width_status":"TBC",
    "inventory":{"visible_packaged_coils":len(visible_coils),"stored_coils":len(stored),"in_transfer":1,"source_slot":"CS-06","source_before_cm":[coil_before.x,coil_before.y,coil_before.z]},
    "hidden_source_label_count":len(hidden_source_labels),"crane_gameplay_authority_changed":False,
    "crane_visual_or_transform_changed":False,"v124_hash_before":base_hash_before,"v124_hash_after":base_hash_after,
    "fixed_cameras":[a.get_actor_label() for a in cameras],"promotion_authorized":False,"failures":failures,
}
OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
