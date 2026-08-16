"""Build v089 from unchanged v087 with authored open-channel transfer-guide collision."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
PARENT_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ReleaseCollisionCandidate_v087"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009TransferGuideCollisionCandidate_v089"
DEST = "/Game/LineBoss/Candidates/PressShop/PR009/v089/InterfaceCollision"
ASSET_PATH = f"{DEST}/SM_CA_MW_PR008_PR009_TransferGuides_01_v089"
OUT = ROOT / "Saved/Audits/PR009_InMap_v089/transfer_guide_collision_build.json"

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def counts(mesh):
    aggregate = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
    row = {
        "box": len(aggregate.get_editor_property("box_elems")),
        "sphere": len(aggregate.get_editor_property("sphere_elems")),
        "capsule": len(aggregate.get_editor_property("sphyl_elems")),
        "convex": len(aggregate.get_editor_property("convex_elems")),
    }
    row["total"] = sum(row.values())
    return row


def apply_open_channel_collision(mesh):
    # Source geometry has GuideRail centres at local X +/-1.12 m and WearStrip
    # centres at +/-1.1032 m.  One box per side covers each rail+strip union while
    # preserving the 2.1814 m clear channel between inner collision faces.
    specs = [
        {"name": "TransferGuide_Left", "center_cm": [-111.785, 0.0, 0.0], "dimensions_cm": [5.43, 222.0, 13.0]},
        {"name": "TransferGuide_Right", "center_cm": [111.785, 0.0, 0.0], "dimensions_cm": [5.43, 222.0, 13.0]},
    ]
    aggregate = unreal.KAggregateGeom()
    boxes = []
    for spec in specs:
        box = unreal.KBoxElem()
        box.set_editor_property("center", unreal.Vector(*spec["center_cm"]))
        box.set_editor_property("rotation", unreal.Rotator())
        box.set_editor_property("x", spec["dimensions_cm"][0])
        box.set_editor_property("y", spec["dimensions_cm"][1])
        box.set_editor_property("z", spec["dimensions_cm"][2])
        boxes.append(box)
    body = mesh.get_editor_property("body_setup")
    aggregate.set_editor_property("box_elems", boxes)
    body.set_editor_property("agg_geom", aggregate)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    body.modify()
    mesh.modify()
    lib.save_loaded_asset(mesh, only_if_is_dirty=False)
    persisted = counts(mesh)
    if persisted != {"box": 2, "sphere": 0, "capsule": 0, "convex": 0, "total": 2}:
        raise RuntimeError(f"Guide collision persistence mismatch: {persisted}")
    return specs, persisted


def main():
    if not lib.does_asset_exist(TARGET_MAP):
        if not lib.duplicate_asset(PARENT_MAP, TARGET_MAP):
            raise RuntimeError(f"Could not duplicate immutable parent {PARENT_MAP}")
        if not lib.save_asset(TARGET_MAP, only_if_is_dirty=False):
            raise RuntimeError(f"Could not save isolated target {TARGET_MAP}")
        unreal.log("PR009_V089_MAP_DUPLICATED__RERUN_FOR_GUIDE_COLLISION_AUTHORING")
        unreal.SystemLibrary.quit_editor()
        return

    if not levels.load_level(TARGET_MAP):
        raise RuntimeError(f"Could not load {TARGET_MAP}")
    actors = list(actors_api.get_all_level_actors())
    guides = [
        actor for actor in actors
        if unreal.Name("LB.Interface.PR008.PR009") in actor.tags
        and "TransferGuides_01" in actor.get_actor_label()
    ]
    if len(guides) != 1:
        raise RuntimeError(f"Expected one supported-transfer guide actor, found {len(guides)}")
    guide_actor = guides[0]
    component = guide_actor.get_component_by_class(unreal.StaticMeshComponent)
    source_mesh = component.get_editor_property("static_mesh")
    source_asset = source_mesh.get_path_name().split(".")[0]
    new_mesh = lib.load_asset(ASSET_PATH)
    if new_mesh is None:
        if not lib.duplicate_asset(source_asset, ASSET_PATH):
            raise RuntimeError(f"Could not duplicate transfer-guide mesh {source_asset}")
        new_mesh = lib.load_asset(ASSET_PATH)
    source_bounds = source_mesh.get_bounding_box()
    source_vertices = source_mesh.get_num_vertices(0)
    source_triangles = source_mesh.get_num_triangles(0)
    materials = [component.get_material(index) for index in range(component.get_num_materials())]
    specs, collision_counts = apply_open_channel_collision(new_mesh)
    component.set_static_mesh(new_mesh)
    for index, material in enumerate(materials):
        if material is not None and index < component.get_num_materials():
            component.set_material(index, material)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_editor_property("can_ever_affect_navigation", True)
    component.set_world_scale3d(unreal.Vector(1.0, 1.0, 1.0))

    for actor in actors_api.get_all_level_actors():
        label = actor.get_actor_label()
        if "V087" in label:
            actor.set_actor_label(label.replace("V087", "V089"))
        actor.tags = [unreal.Name(str(tag).replace("v087", "v089")) for tag in actor.tags]
    guide_actor.set_actor_label("LB_PR009_V089_SM_CA_MW_PR008_PR009_TransferGuides_01")
    guide_actor.tags = list(guide_actor.tags) + [
        unreal.Name("LB.Collision.AuthoredOpenTransferGuides.v089"),
        unreal.Name("LB.Dimension.GuideClearChannel.2181mm"),
    ]

    flows = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
    pr008 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR008Station)]
    pr009 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR009Station)]
    if len(flows) != 1 or len(pr008) != 1 or len(pr009) != 1:
        raise RuntimeError(f"Authority cardinality changed: flow={len(flows)} PR008={len(pr008)} PR009={len(pr009)}")
    flows[0].bind_blank_stations(pr008[0], pr009[0])

    new_bounds = new_mesh.get_bounding_box()
    visual_identity = {
        "vertices_match": source_vertices == new_mesh.get_num_vertices(0),
        "triangles_match": source_triangles == new_mesh.get_num_triangles(0),
        "bounds_match": all(abs(a-b) <= 0.01 for a,b in zip(
            [source_bounds.min.x, source_bounds.min.y, source_bounds.min.z, source_bounds.max.x, source_bounds.max.y, source_bounds.max.z],
            [new_bounds.min.x, new_bounds.min.y, new_bounds.min.z, new_bounds.max.x, new_bounds.max.y, new_bounds.max.z],
        )),
        "component_materials": [material.get_path_name() if material else None for material in materials],
    }
    if not all(visual_identity[key] for key in ("vertices_match", "triangles_match", "bounds_match")):
        raise RuntimeError(f"Guide visual geometry changed unexpectedly: {visual_identity}")
    transform = guide_actor.get_actor_transform()
    if any(abs(value - 1.0) > 0.0001 for value in (transform.scale3d.x, transform.scale3d.y, transform.scale3d.z)):
        raise RuntimeError(f"Guide actor scale is not identity: {transform.scale3d}")
    if not levels.save_current_level():
        raise RuntimeError(f"Could not save {TARGET_MAP}")
    lib.save_directory(DEST, only_if_is_dirty=False, recursive=True)

    payload = {
        "$schema": "cairnwell/audit/pr009-transfer-guide-collision-build-v089/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "V089_AUTHORED_OPEN_TRANSFER_GUIDE_COLLISION__FULL_RUNTIME_SWEEP_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
        "parent_map": PARENT_MAP,
        "target_map": TARGET_MAP,
        "source_asset": source_mesh.get_path_name(),
        "release_candidate_asset": new_mesh.get_path_name(),
        "actor": guide_actor.get_actor_label(),
        "actor_scale": [transform.scale3d.x, transform.scale3d.y, transform.scale3d.z],
        "authored_collision_primitives": specs,
        "collision_counts": collision_counts,
        "clear_channel_mm": 2181.4,
        "pro_max_blank_mm_flow_by_across": [2600, 1800],
        "across_side_clearance_mm": 190.7,
        "visual_identity": visual_identity,
        "visual_geometry_changed": False,
        "parent_v087_modified": False,
        "experimental_v088_used_as_parent": False,
        "pr010_started": False,
        "robots_modified": False,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"PR009_V089_TRANSFER_GUIDE_COLLISION_BUILD_PASS output={OUT}")
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
