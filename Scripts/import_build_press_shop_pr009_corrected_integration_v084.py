"""Build isolated corrected-source PR-009 integration candidate v084."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
CANDIDATE = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002"
EXPORTS = CANDIDATE / "PR009_Exports/v002_candidate"
EXPORT_MANIFEST = json.loads((CANDIDATE / "PR009_Audits/v002/PR009_FBX_EXPORT_MANIFEST_v002.json").read_text(encoding="utf-8"))
BINDING = json.loads((CANDIDATE / "PR009_Audits/v002/PR009_SK_BINDING_MANIFEST_v002.json").read_text(encoding="utf-8"))
INTAKE = json.loads((ROOT / "Saved/Audits/press_shop_pr009_source_intake_v002.json").read_text(encoding="utf-8"))
MODULAR_GATE = json.loads((ROOT / "Saved/Audits/press_shop_pr009_modular_import_pilot_v003.json").read_text(encoding="utf-8"))
TRANSFER = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Interface_v001"
TRANSFER_MANIFEST = json.loads((TRANSFER / "pr008_pr009_supported_transfer_manifest_v001.json").read_text(encoding="utf-8"))

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008ExternalAnchorTabsCandidate_v082"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009CorrectedIntegrationCandidate_v084"
STATIC_DEST = "/Game/LineBoss/Candidates/PressShop/PR009/v003/Static"
MODULAR_ROOT = "/Game/LineBoss/Candidates/PressShop/PR009/ModularImportPilot_v003"
TRANSFER_DEST = "/Game/LineBoss/Candidates/PressShop/PR009/v002/Interface"
PREFIX = "LB_PR009_V084_"
OUT = ROOT / "Saved/Audits/press_shop_pr009_corrected_integration_v084.json"
STATION_LOCATION = unreal.Vector(600.0, -2000.0, 0.0)
STATION_ROTATION = unreal.Rotator(yaw=-90.0)
CHILD_EFFECTIVE_ROTATION = unreal.Rotator(yaw=90.0)

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def import_combined_static(path, destination, name):
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
        "generate_lightmap_u_vs": True, "auto_generate_collision": False,
        "remove_degenerates": True, "import_uniform_scale": 1.0,
    })
    try:
        data.set_editor_property("transform_vertex_to_absolute", True)
    except Exception:
        pass
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])


if INTAKE.get("status") != "CANONICAL_V002_SOURCE_INTAKE_HASH_AND_MANIFEST_PASS__UNREAL_GATES_REQUIRED__NOT_PROMOTED":
    raise RuntimeError("Canonical corrected PR-009 source intake is not passed")
if not MODULAR_GATE.get("status", "").startswith("PR009_CORRECTED_SIX_GROUP_UNREAL_IMPORT_") or MODULAR_GATE.get("failures"):
    raise RuntimeError("Corrected six-group Unreal modular import gate is not passed")
if BINDING.get("group_count") != 6 or sum(group["object_count"] for group in BINDING["groups"]) != 158:
    raise RuntimeError("Corrected PR-009 binding manifest is incomplete")

static_entries = [
    entry for entry in EXPORT_MANIFEST["files"]
    if entry["file"].startswith("SM_") and "_LOD1" not in entry["file"] and "_LOD2" not in entry["file"]
]
for entry in static_entries:
    stem = Path(entry["file"]).stem
    import_combined_static(EXPORTS / entry["file"], STATIC_DEST, stem)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR009CorrectedIntegrationCandidate_v084.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP) or not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not prepare isolated v084 map")
    unreal.log("CAIRNWELL_PR009_V084_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)

if any(isinstance(actor, unreal.LBPR009Station) for actor in actors_api.get_all_level_actors()):
    raise RuntimeError("Unexpected inherited PR-009 native station in v082 base")

station = actors_api.spawn_actor_from_class(unreal.LBPR009Station, STATION_LOCATION, STATION_ROTATION)
station.set_actor_label(PREFIX + "Station_PR-009_NativeAuthority")
station.tags = [unreal.Name(value) for value in (
    "LB.Station.PR009", "LB.Authority.PR009.Native", "LB.Authority.RemoteHMI.SharedGateway",
    "LB.Authority.ControlRoom.CW.MW.CONTROL_ROOM", "LB.Asset.Candidate.v084",
    "LB.Asset.CandidateNotPromoted", "LB.Process.AutomatedBlankStacking",
)]

pr008_stations = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR008Station)]
if len(pr008_stations) != 1:
    raise RuntimeError(f"Expected one inherited native PR-008 authority, found {len(pr008_stations)}")
flows = [actor for actor in actors_api.get_all_level_actors()
         if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
if len(flows) != 1:
    raise RuntimeError(f"Expected one inherited native material-flow controller, found {len(flows)}")
flow = flows[0]
flow.tags = list(flow.tags) + [unreal.Name("LB.Traceability.PR008.PR009"), unreal.Name("LB.Asset.Candidate.v084")]
flow.bind_blank_stations(pr008_stations[0], station)

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
    raise RuntimeError("Missing retained Cairnwell Press Shop material hierarchy")


def choose_material(slot_name):
    value = slot_name.lower()
    if "yellow" in value or "safety" in value: return material_assets["yellow"]
    if "green" in value or "cairnwell" in value: return material_assets["green"]
    if "galv" in value or "zinc" in value or "mesh" in value: return material_assets["galv"]
    if "groundsteel" in value or "steel" in value or "metal" in value or "aluminium" in value: return material_assets["steel"]
    if "rubber" in value: return material_assets["rubber"]
    if "sensor" in value or "glass" in value or "lens" in value or "screen" in value: return material_assets["sensor"]
    if "label" in value or "white" in value or "lightgrey" in value: return material_assets["white"]
    if "red" in value or "estop" in value: return material_assets["red"]
    if "blue" in value or "drive" in value: return material_assets["blue"]
    return material_assets["charcoal"]


def apply_materials(component, mesh):
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        component.set_material(index, choose_material(slot_name))


def enable_complex_collision(mesh):
    try:
        body_setup = mesh.get_editor_property("body_setup")
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        mesh.modify()
        mesh.post_edit_change()
        library.save_loaded_asset(mesh, only_if_is_dirty=False)
        return True
    except Exception as exc:
        unreal.log_warning(f"PR009 v084 collision setup unavailable for {mesh.get_name()}: {exc}")
        return False


def spawn_mesh(label, mesh_path, location, rotation, movable, collision, nav, tags):
    mesh = library.load_asset(mesh_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing imported mesh {mesh_path}")
    if collision:
        enable_complex_collision(mesh)
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name(tag) for tag in tags]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC)
    apply_materials(component, mesh)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("BlockAll" if collision else "NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", nav)
    return actor


static_actors = []
for entry in static_entries:
    stem = Path(entry["file"]).stem
    static_actors.append(spawn_mesh(
        stem, f"{STATIC_DEST}/{stem}", STATION_LOCATION, STATION_ROTATION,
        False, True, True,
        ("LB.Asset.Candidate.v084", "LB.Asset.CandidateNotPromoted", "LB.Station.PR009", "LB.Structure.PR009", "LB.Control.ControlRoomOnly"),
    ))


def child_world_location(source_cm):
    source_x, source_y, source_z = source_cm
    return unreal.Vector(600.0 - source_y, -2000.0 - source_x, source_z)


modular_actors = []
binding_targets = Counter()
for group in BINDING["groups"]:
    destination = f"{MODULAR_ROOT}/{group['export_group']}"
    for record in group["objects"]:
        asset_name = record["object_name"].replace(".", "_")
        actor = spawn_mesh(
            "MOD_" + asset_name,
            f"{destination}/{asset_name}",
            child_world_location(record["source_world"]["location_cm"]),
            CHILD_EFFECTIVE_ROTATION,
            True, False, False,
            ("LB.Asset.Candidate.v084", "LB.Asset.CandidateNotPromoted", "LB.Station.PR009",
             "LB.Runtime.NativePresentationBound", "LB.Control.ControlRoomOnly"),
        )
        if not station.bind_presentation_actor(
            unreal.Name(record["object_name"]), unreal.Name(record["semantic"]),
            unreal.Name(record["intended_binding_parent"]), actor):
            raise RuntimeError(f"Native presentation binding failed for {record['object_name']}")
        parent = actor.root_component.get_attach_parent()
        if parent is None:
            raise RuntimeError(f"No native presentation parent after binding {record['object_name']}")
        binding_targets[str(parent.get_name())] += 1
        modular_actors.append(actor)


def transfer_local_to_world(local_m):
    x, y, z = local_m
    return unreal.Vector(-20.0 + y * 100.0, -2000.0 - x * 100.0, z * 100.0)


transfer_actors = []
for record in TRANSFER_MANIFEST["records"]:
    transfer_actors.append(spawn_mesh(
        record["name"], f"{TRANSFER_DEST}/{record['name']}",
        transfer_local_to_world(record["local_location_m"]), unreal.Rotator(yaw=-90.0),
        record["movable"], record["collision"] == "BlockAll",
        record["collision"] == "BlockAll" and not record["movable"],
        ("LB.Asset.Candidate.v084", "LB.Asset.CandidateNotPromoted", "LB.Interface.PR008.PR009",
         "LB.SupportedTransfer", "LB.Control.ControlRoomOnly"),
    ))


def text_actor(label, value, location, yaw, size, colour):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=yaw))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name("LB.Asset.Candidate.v084"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Identity.CairnwellMoorcross")]
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
    text_actor("Brand", "CAIRNWELL AUTOMOTIVE / MOORCROSS WORKS", (600.0, -2262.0, 225.0), 90.0, 3.2, unreal.Color(45, 130, 105, 255)),
    text_actor("Station", "PR-009  AUTOMATED BLANK STACKER", (600.0, -2262.0, 217.0), 90.0, 3.0, unreal.Color(225, 230, 225, 255)),
]


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR009.v084"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


cameras = [
    camera("Process", (-650, -1350, 620), (260, -2000, 125), 54),
    camera("Interface", (-240, -1540, 335), (120, -2000, 105), 43),
    camera("PR009Cell", (1110, -1330, 570), (600, -2000, 145), 49),
    camera("Elevated", (260, -1030, 940), (440, -2000, 120), 57),
]

# PR-009 is outside the inherited PR-004 local navigation bounds. Author
# invisible local coverage and explicitly exclude the guarded process envelope.
nav_bounds = actors_api.spawn_actor_from_class(
    unreal.NavMeshBoundsVolume, unreal.Vector(600.0, -2000.0, 350.0), unreal.Rotator())
if nav_bounds is None:
    raise RuntimeError("Could not spawn PR-009 navigation bounds")
nav_bounds.set_actor_label(PREFIX + "NavBounds_LocalCoverage")
nav_bounds.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v084", "LB.Asset.CandidateNotPromoted",
    "LB.PR009.Navigation", "LB.Navigation.LocalCoverage")]
nav_bounds.set_actor_scale3d(unreal.Vector(9.0, 8.0, 3.5))

nav_exclusion = actors_api.spawn_actor_from_class(
    unreal.NavModifierVolume, unreal.Vector(600.0, -2000.0, 250.0), unreal.Rotator())
if nav_exclusion is None:
    raise RuntimeError("Could not spawn PR-009 protected-space navigation exclusion")
nav_exclusion.set_actor_label(PREFIX + "NavModifier_ProtectedProcessSpace")
nav_exclusion.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v084", "LB.Asset.CandidateNotPromoted",
    "LB.PR009.Navigation", "LB.Navigation.ProtectedProcessSpace")]
nav_exclusion.set_actor_scale3d(unreal.Vector(4.0, 3.0, 2.5))
nav_null_area = unreal.load_class(None, "/Script/NavigationSystem.NavArea_Null")
if nav_null_area is None:
    raise RuntimeError("Could not load NavArea_Null")
nav_exclusion.set_editor_property("area_class", nav_null_area)

unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(), "RebuildNavigation")
for nav_actor in actors_api.get_all_level_actors():
    if isinstance(nav_actor, unreal.RecastNavMesh):
        nav_actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        nav_actor.set_editor_property("can_be_main_nav_data", True)

if len(modular_actors) != 158 or len(static_actors) != len(static_entries):
    raise RuntimeError("Corrected PR-009 actor population is incomplete")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(STATIC_DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-corrected-integration-v084/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PR009_V084_CORRECTED_SOURCE_STATIC_AND_158_PART_NATIVE_PRESENTATION_BINDING_TRANSACTIONAL_PR008_PR009_AUTHORITY_MAP_BUILD_PASS__COLLISION_NAVIGATION_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "source_candidate": "Candidate_v002 corrected final handoff",
    "source_intake_status": INTAKE["status"],
    "modular_import_status": MODULAR_GATE["status"],
    "native_authority": station.get_actor_label(),
    "material_flow_authority": flow.get_actor_label(),
    "static_group_count": len(static_actors),
    "modular_visual_actor_count": len(modular_actors),
    "transfer_actor_count": len(transfer_actors),
    "native_binding_targets": dict(sorted(binding_targets.items())),
    "identity": [actor.get_actor_label() for actor in identity],
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "component_scale_contract": [1.0, 1.0, 1.0],
    "child_basis_contract": "fixed station yaw -90 plus pivot-preserving child relative yaw 180 (effective world yaw +90)",
    "promotion_authorized": False,
    "remaining_gates": ["collision", "navigation", "runtime presentation", "save in-map", "fresh fixed-camera visual review against Pro"],
    "pr010_started": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(payload["status"])
unreal.SystemLibrary.quit_editor()
