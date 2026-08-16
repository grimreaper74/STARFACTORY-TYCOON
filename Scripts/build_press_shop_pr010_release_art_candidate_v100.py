"""Create isolated PR-010 v100 and install the dimensioned presentation kit."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v100"
SOURCE = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v100"
MANIFEST = json.loads((SOURCE / "PR010_RELEASE_ART_MANIFEST_v100.json").read_text(encoding="utf-8"))
SOURCE_AUDIT = json.loads((ROOT / "Saved/Audits/PR010_ReleaseArt_v100/pr010_release_art_source_audit_v100.json").read_text(encoding="utf-8"))
DEST = "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v100"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v100/pr010_release_art_build_v100.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

if not str(SOURCE_AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("PR-010 v100 source audit has not passed")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(TARGET_MAP):
    raise RuntimeError(f"Refusing to overwrite existing isolated candidate: {TARGET_MAP}")
if not library.duplicate_asset(SOURCE_MAP, TARGET_MAP):
    raise RuntimeError(f"Could not duplicate {SOURCE_MAP}")
if not library.save_asset(TARGET_MAP, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save duplicated map {TARGET_MAP}")


def import_static(row):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / row["file"]), "destination_path": DEST,
        "destination_name": row["asset"], "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False, "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])


for asset_row in MANIFEST["assets"]:
    import_static(asset_row)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

if not levels.load_level(TARGET_MAP):
    raise RuntimeError(TARGET_MAP)

material_root = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials"
material_paths = {
    "CA_MW_CairnwellGreen": f"{material_root}/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "CA_MW_FoundryCharcoal": f"{material_root}/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "CA_MW_SafetyYellow": f"{material_root}/M_CA_MW_PR009_LayeredSafetyYellow_v085",
    "CA_MW_ServiceGrey": f"{material_root}/M_CA_MW_PR009_LayeredServiceGrey_v085",
    "CA_MW_WorkedSteel": f"{material_root}/M_CA_MW_PR009_MachinedSteel_v085",
    "CA_MW_ScreenOnline": f"{material_root}/M_CA_MW_PR009_HMIScreenOnline_v085",
    "CA_MW_SensorGlass": f"{material_root}/M_CA_MW_PR009_SensorGlass_v085",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
if any(value is None for value in materials.values()):
    raise RuntimeError("Missing shared layered Press Shop materials")

manifest_rows = {row["asset"]: row for row in MANIFEST["assets"]}


def mesh(name):
    value = library.load_asset(f"{DEST}/{name}")
    if not isinstance(value, unreal.StaticMesh):
        raise RuntimeError(f"Missing imported static mesh: {name}")
    return value


def apply_materials(component, asset_name):
    for index, slot_name in enumerate(manifest_rows[asset_name]["material_slots"]):
        component.set_material(index, materials[slot_name])


def add_tags(actor, *values):
    current = [str(tag) for tag in actor.tags]
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(current + list(values))]


def hide_visual(actor):
    component = actor.get_component_by_class(unreal.PrimitiveComponent)
    if component:
        component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)


all_actors = list(actors_api.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in all_actors}
failures = []

# Replace the moving cube in place so the native v099 presentation binding stays valid.
carriage = by_label.get("LB_PR010_V099_PR010_M01_InfeedCarriage")
if carriage is None:
    failures.append("missing retained moving carriage")
else:
    origin, extent = carriage.get_actor_bounds(False, False)
    floor_z = origin.z - extent.z
    carriage.static_mesh_component.set_static_mesh(mesh("SM_CA_MW_PR010_InfeedTransferCradle_v100"))
    carriage.set_actor_scale3d(unreal.Vector(1, 1, 1))
    location = carriage.get_actor_location()
    carriage.set_actor_location(unreal.Vector(location.x, location.y, floor_z), False, False)
    apply_materials(carriage.static_mesh_component, "SM_CA_MW_PR010_InfeedTransferCradle_v100")
    add_tags(carriage, "LB.Asset.Candidate.v100", "LB.PR010.ReleaseArt.TransferCradle")

# Keep v099 blockers as invisible collision proxies; install proper open-grid panels.
guard_panels = []
for actor in all_actors:
    label = actor.get_actor_label()
    if "GuardPost_Lane" in label or "GuardRail_Lane" in label:
        hide_visual(actor)
        add_tags(actor, "LB.PR010.CollisionProxy", "LB.Asset.Candidate.v100")
    if "GuardRail_Lane" not in label:
        continue
    location = actor.get_actor_location()
    panel = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(location.x, location.y, 0.0), actor.get_actor_rotation())
    panel.set_actor_label(label.replace("LB_PR010_V098_GuardRail_", "LB_PR010_V100_GuardPanel_"))
    panel.tags = [unreal.Name(value) for value in (
        "LB.Station.PR010", "LB.Asset.Candidate.v100", "LB.Asset.CandidateNotPromoted",
        "LB.Safety.OpenMesh.GuardPanel", "LB.PR010.ReleaseArt.VisualOnly")]
    panel.static_mesh_component.set_static_mesh(mesh("SM_CA_MW_PR010_GuardPanel_OpenMesh_v100"))
    panel.static_mesh_component.set_world_scale3d(unreal.Vector(1, 1, 1))
    panel.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    panel.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    panel.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    apply_materials(panel.static_mesh_component, "SM_CA_MW_PR010_GuardPanel_OpenMesh_v100")
    guard_panels.append(panel)

# Upgrade lane-end scanners and tow points in place, retaining authored coordinates.
upgraded = []
for actor in all_actors:
    label = actor.get_actor_label()
    if "Scanner_Lane" in label:
        asset_name = "SM_CA_MW_PR010_SafetyScanner_v100"
    elif "TowPoint_Lane" in label:
        asset_name = "SM_CA_MW_PR010_TowPoint_v100"
    else:
        continue
    actor.static_mesh_component.set_static_mesh(mesh(asset_name))
    actor.set_actor_scale3d(unreal.Vector(1, 1, 1))
    location = actor.get_actor_location()
    actor.set_actor_location(unreal.Vector(location.x, location.y, 0.0), False, False)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    apply_materials(actor.static_mesh_component, asset_name)
    add_tags(actor, "LB.Asset.Candidate.v100", "LB.PR010.ReleaseArt")
    upgraded.append(label)

# Remove the coarse duplicate HMI presentation while retaining unrelated v099 state.
for actor in all_actors:
    label = actor.get_actor_label()
    if any(token in label for token in (
            "PR010_CoordinationHMI_", "RemoteHMI_", "IdentityBackplate",
            "TEXT_Corporation", "TEXT_Site", "TEXT_Station", "TEXT_Remote")):
        hide_visual(actor)
        add_tags(actor, "LB.PR010.LegacyPresentation.Hidden.v100")

hmi = actors_api.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(1025.0, -2645.0, 0.0), unreal.Rotator(yaw=-90.0))
hmi.set_actor_label("LB_PR010_V100_RemoteCoordinationHMI")
hmi.tags = [unreal.Name(value) for value in (
    "LB.Station.PR010", "LB.Asset.Candidate.v100", "LB.Asset.CandidateNotPromoted",
    "LB.HMI.Remote", "LB.Control.ControlRoomOnly", "LB.RemoteAuthority.CW.MW.CONTROL_ROOM")]
hmi.static_mesh_component.set_static_mesh(mesh("SM_CA_MW_PR010_RemoteHMIHousing_v100"))
hmi.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
hmi.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))
hmi.static_mesh_component.set_editor_property("can_ever_affect_navigation", True)
apply_materials(hmi.static_mesh_component, "SM_CA_MW_PR010_RemoteHMIHousing_v100")


def text_actor(label, value, location, size, colour):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=-90.0))
    actor.set_actor_label("LB_PR010_V100_TEXT_" + label)
    actor.tags = [unreal.Name(tag) for tag in (
        "LB.Station.PR010", "LB.Asset.Candidate.v100", "LB.Asset.CandidateNotPromoted", "LB.Identity.Diegetic")]
    actor.text_render.set_text(value)
    actor.text_render.set_world_size(size)
    actor.text_render.set_text_render_color(colour)
    actor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    actor.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.text_render.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity = [
    text_actor("Corporation", "CAIRNWELL AUTOMOTIVE", (997, -2645, 148), 5.6, unreal.Color(45, 190, 135, 255)),
    text_actor("Site", "MOORCROSS WORKS", (996, -2645, 137), 4.3, unreal.Color(230, 235, 230, 255)),
    text_actor("Station", "PR-010  FOUR-LANE BUFFER", (995, -2645, 123), 3.5, unreal.Color(245, 185, 35, 255)),
]

# Retarget the retained fixed HMI evidence camera to the authoritative HMI point.
camera = by_label.get("LB_PR010_V098_CAM_ServiceHMI")
if camera:
    camera.set_actor_location(unreal.Vector(600, -3100, 270), False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        camera.get_actor_location(), unreal.Vector(1025, -2645, 105)), False)
    camera.camera_component.set_editor_properties({"field_of_view": 43.0, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})
    add_tags(camera, "LB.Camera.Fixed.PR010.v100", "LB.Asset.Candidate.v100")
else:
    failures.append("missing retained ServiceHMI camera")

if len(guard_panels) != 8:
    failures.append(f"expected 8 release-art guard panels, found {len(guard_panels)}")
if len(upgraded) != 8:
    failures.append(f"expected 8 upgraded scanner/tow actors, found {len(upgraded)}")
if len(identity) != 3:
    failures.append("identity actor count mismatch")
if len([actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR010Station)]) != 1:
    failures.append("retained native PR010 authority count is not one")

if not levels.save_current_level():
    failures.append("could not save v100 candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "cairnwell/audit/pr010-release-art-build-v100/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V100_ISOLATED_RELEASE_ART_INSTALLED__TECHNICAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V100_RELEASE_ART_BUILD__NOT_PROMOTED",
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "asset_destination": DEST,
    "imported_assets": [row["asset"] for row in MANIFEST["assets"]],
    "moving_carriage_replaced_in_place": carriage is not None,
    "guard_visual_count": len(guard_panels), "upgraded_lane_end_actor_count": len(upgraded),
    "hmi_world_location_cm": [1025.0, -2645.0, 0.0],
    "hmi_authority_local_mm": [6450, -3250, 0],
    "identity_text": ["CAIRNWELL AUTOMOTIVE", "MOORCROSS WORKS", "PR-010  FOUR-LANE BUFFER"],
    "retained_v099_collision_navigation_runtime_contracts": True,
    "failures": failures, "promotion_authorized": False,
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
