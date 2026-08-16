"""Read-only UE 5.8 collision diagnosis for the failed spray-booth v002 import."""

from __future__ import annotations

import json

import unreal


ASSET = (
    "/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002/"
    "SM_LB_PaintSprayBooth_Runtime_v002.SM_LB_PaintSprayBooth_Runtime_v002"
)


mesh = unreal.EditorAssetLibrary.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Failed to load partial diagnostic mesh: {ASSET}")

subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
if subsystem is None:
    raise RuntimeError("StaticMeshEditorSubsystem is unavailable")

payload = {
    "asset": mesh.get_path_name(),
    "simple_collision_count": int(subsystem.get_simple_collision_count(mesh)),
    "lod_count": int(mesh.get_num_lods()),
    "triangles": [int(mesh.get_num_triangles(i)) for i in range(mesh.get_num_lods())],
}

body_setup = mesh.get_editor_property("body_setup")
payload["body_setup"] = body_setup.get_path_name() if body_setup else None
if body_setup:
    aggregate = body_setup.get_editor_property("agg_geom")
    for field in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems", "tapered_capsule_elems"):
        try:
            payload[field] = len(aggregate.get_editor_property(field))
        except Exception as error:
            payload[field] = f"unavailable: {error}"
    try:
        payload["convex_contract"] = []
        for convex in aggregate.get_editor_property("convex_elems"):
            row = {}
            for field in ("vertex_data", "elem_box", "transform"):
                try:
                    value = convex.get_editor_property(field)
                    if field == "vertex_data":
                        row[field] = [
                            [round(float(vertex.x), 4), round(float(vertex.y), 4),
                             round(float(vertex.z), 4)]
                            for vertex in value
                        ]
                    else:
                        row[field] = str(value)
                except Exception as error:
                    row[field] = f"unavailable: {error}"
            payload["convex_contract"].append(row)
    except Exception as error:
        payload["convex_contract"] = f"unavailable: {error}"

unreal.log("LINE_BOSS_SPRAY_BOOTH_V002_COLLISION_DIAGNOSTIC " + json.dumps(payload, sort_keys=True))
