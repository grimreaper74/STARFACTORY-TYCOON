"""Import PR-009 and the supported PR-008/PR-009 bridge into isolated map v083."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
PR009 = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002"
PR009_EXPORT = PR009 / "PR009_Exports/v002_candidate"
PR009_EXPORT_MANIFEST = json.loads((PR009 / "PR009_Audits/v002/PR009_FBX_EXPORT_MANIFEST_v002.json").read_text(encoding="utf-8"))
PR009_INTAKE = json.loads((ROOT / "Saved/Audits/press_shop_pr009_source_intake_v002.json").read_text(encoding="utf-8"))
TRANSFER = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Interface_v001"
TRANSFER_MANIFEST = json.loads((TRANSFER / "pr008_pr009_supported_transfer_manifest_v001.json").read_text(encoding="utf-8"))

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008ExternalAnchorTabsCandidate_v082"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009PhysicalIntegrationCandidate_v083"
PR009_DEST = "/Game/LineBoss/Candidates/PressShop/PR009/v002/Cell"
PR009_COLLISION_DEST = "/Game/LineBoss/Candidates/PressShop/PR009/v002/CollisionEvidence"
TRANSFER_DEST = "/Game/LineBoss/Candidates/PressShop/PR009/v002/Interface"
PREFIX = "LB_PR009_V083_"
OUT = ROOT / "Saved/Audits/press_shop_pr009_physical_integration_v083.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def import_static(path, destination, name, collision):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(path), "destination_path": destination, "destination_name": name,
        "automated": True, "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": collision, "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])
    return task


# Source groups remain semantically separate. SK-prefixed files are imported as static candidate groups
# for this physical gate; their future native moving decomposition remains an explicit release hold.
if PR009_INTAKE.get("status") != "CANONICAL_V002_SOURCE_INTAKE_HASH_AND_MANIFEST_PASS__UNREAL_GATES_REQUIRED__NOT_PROMOTED":
    raise RuntimeError("Canonical PR-009 v002 hash intake has not passed")
if len(PR009_EXPORT_MANIFEST.get("files", [])) != 19:
    raise RuntimeError("PR-009 v002 export manifest must contain exactly 19 FBX groups")

pr009_import_files = list(PR009_EXPORT_MANIFEST["files"])
pr009_files = [
    entry for entry in pr009_import_files
    if not entry["file"].startswith("UCX_") and "_LOD1" not in entry["file"] and "_LOD2" not in entry["file"]
]
for entry in pr009_import_files:
    stem = Path(entry["file"]).stem
    destination = PR009_COLLISION_DEST if stem.startswith("UCX_") else PR009_DEST
    import_static(PR009_EXPORT / entry["file"], destination, stem, not stem.startswith(("SK_", "UCX_")))

for record in TRANSFER_MANIFEST["records"]:
    import_static(TRANSFER / record["fbx"], TRANSFER_DEST, record["name"], record["collision"] == "BlockAll")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR009PhysicalIntegrationCandidate_v083.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP) or not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not prepare isolated v083 map")
    unreal.log("LINE_BOSS_PR009_V083_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)

inherited_pr009 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR009Station)]
if inherited_pr009:
    raise RuntimeError("Unexpected inherited PR-009 native authority in v082 base")

station = actors_api.spawn_actor_from_class(
    unreal.LBPR009Station, unreal.Vector(600.0, -2000.0, 0.0), unreal.Rotator(yaw=-90.0))
if station is None:
    raise RuntimeError("Could not spawn native PR-009 authority")
station.set_actor_label(PREFIX + "Station_PR-009_NativeAuthority")
station.tags = [unreal.Name(value) for value in (
    "LB.Station.PR009", "LB.Authority.PR009.Native", "LB.Authority.RemoteHMI.SharedGateway",
    "LB.Authority.ControlRoom.CW.MW.CONTROL_ROOM", "LB.Asset.Candidate.v083",
    "LB.Asset.CandidateNotPromoted", "LB.Process.AutomatedBlankStacking",
)]

shared_mat_root = "/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials"
material_assets = {
    key: library.load_asset(f"{shared_mat_root}/{name}") for key, name in {
        "charcoal": "M_CA_MW_PR008_FoundryCharcoal_v001",
        "green": "M_CA_MW_PR008_CairnwellGreen_v001",
        "yellow": "M_CA_MW_PR008_SafetyYellow_v001",
        "steel": "M_CA_MW_PR008_GroundSteel_v001",
        "galv": "M_CA_MW_PR008_Galvanised_v001",
        "rubber": "M_CA_MW_PR008_Rubber_v001",
        "sensor": "M_CA_MW_PR008_SensorGlass_v001",
        "white": "M_CA_MW_PR008_LabelPlate_v001",
        "red": "M_CA_MW_PR008_EStopRed_v001",
        "blue": "M_CA_MW_PR008_DriveBlue_v001",
    }.items()
}
if any(value is None for value in material_assets.values()):
    raise RuntimeError("Missing retained PR-008/PR-009 shared material hierarchy")


def choose_material(slot_name):
    value = slot_name.lower()
    if "yellow" in value or "safety" in value: return material_assets["yellow"]
    if "green" in value or "cairnwell" in value: return material_assets["green"]
    if "galv" in value or "zinc" in value: return material_assets["galv"]
    if "groundsteel" in value or "steel" in value or "metal" in value: return material_assets["steel"]
    if "rubber" in value: return material_assets["rubber"]
    if "sensor" in value or "glass" in value or "lens" in value: return material_assets["sensor"]
    if "label" in value or "white" in value or "lightgrey" in value: return material_assets["white"]
    if "red" in value or "estop" in value: return material_assets["red"]
    if "blue" in value or "drive" in value: return material_assets["blue"]
    return material_assets["charcoal"]


def apply_materials(component, mesh):
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        component.set_material(index, choose_material(slot_name))


def spawn_mesh(label, mesh_path, location, rotation, movable, collision, tags):
    mesh = library.load_asset(mesh_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing imported mesh {mesh_path}")
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name(tag) for tag in tags]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC)
    apply_materials(component, mesh)
    no_collision = collision == "NoCollision"
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION if no_collision else unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name(unreal.Name("NoCollision" if no_collision else "BlockAll"))
    component.set_editor_property("can_ever_affect_navigation", not no_collision and not movable)
    return actor


pr009_actors = []
for entry in pr009_files:
    stem = Path(entry["file"]).stem
    movable_candidate = stem.startswith("SK_")
    pr009_actors.append(spawn_mesh(
        stem, f"{PR009_DEST}/{stem}", unreal.Vector(600.0, -2000.0, 0.0), unreal.Rotator(yaw=-90.0),
        movable_candidate, "BlockAll", (
            "LB.Asset.Candidate.v083", "LB.Asset.CandidateNotPromoted", "LB.Station.PR009",
            "LB.Authority.CairnwellRemainingMachineryPack.v1", "LB.Control.ControlRoomOnly",
            "LB.Runtime.DecompositionRequired" if movable_candidate else "LB.Structure.PR009",
        )
    ))


def transfer_local_to_world(local_m):
    x, y, z = local_m
    return unreal.Vector(-20.0 + y * 100.0, -2000.0 - x * 100.0, z * 100.0)


transfer_actors = []
for record in TRANSFER_MANIFEST["records"]:
    transfer_actors.append(spawn_mesh(
        record["name"], f"{TRANSFER_DEST}/{record['name']}", transfer_local_to_world(record["local_location_m"]),
        unreal.Rotator(yaw=-90.0), record["movable"], record["collision"], (
            "LB.Asset.Candidate.v083", "LB.Asset.CandidateNotPromoted", "LB.Interface.PR008.PR009",
            "LB.SupportedTransfer", "LB.Control.ControlRoomOnly",
        )
    ))


def text_actor(label, value, location, yaw, size, colour):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=yaw))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name("LB.Asset.Candidate.v083"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Identity.CairnwellMoorcross")]
    component = actor.text_render
    component.set_text(value)
    component.set_world_size(size)
    component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity = [
    text_actor("PR009Brand", "CAIRNWELL AUTOMOTIVE / MOORCROSS WORKS", (610.0, -2259.0, 225.0), 90.0, 3.2, unreal.Color(45, 130, 105, 255)),
    text_actor("PR009Station", "PR-009  AUTOMATED BLANK STACKER", (610.0, -2259.0, 217.0), 90.0, 3.0, unreal.Color(220, 225, 220, 255)),
    text_actor("Interface", "SUPPORTED PR-008 / PR-009 TRANSFER", (100.0, -2142.5, 142.0), 90.0, 2.6, unreal.Color(220, 225, 220, 255)),
]


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR009.v083"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


cameras = [
    camera("Process", (-650, -1350, 620), (240, -2000, 115), 55),
    camera("Interface", (-230, -1550, 320), (110, -2000, 100), 44),
    camera("PR009Cell", (1080, -1350, 560), (600, -2000, 135), 50),
    camera("Elevated", (250, -1050, 950), (430, -2000, 110), 58),
]


def aggregate_bounds(actors):
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    for actor in actors:
        origin, extent = actor.get_actor_bounds(False, False)
        amin = [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z]
        amax = [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z]
        mins = [min(mins[i], amin[i]) for i in range(3)]
        maxs = [max(maxs[i], amax[i]) for i in range(3)]
    return mins, maxs


pr009_min, pr009_max = aggregate_bounds(pr009_actors)
transfer_min, transfer_max = aggregate_bounds(transfer_actors)
pr009_expected = {"min": [220.0, -2260.0, 0.0], "max": [980.0, -1740.0, 425.0]}
pr009_within = all(pr009_min[i] >= pr009_expected["min"][i] - 1.0 and pr009_max[i] <= pr009_expected["max"][i] + 1.0 for i in range(3))
transfer_closes_span = transfer_min[0] <= -19.9 and transfer_max[0] >= 219.9
if not pr009_within:
    raise RuntimeError(f"PR-009 imported bounds exceed EST envelope: min={pr009_min} max={pr009_max}")
if not transfer_closes_span:
    raise RuntimeError(f"Supported transfer does not close measured span: minX={transfer_min[0]} maxX={transfer_max[0]}")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(PR009_DEST, only_if_is_dirty=False, recursive=True)
library.save_directory(PR009_COLLISION_DEST, only_if_is_dirty=False, recursive=True)
library.save_directory(TRANSFER_DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr009-physical-integration-v083/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PR009_V002_SOURCE_IMPORT_NATIVE_AUTHORITY_MAP_BINDING_AND_SEPARATELY_SUPPORTED_PR008_PR009_TRANSFER_PHYSICAL_GATE_PASS__MOTION_DECOMPOSITION_COLLISION_NAVIGATION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP, "base_map": BASE,
    "source_candidate": "Candidate_v002", "source_intake_status": PR009_INTAKE["status"],
    "native_authority": {"label": station.get_actor_label(), "class": station.get_class().get_name(), "control_authority": "CW.MW.CONTROL_ROOM"},
    "imported_fbx_group_count": len(pr009_import_files),
    "pr009_actor_count": len(pr009_actors), "transfer_actor_count": len(transfer_actors),
    "pr009_measured_bounds_cm": {"min": pr009_min, "max": pr009_max},
    "pr009_est_envelope_cm": pr009_expected, "pr009_within_est_envelope": pr009_within,
    "transfer_measured_bounds_cm": {"min": transfer_min, "max": transfer_max},
    "transfer_closes_measured_horizontal_span": transfer_closes_span,
    "pr009_moving_groups_require_native_decomposition": [Path(entry["file"]).stem for entry in pr009_files if Path(entry["file"]).stem.startswith("SK_")],
    "lod_candidates_imported_not_placed": [Path(entry["file"]).stem for entry in pr009_import_files if "_LOD" in entry["file"]],
    "collision_candidate_imported_not_bound": [Path(entry["file"]).stem for entry in pr009_import_files if entry["file"].startswith("UCX_")],
    "identity": [actor.get_actor_label() for actor in identity],
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(payload["status"])
unreal.SystemLibrary.quit_editor()
