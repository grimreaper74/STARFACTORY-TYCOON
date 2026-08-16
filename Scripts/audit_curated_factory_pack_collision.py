"""Read-only collision audit for the curated Factory Environment meshes."""

import json
from pathlib import Path

import unreal


ROOT = "/Game/LineBoss/Vendor/FactoryEnvironment"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "Audits/factory_pack_collision_v001.json"
MESHES = [
    f"{ROOT}/Meshes/SM_Cables01",
    f"{ROOT}/Meshes/SM_CableSet_01",
    f"{ROOT}/Meshes/SM_ElectricalCable_01",
    f"{ROOT}/Meshes/Crane/SM_ElectricMotor01",
    f"{ROOT}/Meshes/SM_Pipe_round_long",
    f"{ROOT}/Meshes/SM_Pipe_round_corner1",
    f"{ROOT}/Meshes/SM_Pipe_round_tee_transition1",
    f"{ROOT}/Meshes/SM_Pipe_round_fixator",
    f"{ROOT}/Meshes/SM_Fence_01",
    f"{ROOT}/Meshes/SM_FencePart_01",
    f"{ROOT}/Meshes/SM_IndustrialPlatform01",
    f"{ROOT}/Meshes/SM_PlatformRailing_01",
    f"{ROOT}/Meshes/SM_MetalBeam01",
    f"{ROOT}/Meshes/SM_Column_02",
    f"{ROOT}/Meshes/SM_Lamp01",
]

records = []
errors = []
for path in MESHES:
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        errors.append(f"missing {path}")
        continue
    simple = unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)
    convex = unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh)
    trace_flag = "UNKNOWN"
    primitive_shapes = {}
    try:
        body = mesh.get_editor_property("body_setup")
        trace_flag = str(body.get_editor_property("collision_trace_flag"))
        aggregate = body.get_editor_property("agg_geom")
        for name in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems", "tapered_capsule_elems"):
            try:
                primitive_shapes[name] = len(aggregate.get_editor_property(name))
            except Exception:
                primitive_shapes[name] = None
    except Exception as exc:
        primitive_shapes["inspection_error"] = str(exc)
    records.append({
        "asset": path,
        "simple_collision_api": simple,
        "convex_collision_api": convex,
        "collision_trace_flag": trace_flag,
        "primitive_shapes": primitive_shapes,
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({"errors": errors, "assets": records}, indent=2), encoding="utf-8")
if errors:
    raise RuntimeError("LINE_BOSS_FACTORY_PACK_COLLISION_FAIL " + "; ".join(errors))
unreal.log(f"LINE_BOSS_FACTORY_PACK_COLLISION_AUDIT_PASS assets={len(records)} output={OUTPUT}")
