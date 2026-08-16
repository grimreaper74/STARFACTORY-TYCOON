"""Build immutable, runtime-oriented shutter FBXs from the frozen v001 Blender candidate.

Run with Blender 5.2 in background/factory-startup mode.  The frozen
FactoryEnvelopeKit_v001 tree is read-only input.  All output is written to a
separate UnrealDerived namespace and an existing mismatched output is never
overwritten.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


PROJECT = Path(__file__).resolve().parent.parent
FROZEN_ROOT = PROJECT / "SourceAssets/Candidate/Architecture/FactoryEnvelopeKit_v001"
FROZEN_AUDIT = FROZEN_ROOT / "Audits/LB_ShutterBay_ProductionPrep_v001.json"
FROZEN_BLEND = FROZEN_ROOT / "Derived/ShutterProductionPrep/LB_Architecture_ShutterBay_ProductionPrep_v001.blend"
FROZEN_MASTER_FBX = FROZEN_ROOT / "Derived/ShutterProductionPrep/Exports/LB_ShutterBay_ProductionPrep_v001.fbx"
FROZEN_LOD1_FBX = FROZEN_ROOT / "Derived/ShutterProductionPrep/Exports/LB_ShutterLeaf_LOD1_v001.fbx"
FROZEN_LOD2_FBX = FROZEN_ROOT / "Derived/ShutterProductionPrep/Exports/LB_ShutterLeaf_LOD2_v001.fbx"
FROZEN_README = FROZEN_ROOT / "README.md"
FROZEN_MANIFEST = FROZEN_ROOT / "Audits/FactoryEnvelopeKit_manifest_v001.json"
FROZEN_LEDGER = FROZEN_ROOT / "Audits/SHA256SUMS_v001.txt"

OUTPUT_ROOT = PROJECT / "SourceAssets/UnrealDerived/Architecture/FactoryEnvelopeKitRuntime_v001"
OUTPUT_MANIFEST_NAME = "FactoryEnvelopeKitRuntime_v001_manifest.json"

EXPECTED_SOURCE_HASHES = {
    FROZEN_BLEND: "fceb069f91c3cdc7851e596a4d8ce0ad3eb576da9956340b49995a6bcb4e4d6b",
    FROZEN_MASTER_FBX: "05c669b3e771d30e7bbb8cf4961c5e7a1da6a9146c0d126d0bdd16f0ff114ceb",
    FROZEN_LOD1_FBX: "9b036244983e678ce48a22607cf6d7688ef7e73b49ea4af1b60fc032e2a0ba0b",
    FROZEN_LOD2_FBX: "06ec711751945c59c972b0d1d3e6de38405c20f5027ee6edf718ffe2af15f2e4",
}

SOURCE_OBJECTS = {
    "static_wall": "SM_LB_ShutterBay_StaticWall_LOD0_v001",
    "frame": "SM_LB_ShutterBay_Frame_LOD0_v001",
    "leaf_lod0": "SM_LB_ShutterLeaf_LOD0_v001",
    "leaf_lod1": "SM_LB_ShutterLeaf_LOD1_v001",
    "leaf_lod2": "SM_LB_ShutterLeaf_LOD2_v001",
}

SOURCE_ROOTS = {
    "static": "ROOT_LB_ShutterBay_Static_v001",
    "leaf_lod0": "ROOT_LB_ShutterLeaf_v001",
    "leaf_lod1": "ROOT_LB_ShutterLeaf_LOD1_v001",
    "leaf_lod2": "ROOT_LB_ShutterLeaf_LOD2_v001",
}

RUNTIME_MESHES = {
    "static_wall": "SM_LB_ShutterBay_StaticWall_v001",
    "frame": "SM_LB_ShutterBay_Frame_v001",
    "leaf": "SM_LB_ShutterLeaf_v001",
}

EXPECTED_TRIANGLES = {
    "static_wall": 972,
    "frame": 432,
    "leaf_lod0": 3564,
    "leaf_lod1": 1836,
    "leaf_lod2": 972,
}

EXPECTED_MATERIAL_SLOTS = {
    "static_wall": [
        "M_LB_Architecture_WarmOffWhite_v001",
        "M_LB_Architecture_Graphite_v001",
        "M_LB_Architecture_SafetyYellow_v001",
    ],
    "frame": [
        "M_LB_Architecture_Graphite_v001",
        "M_LB_Shutter_NeutralSilver_v001",
    ],
    "leaf_lod0": ["M_LB_Shutter_NeutralSilver_v001"],
    "leaf_lod1": ["M_LB_Shutter_NeutralSilver_v001"],
    "leaf_lod2": ["M_LB_Shutter_NeutralSilver_v001"],
}

# Boxes are expressed in frozen Blender metres.  The UE FBX importer performs
# the established Blender +Y -> Unreal -Y conversion.
WALL_COLLISION = [
    {"name": "WallLeft", "center_m": [-3.575, 0.0, 3.0], "dimensions_m": [0.85, 0.24, 6.0]},
    {"name": "WallRight", "center_m": [2.60, 0.0, 3.0], "dimensions_m": [2.80, 0.24, 6.0]},
    {"name": "WallHeader", "center_m": [-0.975, 0.0, 5.30], "dimensions_m": [4.35, 0.24, 1.40]},
    {"name": "GuardLeft", "center_m": [-3.92, -0.24, 0.42], "dimensions_m": [0.24, 0.20, 0.84]},
    {"name": "GuardRight", "center_m": [3.92, -0.24, 0.42], "dimensions_m": [0.24, 0.20, 0.84]},
]

FRAME_COLLISION = [
    {"name": "JambLeft", "center_m": [-3.24, -0.145, 2.30], "dimensions_m": [0.18, 0.14, 4.82]},
    {"name": "JambRight", "center_m": [1.29, -0.145, 2.30], "dimensions_m": [0.18, 0.14, 4.82]},
    {"name": "Header", "center_m": [-0.975, -0.145, 4.71], "dimensions_m": [4.71, 0.18, 0.34]},
    {"name": "Threshold", "center_m": [-0.975, -0.155, 0.045], "dimensions_m": [4.47, 0.18, 0.09]},
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(f"FACTORY_ENVELOPE_SHUTTER_PREP_V001_FAIL: {message}")


def verify_frozen_inputs() -> dict[str, str]:
    required = [
        FROZEN_AUDIT,
        FROZEN_README,
        FROZEN_MANIFEST,
        FROZEN_LEDGER,
        *EXPECTED_SOURCE_HASHES.keys(),
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        fail(f"missing frozen input(s): {missing}")

    measured = {str(path): sha256(path) for path in required}
    for path, expected in EXPECTED_SOURCE_HASHES.items():
        if measured[str(path)].lower() != expected:
            fail(f"frozen hash mismatch for {path}: {measured[str(path)]} != {expected}")

    audit = json.loads(FROZEN_AUDIT.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS__SHUTTER_PRODUCTION_PREP_V001":
        fail(f"frozen production-prep audit is not approved: {audit.get('status')}")
    if audit.get("visual_gate") != "PASS__closed_half_open_open inspected; straight slats/frame, continuous plinth, zero slats visible above header":
        fail("frozen closed/half/open visual gate is not the approved v001 gate")
    if audit.get("derived_blend_sha256", "").lower() != EXPECTED_SOURCE_HASHES[FROZEN_BLEND]:
        fail("frozen audit blend hash does not match the locked contract")
    return measured


def validate_existing_output() -> bool:
    if not OUTPUT_ROOT.exists():
        return False
    manifest_path = OUTPUT_ROOT / OUTPUT_MANIFEST_NAME
    if not manifest_path.is_file():
        fail(f"partial UnrealDerived output exists without manifest: {OUTPUT_ROOT}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("status") != "PASS__FROZEN_SHUTTER_RUNTIME_FBXS_WITH_AUTHORED_SIMPLE_COLLISION_V001":
        fail(f"existing output is not the approved v001 payload: {payload.get('status')}")
    expected_files = {OUTPUT_MANIFEST_NAME}
    for row in payload.get("exports", {}).values():
        relative = row.get("relative_path")
        if not relative:
            fail("existing output manifest contains an export without relative_path")
        expected_files.add(relative)
        path = OUTPUT_ROOT / relative
        if not path.is_file() or sha256(path) != row.get("sha256"):
            fail(f"existing output hash mismatch: {path}")
    actual_files = {
        str(path.relative_to(OUTPUT_ROOT)).replace("\\", "/")
        for path in OUTPUT_ROOT.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_files:
        fail(f"existing output inventory mismatch: expected={sorted(expected_files)} actual={sorted(actual_files)}")
    print(json.dumps({"status": "PASS__IDEMPOTENT_NOOP", "output": str(OUTPUT_ROOT)}, indent=2))
    return True


def triangle_count(obj: bpy.types.Object) -> int:
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def local_bounds(obj: bpy.types.Object) -> tuple[list[float], list[float], list[float]]:
    points = [Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[index] for point in points) for index in range(3)]
    maximum = [max(point[index] for point in points) for index in range(3)]
    dimensions = [maximum[index] - minimum[index] for index in range(3)]
    return (
        [round(value, 6) for value in minimum],
        [round(value, 6) for value in maximum],
        [round(value, 6) for value in dimensions],
    )


def material_slots(obj: bpy.types.Object) -> list[str]:
    return [slot.material.name if slot.material else "" for slot in obj.material_slots]


def clone_flattened(
    source: bpy.types.Object,
    runtime_name: str,
    pivot_world_m: tuple[float, float, float],
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    mesh = source.data.copy()
    transform = Matrix.Translation(-Vector(pivot_world_m)) @ source.matrix_world
    mesh.transform(transform)
    mesh.update()
    result = bpy.data.objects.new(runtime_name, mesh)
    collection.objects.link(result)
    result.matrix_world = Matrix.Identity(4)
    return result


def cube_mesh(name: str, center: list[float], dimensions: list[float]) -> bpy.types.Mesh:
    cx, cy, cz = center
    hx, hy, hz = (value * 0.5 for value in dimensions)
    vertices = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh


def make_collision_objects(
    visual_name: str,
    boxes: list[dict],
    pivot_world_m: tuple[float, float, float],
    collection: bpy.types.Collection,
) -> list[bpy.types.Object]:
    objects = []
    pivot = Vector(pivot_world_m)
    for index, row in enumerate(boxes):
        center = list(Vector(row["center_m"]) - pivot)
        name = f"UCX_{visual_name}_{index:02d}"
        obj = bpy.data.objects.new(name, cube_mesh(name, center, row["dimensions_m"]))
        collection.objects.link(obj)
        obj.matrix_world = Matrix.Identity(4)
        objects.append(obj)
    return objects


def export_fbx(path: Path, visual: bpy.types.Object, collision: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in [visual, *collision]:
        obj.hide_set(False)
        obj.hide_render = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = visual
    path.parent.mkdir(parents=True, exist_ok=True)
    result = bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        object_types={"MESH"},
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        bake_anim=False,
        use_custom_props=False,
    )
    if "FINISHED" not in result or not path.is_file() or path.stat().st_size == 0:
        fail(f"FBX export failed: {path} result={result}")
    payload = path.read_bytes()
    if collision and b"UCX_" not in payload:
        fail(f"FBX lost authored UCX names: {path}")


def remove_generated(objects: list[bpy.types.Object]) -> None:
    for obj in objects:
        mesh = obj.data if obj.type == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def build_export(
    staging: Path,
    key: str,
    source_name: str,
    runtime_name: str,
    pivot_world_m: tuple[float, float, float],
    collision_boxes: list[dict],
    filename: str,
) -> dict:
    source = bpy.data.objects.get(source_name)
    if source is None or source.type != "MESH":
        fail(f"approved source object missing: {source_name}")
    if triangle_count(source) != EXPECTED_TRIANGLES[key]:
        fail(f"source triangle drift for {source_name}: {triangle_count(source)}")
    slots = material_slots(source)
    if slots != EXPECTED_MATERIAL_SLOTS[key]:
        fail(f"source material-slot drift for {source_name}: {slots}")

    collection = bpy.data.collections.new(f"LB_RuntimeExport_{key}_{uuid.uuid4().hex[:8]}")
    bpy.context.scene.collection.children.link(collection)
    visual = clone_flattened(source, runtime_name, pivot_world_m, collection)
    collision = make_collision_objects(runtime_name, collision_boxes, pivot_world_m, collection)
    minimum, maximum, dimensions = local_bounds(visual)
    relative = f"Exports/{filename}"
    path = staging / relative
    export_fbx(path, visual, collision)
    row = {
        "relative_path": relative,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "source_object": source_name,
        "runtime_mesh_name": runtime_name,
        "pivot_world_m": [round(value, 6) for value in pivot_world_m],
        "local_bounds_m": {"min": minimum, "max": maximum, "dimensions": dimensions},
        "triangles": triangle_count(visual),
        "material_slots": material_slots(visual),
        "collision_boxes": collision_boxes,
        "collision_count": len(collision_boxes),
    }
    remove_generated([visual, *collision])
    bpy.data.collections.remove(collection)
    return row


def main() -> None:
    frozen_hashes_before = verify_frozen_inputs()
    if validate_existing_output():
        return

    if OUTPUT_ROOT.parent.exists() and not OUTPUT_ROOT.parent.is_dir():
        fail(f"output parent is not a directory: {OUTPUT_ROOT.parent}")
    OUTPUT_ROOT.parent.mkdir(parents=True, exist_ok=True)
    staging = OUTPUT_ROOT.parent / f".{OUTPUT_ROOT.name}.staging_{uuid.uuid4().hex}"
    if staging.exists():
        fail(f"unexpected staging collision: {staging}")
    staging.mkdir(parents=False)

    try:
        bpy.ops.wm.open_mainfile(filepath=str(FROZEN_BLEND), load_ui=False)
        if Path(bpy.data.filepath).resolve() != FROZEN_BLEND.resolve():
            fail(f"Blender opened the wrong source: {bpy.data.filepath}")

        required_objects = set(SOURCE_OBJECTS.values()) | set(SOURCE_ROOTS.values())
        missing = sorted(name for name in required_objects if bpy.data.objects.get(name) is None)
        if missing:
            fail(f"approved source hierarchy missing: {missing}")

        static_pivot = tuple(bpy.data.objects[SOURCE_ROOTS["static"]].matrix_world.translation)
        leaf_pivots = {
            "leaf_lod0": tuple(bpy.data.objects[SOURCE_ROOTS["leaf_lod0"]].matrix_world.translation),
            "leaf_lod1": tuple(bpy.data.objects[SOURCE_ROOTS["leaf_lod1"]].matrix_world.translation),
            "leaf_lod2": tuple(bpy.data.objects[SOURCE_ROOTS["leaf_lod2"]].matrix_world.translation),
        }
        expected_pivot = (-0.975, 0.145, 4.60)
        if max(abs(leaf_pivots["leaf_lod0"][i] - expected_pivot[i]) for i in range(3)) > 1e-5:
            fail(f"leaf pivot drift: {leaf_pivots['leaf_lod0']}")
        if max(abs(static_pivot[i]) for i in range(3)) > 1e-6:
            fail(f"static root drift: {static_pivot}")

        exports = {
            "static_wall": build_export(
                staging, "static_wall", SOURCE_OBJECTS["static_wall"], RUNTIME_MESHES["static_wall"],
                static_pivot, WALL_COLLISION, f"{RUNTIME_MESHES['static_wall']}.fbx",
            ),
            "frame": build_export(
                staging, "frame", SOURCE_OBJECTS["frame"], RUNTIME_MESHES["frame"],
                static_pivot, FRAME_COLLISION, f"{RUNTIME_MESHES['frame']}.fbx",
            ),
            "leaf_lod0": build_export(
                staging, "leaf_lod0", SOURCE_OBJECTS["leaf_lod0"], RUNTIME_MESHES["leaf"],
                leaf_pivots["leaf_lod0"], [], f"{RUNTIME_MESHES['leaf']}_LOD0.fbx",
            ),
            "leaf_lod1": build_export(
                staging, "leaf_lod1", SOURCE_OBJECTS["leaf_lod1"], RUNTIME_MESHES["leaf"],
                leaf_pivots["leaf_lod1"], [], f"{RUNTIME_MESHES['leaf']}_LOD1.fbx",
            ),
            "leaf_lod2": build_export(
                staging, "leaf_lod2", SOURCE_OBJECTS["leaf_lod2"], RUNTIME_MESHES["leaf"],
                leaf_pivots["leaf_lod2"], [], f"{RUNTIME_MESHES['leaf']}_LOD2.fbx",
            ),
        }

        frozen_hashes_after = verify_frozen_inputs()
        if frozen_hashes_before != frozen_hashes_after:
            fail("frozen SourceAssets changed while runtime FBXs were prepared")

        non_shutter_exports = [
            str(path.relative_to(FROZEN_ROOT)).replace("\\", "/")
            for path in FROZEN_ROOT.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".fbx", ".glb"}
            and "Derived/ShutterProductionPrep/Exports" not in str(path.relative_to(FROZEN_ROOT)).replace("\\", "/")
        ]
        if non_shutter_exports:
            fail(f"unexpected clean exports appeared for held architecture modules: {non_shutter_exports}")

        payload = {
            "$schema": "cairnwell/source/architecture/factory-envelope-kit-runtime-v001/v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS__FROZEN_SHUTTER_RUNTIME_FBXS_WITH_AUTHORED_SIMPLE_COLLISION_V001",
            "source_frozen_root": str(FROZEN_ROOT),
            "source_hashes_before": frozen_hashes_before,
            "source_hashes_after": frozen_hashes_after,
            "preparation_script": str(Path(__file__).resolve()),
            "preparation_script_sha256": sha256(Path(__file__).resolve()),
            "scale_contract": {
                "unreal_units_per_metre": 100.0,
                "module_m": [8.0, 0.24, 6.0],
                "physical_bounds_m": [8.08, 0.46, 6.0],
                "plinth_top_m": 1.50,
                "opening_m": [4.35, 4.60],
            },
            "motion_contract": {
                "leaf_pivot_world_m": [-0.975, 0.145, 4.60],
                "unreal_leaf_component_location_cm_after_handedness": [-97.5, -14.5, 460.0],
                "axis": "+Z",
                "travel_cm": 460.0,
                "states_cm": {"closed": 0.0, "half_open": 230.0, "open": 460.0},
            },
            "material_contract": {
                "M_LB_Architecture_WarmOffWhite_v001": {"srgb_hex": "#E8E4DB", "metallic": 0.0, "roughness": 0.72},
                "M_LB_Architecture_Graphite_v001": {"srgb_hex": "#30363B", "metallic": 0.18, "roughness": 0.50},
                "M_LB_Shutter_NeutralSilver_v001": {"srgb_hex": "#C9CED1", "metallic": 0.58, "roughness": 0.34},
                "M_LB_Architecture_SafetyYellow_v001": {"srgb_hex": "#F0B91D", "metallic": 0.05, "roughness": 0.44},
            },
            "exports": exports,
            "held_modules": {
                "postless_infill": "HOLD__approval Blender study only; no clean runtime FBX/GLB export in frozen v001",
                "warehouse_double_door": "HOLD__approximately two-million-triangle approval mesh; no clean runtime export in frozen v001",
                "loading_bay": "HOLD__approximately two-million-triangle approval mesh; no clean runtime export in frozen v001",
            },
            "source_assets_mutated": False,
            "runtime_binding_authorized": False,
            "map_binding_authorized": False,
        }
        (staging / OUTPUT_MANIFEST_NAME).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(staging, OUTPUT_ROOT)
        print(json.dumps({"status": payload["status"], "output": str(OUTPUT_ROOT), "exports": exports}, indent=2))
    except Exception:
        if staging.exists():
            resolved = staging.resolve()
            if resolved.parent == OUTPUT_ROOT.parent.resolve() and resolved.name.startswith(f".{OUTPUT_ROOT.name}.staging_"):
                shutil.rmtree(resolved)
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise
