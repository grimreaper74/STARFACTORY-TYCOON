"""Record the Unreal 5.8 static-mesh collision Python API available to Line Boss."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUTPUT = REPO / "Saved/Audits/unreal_5_8_static_mesh_collision_api.json"
TEST_MESH = (
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v002/PoweredCradle_v001/"
    "SM_LB_PR004_PoweredCradle_Static_v001"
)


def public_names(value):
    return sorted(name for name in dir(value) if not name.startswith("_") and "collision" in name.lower())


subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
mesh = unreal.load_asset(TEST_MESH)

result = {
    "$schema": "line-boss/audit/unreal-static-mesh-collision-api/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "engine_version": str(unreal.SystemLibrary.get_engine_version()),
    "subsystem_type": str(type(subsystem)),
    "subsystem_collision_methods": public_names(subsystem),
    "subsystem_class_collision_methods": public_names(unreal.StaticMeshEditorSubsystem),
    "deprecated_library_collision_methods": public_names(unreal.EditorStaticMeshLibrary),
    "enum_values": [str(value) for value in unreal.ScriptingCollisionShapeType],
    "test_mesh": TEST_MESH,
    "test_mesh_loaded": isinstance(mesh, unreal.StaticMesh),
}

if isinstance(mesh, unreal.StaticMesh):
    for owner_name, owner in (
        ("subsystem", subsystem),
        ("deprecated_library", unreal.EditorStaticMeshLibrary),
    ):
        method = getattr(owner, "get_simple_collision_count", None)
        try:
            result[f"{owner_name}_simple_collision_count"] = method(mesh) if method else None
        except Exception as exc:  # Unreal Python exception details are evidence for routing.
            result[f"{owner_name}_simple_collision_error"] = repr(exc)

    body_setup = mesh.get_editor_property("body_setup")
    result["body_setup_exists"] = body_setup is not None
    if body_setup is not None:
        result["body_setup_public_collision_names"] = public_names(body_setup)
        try:
            aggregate = body_setup.get_editor_property("agg_geom")
            result["aggregate_geometry_type"] = str(type(aggregate))
            result["aggregate_geometry_public_names"] = sorted(
                name for name in dir(aggregate) if not name.startswith("_")
            )
            result["aggregate_counts_before"] = {
                name: len(aggregate.get_editor_property(name))
                for name in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems")
            }
        except Exception as exc:
            result["aggregate_geometry_error"] = repr(exc)

    try:
        result["fallback_add_result"] = unreal.EditorStaticMeshLibrary.add_simple_collisions_with_notification(
            mesh,
            unreal.ScriptingCollisionShapeType.BOX,
            False,
        )
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        result["fallback_count_after"] = unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)
        body_setup = mesh.get_editor_property("body_setup")
        aggregate = body_setup.get_editor_property("agg_geom")
        result["aggregate_counts_after"] = {
            name: len(aggregate.get_editor_property(name))
            for name in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems")
        }
    except Exception as exc:
        result["fallback_add_error"] = repr(exc)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_COLLISION_API_AUDIT {OUTPUT}")
