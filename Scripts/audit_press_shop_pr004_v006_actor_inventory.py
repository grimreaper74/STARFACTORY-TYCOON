"""Fresh read-only actor/component inventory of the accepted PR-004 v006 map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
OUTPUT = (
    Path(unreal.Paths.project_saved_dir())
    / "Audits/press_shop_pr004_v006_actor_inventory_fresh.json"
)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load accepted baseline {MAP}")

rows = []
for actor in sorted(actors.get_all_level_actors(), key=lambda item: item.get_actor_label()):
    transform = actor.get_actor_transform()
    static_components = actor.get_components_by_class(unreal.StaticMeshComponent)
    mesh_paths = []
    material_paths = []
    simple_collision_components = 0
    for component in static_components:
        mesh = component.get_editor_property("static_mesh")
        if mesh is not None:
            mesh_paths.append(mesh.get_path_name())
            body_setup = mesh.get_editor_property("body_setup")
            if body_setup is not None:
                aggregate = body_setup.get_editor_property("agg_geom")
                count = sum(
                    len(aggregate.get_editor_property(field))
                    for field in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems")
                )
                if count > 0:
                    simple_collision_components += 1
        for index in range(component.get_num_materials()):
            material = component.get_material(index)
            if material is not None:
                material_paths.append(material.get_path_name())
    rows.append(
        {
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_path_name(),
            "tags": [str(tag) for tag in actor.tags],
            "location_cm": [transform.translation.x, transform.translation.y, transform.translation.z],
            "rotation_quat": [transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w],
            "scale": [transform.scale3d.x, transform.scale3d.y, transform.scale3d.z],
            "static_mesh_component_count": len(static_components),
            "simple_collision_component_count": simple_collision_components,
            "mesh_assets": sorted(set(mesh_paths)),
            "materials": sorted(set(material_paths)),
        }
    )

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-v006-actor-inventory/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "read_only": True,
    "actor_count": len(rows),
    "static_mesh_component_count": sum(row["static_mesh_component_count"] for row in rows),
    "simple_collision_component_count": sum(row["simple_collision_component_count"] for row in rows),
    "actors": rows,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR004_V006_ACTOR_INVENTORY_PASS actors={len(rows)} output={OUTPUT}"
)
unreal.SystemLibrary.quit_editor()
