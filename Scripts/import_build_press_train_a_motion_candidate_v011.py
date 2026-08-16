"""Import exact v003 motion source into a fresh isolated Unreal child of v010."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v003"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v003.json"
SOURCE_VALIDATION = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_v003.json"
STAGING = ROOT / "Saved/ImportStaging/PressTrainAMotion_v011"
STAGING_RECEIPT = ROOT / "Saved/Audits/PressTrains/press_train_a_motion_staging_v011.json"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyMotion_v011"
AUTHORED_DEST = DEST + "/Authored"
MATERIAL_DEST = DEST + "/Materials"
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainARuntimeCandidate_v010"
MAP = "/Game/LineBoss/Maps/LB_PressTrainAMotionCandidate_v011"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_motion_build_v011.json"
SOURCE_MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainARuntimeCandidate_v010.umap"
TARGET_MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainAMotionCandidate_v011.umap"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
source_validation = json.loads(SOURCE_VALIDATION.read_text(encoding="utf-8"))
staging_receipt = json.loads(STAGING_RECEIPT.read_text(encoding="utf-8"))
if not source_validation.get("status", "").startswith("PASS") or not staging_receipt.get("status", "").startswith("PASS"):
    raise RuntimeError("v003 source validation or v011 staging is not PASS")
if library.does_asset_exist(MAP) or library.does_directory_exist(DEST) or OUT.exists():
    raise RuntimeError("Refusing to overwrite Train A motion v011")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


protected_source_hash = sha(SOURCE_MAP_FILE)


def import_mesh(path, destination, name):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(path), "destination_path": destination, "destination_name": name,
        "automated": True, "replace_existing": False, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "transform_vertex_to_absolute": False, "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tools.import_asset_tasks([task])
    asset = library.load_asset(f"{destination}/{name}")
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Import failed: {path}")
    return asset


authored_assets = {}
for row in staging_receipt["assets"]:
    authored_assets[row["asset"]] = import_mesh(STAGING / row["file"], AUTHORED_DEST, row["asset"])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

material_roles = (
    "Charcoal", "Foundation", "WorkedSteel", "Green", "SafetyYellow", "TrainABlue", "DarkRubber",
    "LabelIvory", "HydraulicRed", "PneumaticBlue", "ElectricalOrange", "InspectionWhite", "PanelSteel", "BlankSteel",
)
materials = {}
for role in material_roles:
    source_material = f"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v005/Materials/M_CA_MW_PTA_{role}_Integration_v005"
    target_material = f"{MATERIAL_DEST}/M_CA_MW_PTA_{role}_Motion_v011"
    if not library.duplicate_asset(source_material, target_material):
        raise RuntimeError(f"Could not duplicate retained material: {role}")
    materials[role] = library.load_asset(target_material)


def slot_names(mesh):
    return [str(row.get_editor_property("material_slot_name")) for row in mesh.get_editor_property("static_materials")]


def role_for(slot):
    key = slot.lower()
    tests = (
        ("foundation", "Foundation"), ("inspectionwhite", "InspectionWhite"),
        ("inspectionglass", "TrainABlue"), ("blanksteel", "BlankSteel"),
        ("panelsteel", "PanelSteel"), ("yellow", "SafetyYellow"),
        ("traina", "TrainABlue"), ("hydraulic", "HydraulicRed"),
        ("pneumatic", "PneumaticBlue"), ("electrical", "ElectricalOrange"),
        ("rubber", "DarkRubber"), ("ivory", "LabelIvory"), ("green", "Green"),
    )
    for token, role in tests:
        if token in key:
            return role
    if "worked" in key or "steel" in key or "metal" in key:
        return "WorkedSteel"
    return "Charcoal"


for mesh in authored_assets.values():
    for index, slot in enumerate(slot_names(mesh)):
        mesh.set_material(index, materials[role_for(slot)])
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

if not levels.new_level_from_template(MAP, SOURCE_MAP):
    raise RuntimeError("Could not create v011 from retained native runtime v010")


def tags(actor):
    return {str(value) for value in actor.tags}


def add_tags(actor, *values):
    current = [str(value) for value in actor.tags]
    for value in values:
        if value not in current:
            current.append(value)
    actor.set_editor_property("tags", [unreal.Name(value) for value in current])


old_presentation = [
    actor for actor in actors_api.get_all_level_actors()
    if isinstance(actor, unreal.StaticMeshActor)
    and "LB.PressTrain.TrainA.AssemblyDetail.v009" in tags(actor)
    and any(value.startswith("LB.PressTrain.Role.") for value in tags(actor))
]
if len(old_presentation) != 309:
    raise RuntimeError(f"Expected 309 inherited v009 presentation actors, found {len(old_presentation)}")
actors_api.destroy_actors(old_presentation)

for actor in actors_api.get_all_level_actors():
    add_tags(actor, "LB.PressTrain.TrainA.Motion.v011", "LB.Asset.Candidate.v011",
             "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented")

authored_map = {row["object"]: row["asset"] for row in staging_receipt["instances"]}
placed_by_name = {}
role_counts = Counter()
for record in manifest["instances"]:
    mesh = authored_assets[authored_map[record["name"]]]
    loc = record["location_mm"]
    rot = record["rotation_deg"]
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*(value / 10.0 for value in loc)),
        unreal.Rotator(pitch=rot[1], yaw=rot[2], roll=rot[0]),
    )
    actor.set_actor_label(record["name"] + "_UEv011")
    add_tags(actor,
             "LB.PressTrain.TrainA.Motion.v011", "LB.Asset.Candidate.v011", "LB.Asset.CandidateNotPromoted",
             "LB.Authority.WorldPlacement.TBCNotInvented", "LB.Scope.IsolatedLocalOrigin",
             f"LB.PressTrain.Stage.{record['stage']}", f"LB.PressTrain.Role.{record['role']}",
             "LB.PressTrain.ProcessDirection.PositiveY")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*record["scale"]))
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(slot_names(mesh)):
        actor.static_mesh_component.set_material(index, materials[role_for(slot)])
    placed_by_name[record["name"]] = actor
    role_counts[record["role"]] += 1

hierarchy_edges = []
for record in manifest["instances"]:
    parent_name = record.get("runtime_parent")
    if not parent_name:
        continue
    child = placed_by_name[record["name"]]
    parent = placed_by_name.get(parent_name)
    if parent is None:
        raise RuntimeError(f"Missing runtime parent {parent_name} for {record['name']}")
    child.attach_to_actor(parent, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    hierarchy_edges.append({"child": record["name"], "parent": parent_name})

authority_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBPressTrainAStation")
authorities = [actor for actor in actors_api.get_all_level_actors() if authority_class and isinstance(actor, authority_class)]
if len(authorities) != 1:
    raise RuntimeError(f"Expected exactly one inherited native authority, found {len(authorities)}")
add_tags(authorities[0], "LB.PressTrain.TrainA.Motion.v011")

live_hmis = [actor for actor in actors_api.get_all_level_actors() if "LB.HMI.PressTrainA.LiveState" in tags(actor)]
if len(live_hmis) != 1:
    raise RuntimeError(f"Expected exactly one inherited live HMI, found {len(live_hmis)}")
live_hmis[0].set_actor_label("CA_MW_PTA_HMI_LiveState_v011")

if not levels.save_current_level():
    raise RuntimeError("Could not save Train A motion v011")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
if not TARGET_MAP_FILE.exists():
    raise RuntimeError("Train A motion v011 map file missing after save")
if sha(SOURCE_MAP_FILE) != protected_source_hash:
    raise RuntimeError("Protected v010 source map changed during v011 build")

minimum = unreal.Vector(1e12, 1e12, 1e12)
maximum = unreal.Vector(-1e12, -1e12, -1e12)
for actor in placed_by_name.values():
    origin, extent = actor.get_actor_bounds(False, False)
    minimum.x = min(minimum.x, origin.x - extent.x); minimum.y = min(minimum.y, origin.y - extent.y); minimum.z = min(minimum.z, origin.z - extent.z)
    maximum.x = max(maximum.x, origin.x + extent.x); maximum.y = max(maximum.y, origin.y + extent.y); maximum.z = max(maximum.z, origin.z + extent.z)
bounds_mm = [round((maximum.x - minimum.x) * 10, 3), round((maximum.y - minimum.y) * 10, 3), round((maximum.z - minimum.z) * 10, 3)]

report = {
    "$schema": "cairnwell/audit/press-train-a-motion-build-v011/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EXACT_V003_MOTION_SOURCE_IN_NATIVE_V010_RUNTIME_ENVIRONMENT__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "source_map_sha256": protected_source_hash,
    "map": MAP,
    "map_sha256": sha(TARGET_MAP_FILE),
    "source_manifest_sha256": sha(MANIFEST_PATH),
    "source_blend_sha256": sha(SOURCE / "CA_MW_PressTrainA_AssemblyStudy_v003.blend"),
    "removed_v009_presentation_actor_count": len(old_presentation),
    "placed_manifest_actor_count": len(placed_by_name),
    "deduplicated_authored_asset_count": len(authored_assets),
    "material_asset_count": len(materials),
    "aggregate_actor_bounds_mm": bounds_mm,
    "native_authority_count": len(authorities),
    "live_hmi_count": len(live_hmis),
    "runtime_hierarchy_edge_count": len(hierarchy_edges),
    "runtime_hierarchy_edges": hierarchy_edges,
    "motion_role_counts": {role: role_counts[role] for role in (
        "moving_press_slide", "moving_upper_die", "carried_workpiece_state",
        "unload_robot_shoulder_runtime", "state_beacon_red", "state_beacon_amber", "state_beacon_green")},
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
