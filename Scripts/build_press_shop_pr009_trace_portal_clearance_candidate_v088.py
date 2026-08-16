"""Build isolated PR-009 v088 with the dimensioned trace-portal clearance asset."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
PARENT_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ReleaseCollisionCandidate_v087"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009TracePortalClearanceCandidate_v088"
SOURCE_ROOT = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/TracePortalClearance_v001"
SOURCE_FBX = SOURCE_ROOT / "PR009_Exports/SM_CA_MW_PR009_TracePortal_Clearance_01_v001.fbx"
SOURCE_AUDIT = SOURCE_ROOT / "PR009_Audits/PR009_TRACE_PORTAL_CLEARANCE_SOURCE_v001.json"
DEST = "/Game/LineBoss/Candidates/PressShop/PR009/v088/TracePortal"
ASSET_NAME = "SM_CA_MW_PR009_TracePortal_Clearance_01_v001"
ASSET_PATH = f"{DEST}/{ASSET_NAME}"
OUT = ROOT / "Saved/Audits/PR009_InMap_v088/trace_portal_clearance_build.json"

lib = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def import_combined_static():
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE_FBX),
        "destination_path": DEST,
        "destination_name": ASSET_NAME,
        "automated": True,
        "replace_existing": True,
        "replace_existing_settings": True,
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
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
        "import_uniform_scale": 1.0,
    })
    try:
        data.set_editor_property("transform_vertex_to_absolute", True)
    except Exception:
        pass
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = lib.load_asset(ASSET_PATH)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Derived trace portal did not import as one static mesh: {ASSET_PATH}")
    return mesh


def source_to_unreal_box(record):
    rotation = record.get("rotation_euler_rad", [0.0, 0.0, 0.0])
    rotation_degrees = [value * 180.0 / 3.141592653589793 for value in rotation]
    if any(abs(value) > 0.01 for value in rotation_degrees[:2]):
        raise RuntimeError(f"Unsupported non-upright portal primitive {record['name']}: {rotation_degrees}")
    return {
        "source": record["name"],
        "center_cm": [record["location_m"][0] * 100.0, -record["location_m"][1] * 100.0, record["location_m"][2] * 100.0],
        "dimensions_cm": [value * 100.0 for value in record["dimensions_m"]],
        "rotation_degrees": [0.0, -rotation_degrees[2], 0.0],
    }


def apply_collision(mesh, specs):
    body = mesh.get_editor_property("body_setup")
    aggregate = unreal.KAggregateGeom()
    boxes = []
    for spec in specs:
        box = unreal.KBoxElem()
        box.set_editor_property("center", unreal.Vector(*spec["center_cm"]))
        box.set_editor_property("rotation", unreal.Rotator(*spec["rotation_degrees"]))
        box.set_editor_property("x", spec["dimensions_cm"][0])
        box.set_editor_property("y", spec["dimensions_cm"][1])
        box.set_editor_property("z", spec["dimensions_cm"][2])
        boxes.append(box)
    aggregate.set_editor_property("box_elems", boxes)
    body.set_editor_property("agg_geom", aggregate)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    body.modify()
    mesh.modify()
    lib.save_loaded_asset(mesh, only_if_is_dirty=False)
    persisted = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
    counts = {
        "box": len(persisted.get_editor_property("box_elems")),
        "sphere": len(persisted.get_editor_property("sphere_elems")),
        "capsule": len(persisted.get_editor_property("sphyl_elems")),
        "convex": len(persisted.get_editor_property("convex_elems")),
    }
    counts["total"] = sum(counts.values())
    if counts != {"box": 3, "sphere": 0, "capsule": 0, "convex": 0, "total": 3}:
        raise RuntimeError(f"Derived portal collision persistence mismatch: {counts}")
    return counts


def label_version(actor):
    label = actor.get_actor_label()
    if "V087" in label:
        actor.set_actor_label(label.replace("V087", "V088"))
    actor.tags = [unreal.Name(str(tag).replace("v087", "v088")) for tag in actor.tags]


def main():
    source = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))
    expected_status = "DIMENSIONED_DERIVED_TRACE_PORTAL_SOURCE_PASS__UNREAL_IMPORT_RUNTIME_COLLISION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
    if source.get("status") != expected_status or source.get("failures"):
        raise RuntimeError("Derived portal source audit is not passed")
    if not source["source"].get("unchanged") or source["derived"].get("object_count") != 11:
        raise RuntimeError("Derived source integrity/object cardinality is not passed")
    if abs(source["derived"].get("clear_opening_m", 0.0) - 2.8) > 0.0005:
        raise RuntimeError("Derived source does not provide a 2800 mm opening")

    if not lib.does_asset_exist(TARGET_MAP):
        if not lib.duplicate_asset(PARENT_MAP, TARGET_MAP):
            raise RuntimeError(f"Could not duplicate immutable parent {PARENT_MAP}")
        if not lib.save_asset(TARGET_MAP, only_if_is_dirty=False):
            raise RuntimeError(f"Could not save isolated target {TARGET_MAP}")
        unreal.log("PR009_V088_MAP_DUPLICATED__RERUN_FOR_PORTAL_INTEGRATION")
        unreal.SystemLibrary.quit_editor()
        return

    mesh = import_combined_static()
    portal_records = [
        record
        for record in source["derived"]["objects_after"]
        if record.get("semantic") in {"trace_portal_beam", "trace_portal_post"}
    ]
    if len(portal_records) != 3:
        raise RuntimeError(f"Expected two derived posts and one beam, found {len(portal_records)}")
    collision_specs = [source_to_unreal_box(record) for record in portal_records]
    collision_counts = apply_collision(mesh, collision_specs)

    if not levels.load_level(TARGET_MAP):
        raise RuntimeError(f"Could not load {TARGET_MAP}")
    all_actors = list(actors_api.get_all_level_actors())
    portal_static = [
        actor for actor in all_actors
        if unreal.Name("LB.Structure.PR009") in actor.tags
        and "SM_CA_MW_PR009_TracePortal_01" in actor.get_actor_label()
    ]
    if len(portal_static) != 1:
        raise RuntimeError(f"Expected one inherited combined trace portal, found {len(portal_static)}")
    portal_actor = portal_static[0]
    component = portal_actor.get_component_by_class(unreal.StaticMeshComponent)
    old_mesh = component.get_editor_property("static_mesh")
    old_materials = [component.get_material(index) for index in range(component.get_num_materials())]
    component.set_static_mesh(mesh)
    for index, material in enumerate(old_materials):
        if material is not None and index < component.get_num_materials():
            component.set_material(index, material)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_editor_property("can_ever_affect_navigation", True)
    component.set_world_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    portal_actor.set_actor_label("LB_PR009_V088_SM_CA_MW_PR009_TracePortal_Clearance_01_v001")
    portal_actor.tags = [
        unreal.Name(str(tag).replace("v087", "v088"))
        for tag in portal_actor.tags
        if str(tag) != "LB.Collision.ReleaseCandidate.v087"
    ] + [
        unreal.Name("LB.Collision.ReleaseCandidate.v088"),
        unreal.Name("LB.Asset.DerivedTracePortalClearance.v001"),
        unreal.Name("LB.Dimension.ClearOpening.2800mm"),
    ]

    redundant_modular = [
        actor for actor in list(actors_api.get_all_level_actors())
        if "MOD_PR009_07_" in actor.get_actor_label()
    ]
    if redundant_modular:
        raise RuntimeError(f"Unexpected modular trace-portal duplicates in inherited six-SK binding: {len(redundant_modular)}")
    redundant_labels = sorted(actor.get_actor_label() for actor in redundant_modular)

    for actor in actors_api.get_all_level_actors():
        if actor is not portal_actor:
            label_version(actor)

    flows = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
    pr008 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR008Station)]
    pr009 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR009Station)]
    if len(flows) != 1 or len(pr008) != 1 or len(pr009) != 1:
        raise RuntimeError(f"Authority cardinality changed: flow={len(flows)} PR008={len(pr008)} PR009={len(pr009)}")
    flows[0].bind_blank_stations(pr008[0], pr009[0])

    transform = portal_actor.get_actor_transform()
    actor_scale = transform.scale3d
    if any(abs(value - 1.0) > 0.0001 for value in (actor_scale.x, actor_scale.y, actor_scale.z)):
        raise RuntimeError(f"Portal actor has non-identity scale: {actor_scale}")
    bounds = portal_actor.get_actor_bounds(False)
    if not levels.save_current_level():
        raise RuntimeError(f"Could not save {TARGET_MAP}")
    lib.save_directory(DEST, only_if_is_dirty=False, recursive=True)

    payload = {
        "$schema": "cairnwell/audit/pr009-trace-portal-clearance-build-v088/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "V088_DIMENSIONED_TRACE_PORTAL_INTEGRATED__FULL_RUNTIME_COLLISION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
        "parent_map": PARENT_MAP,
        "target_map": TARGET_MAP,
        "source_manifest": str(SOURCE_AUDIT.relative_to(ROOT)).replace("\\", "/"),
        "imported_asset": mesh.get_path_name(),
        "replaced_asset": old_mesh.get_path_name(),
        "portal_actor": portal_actor.get_actor_label(),
        "portal_actor_location_cm": [transform.translation.x, transform.translation.y, transform.translation.z],
        "portal_actor_rotation": [transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w],
        "portal_actor_scale": [actor_scale.x, actor_scale.y, actor_scale.z],
        "portal_actor_bounds_origin_cm": [bounds[0].x, bounds[0].y, bounds[0].z],
        "portal_actor_bounds_extent_cm": [bounds[1].x, bounds[1].y, bounds[1].z],
        "clear_opening_mm": 2800,
        "source_y_envelope_m": [2.945, 3.355],
        "collision": {"counts": collision_counts, "primitives": collision_specs},
        "removed_redundant_modular_portal_visuals": redundant_labels,
        "removed_redundant_modular_portal_visual_count": len(redundant_labels),
        "materials_preserved_from_v087_component": [material.get_path_name() if material else None for material in old_materials],
        "authoritative_gantry_travel_mm": 2800,
        "max_blank_mm": [1800, 2600],
        "source_v002_modified": False,
        "parent_v087_modified": False,
        "pr010_started": False,
        "robots_modified": False,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"PR009_V088_TRACE_PORTAL_INTEGRATION_PASS output={OUT}")
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
