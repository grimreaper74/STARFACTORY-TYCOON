"""Replace generic v082 anchor primitives with authored measured modules in v210."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/PR008/ServoBlankingLine/ReleaseAnchorBase_v001"
MANIFEST = SOURCE / "pr008_release_anchor_base_manifest_v001.json"
BASE = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210"
DEST = "/Game/LineBoss/Stations/Press/PR008/ReleaseAnchorBase_v001"
MAT_DEST = DEST + "/Materials"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr008_authored_anchor_build_v210.json"
PREFIX = "LB_PR008_V210_"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary

base_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107.umap"
base_hash_before = hashlib.sha256(base_file.read_bytes()).hexdigest().upper()
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("could not create isolated v210 from retained v107")


def make_material(name, colour, metallic, roughness):
    asset = tools.create_asset(name, MAT_DEST, unreal.Material, unreal.MaterialFactoryNew())
    if asset is None:
        raise RuntimeError(f"could not create material {name}")
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -320, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -320, 40)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -320, 130)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


materials = {
    "CA_AnchorPlate": make_material("M_PR008_V210_AnchorPlate", (0.085, 0.098, 0.102), 0.82, 0.40),
    "CA_FastenerSteel": make_material("M_PR008_V210_FastenerSteel", (0.28, 0.31, 0.32), 0.90, 0.28),
    "CA_Weld": make_material("M_PR008_V210_Weld", (0.045, 0.053, 0.056), 0.72, 0.54),
}

records = json.loads(MANIFEST.read_text(encoding="utf-8"))
tasks = []
for record in records:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / record["fbx"]),
        "destination_path": DEST,
        "destination_name": "SM_" + record["name"] + "_v001",
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)
tools.import_asset_tasks(tasks)


def assign_material_slots(component, mesh):
    slot_names = [str(value.get_editor_property("material_slot_name"))
                  for value in mesh.get_editor_property("static_materials")]
    for index, slot_name in enumerate(slot_names):
        clean = slot_name.split(".")[-1]
        if clean not in materials:
            raise RuntimeError(f"unmapped material slot {slot_name} on {mesh.get_name()}")
        component.set_material(index, materials[clean])
    return slot_names


# Remove only the 48 inherited generic presentation primitives from this child.
# Their v107/v082 history and source assets remain intact.
old_anchor_actors = [actor for actor in actors_api.get_all_level_actors()
                     if actor.get_actor_label().startswith("LB_PR008_V082_Base")
                     and (actor.get_actor_label().endswith("_Plate") or actor.get_actor_label().endswith("_Stud"))]
old_anchor_labels = sorted(actor.get_actor_label() for actor in old_anchor_actors)
if len(old_anchor_actors) != 48:
    raise RuntimeError(f"expected 48 inherited v082 anchor primitives, found {len(old_anchor_actors)}")
for actor in old_anchor_actors:
    if not actors_api.destroy_actor(actor):
        raise RuntimeError(f"could not replace inherited anchor actor {actor.get_actor_label()}")

common_tags = [
    unreal.Name("LB.Asset.Candidate.v210"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Station.PR008"),
    unreal.Name("LB.Foundation.PR008.MeasuredAuthoredAnchor"),
    unreal.Name("LB.Navigation.Neutral"),
]
created = []
rows = []
dimension_failures = []
for record in records:
    mesh_path = f"{DEST}/SM_{record['name']}_v001"
    mesh = library.load_asset(mesh_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"missing imported mesh {mesh_path}")
    expected_cm = [value / 10.0 for value in record["dimensions_mm"]]
    actual = mesh.get_bounds().box_extent * 2.0
    actual_cm = [float(actual.x), float(actual.y), float(actual.z)]
    drift_mm = [abs(actual_cm[index] - expected_cm[index]) * 10.0 for index in range(3)]
    if max(drift_mm) > 2.0:
        dimension_failures.append({"asset": mesh_path, "drift_mm": drift_mm})
    world = record["world_placement_cm"]
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*world), unreal.Rotator())
    actor.set_actor_label(PREFIX + record["name"])
    actor.tags = common_tags + [unreal.Name("LB.Source.PR008.ReleaseAnchorBase.v001")]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    slots = assign_material_slots(component, mesh)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    created.append(actor)
    rows.append({
        "actor": actor.get_actor_label(),
        "asset": mesh_path,
        "world_location_cm": world,
        "measured_corner_offsets_cm": record["measured_corner_offsets_cm"],
        "source_dimensions_mm": record["dimensions_mm"],
        "unreal_dimensions_cm": actual_cm,
        "dimension_drift_mm": drift_mm,
        "material_slots": slots,
        "collision": "NoCollision",
        "navigation": False,
    })


def add_camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = common_tags + [unreal.Name("LB.Camera.Fixed.PR008.v210")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    return actor


cameras = [
    add_camera("AnchorOperatorClose", (-650, -2420, 145), (-650, -2000, 25), 48.0),
    add_camera("AnchorDriveClose", (-335, -1540, 150), (-335, -2000, 25), 49.0),
    add_camera("AuthoredAnchorProcess", (-1380, -3150, 610), (-560, -2000, 125), 57.0),
]

all_actors = actors_api.get_all_level_actors()
stations = [actor for actor in all_actors if isinstance(actor, unreal.LBPR008Station)]
expected_bindings = {
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Lower_01": "PR008_FeedRollLowerMover",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Lower_01": "PR008_FeedRollLowerMover",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Upper_01": "PR008_FeedRollUpperMover",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Upper_01": "PR008_FeedRollUpperMover",
    "LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Operator": "PR008_EdgeGuideOperatorMover",
    "LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Drive": "PR008_EdgeGuideDriveMover",
    "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage1_01": "PR008_TelescopeStage1Mover",
    "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage2_01": "PR008_TelescopeStage2Mover",
    "LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage3_01": "PR008_TelescopeStage3Mover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchSlide_01": "PR008_PrePunchMover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchScrapFlap_01": "PR008_ScrapFlapMover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Operator": "PR008_ServiceDoorOperatorMover",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Drive": "PR008_ServiceDoorDriveMover",
    "LB_PR008_V069_SM_CA_MW_PR008_ShearBladeBeam_01": "PR008_GuillotineMover",
}
by_label = {actor.get_actor_label(): actor for actor in all_actors}
binding_rows = []
for label, expected_parent in expected_bindings.items():
    actor = by_label.get(label)
    root = actor.static_mesh_component if isinstance(actor, unreal.StaticMeshActor) else None
    parent = root.get_attach_parent() if root else None
    binding_rows.append({
        "actor": label,
        "expected_parent": expected_parent,
        "actual_parent": parent.get_name() if parent else None,
    })

failures = []
if len(stations) != 1:
    failures.append(f"expected one PR-008 authority, found {len(stations)}")
if any(row["actual_parent"] != row["expected_parent"] for row in binding_rows):
    failures.append("one or more inherited PR-008 mover attachments changed")
if dimension_failures:
    failures.append(f"source-to-Unreal dimension drift exceeds 2 mm: {dimension_failures}")
if len(created) != 6 or len(cameras) != 3:
    failures.append("authored anchor module or camera count mismatch")
remaining_old = [actor.get_actor_label() for actor in all_actors
                 if actor.get_actor_label().startswith("LB_PR008_V082_Base")]
if remaining_old:
    failures.append(f"generic v082 anchor primitives remain: {remaining_old}")
if not levels.save_current_level():
    failures.append("could not save v210")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

base_hash_after = hashlib.sha256(base_file.read_bytes()).hexdigest().upper()
if base_hash_after != base_hash_before:
    failures.append("protected retained v107 parent hash changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-pr008-authored-anchor-build-v210/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PR008_V210_MEASURED_AUTHORED_ANCHOR_BUILD_PASS__RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
               if not failures else "PR008_V210_BUILD_FAIL__NOT_PROMOTED"),
    "source_map": BASE,
    "map": MAP,
    "source_manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
    "removed_generic_v082_actor_count": len(old_anchor_labels),
    "removed_generic_v082_actors": old_anchor_labels,
    "authored_module_count": len(created),
    "authored_modules": rows,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "pr008_authority_count": len(stations),
    "pr008_mover_binding_count": len(binding_rows),
    "pr008_mover_bindings": binding_rows,
    "protected_v107_sha256_before": base_hash_before,
    "protected_v107_sha256_after": base_hash_after,
    "map_sha256": hashlib.sha256(map_file.read_bytes()).hexdigest().upper() if map_file.exists() else None,
    "machine_or_datum_changed": False,
    "runtime_authority_changed": False,
    "anchor_capacity_or_certification_claimed": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
