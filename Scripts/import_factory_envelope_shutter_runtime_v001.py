"""Guarded, idempotent Unreal intake for FactoryEnvelopeKitRuntime_v001.

This script creates assets only in a fresh architecture candidate namespace.
It never overwrites or repairs a partial namespace, and it does not create or
modify maps, actors, runtime bindings, C++, configuration, or frozen sources.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(__file__).resolve().parent.parent
UPROJECT = PROJECT / "LineBossCarFactory.uproject"
if not UPROJECT.is_file():
    raise RuntimeError(f"FACTORY_ENVELOPE_SHUTTER_UNREAL_IMPORT_V001_FAIL: exact project descriptor missing: {UPROJECT}")
SOURCE_ROOT = PROJECT / "SourceAssets/UnrealDerived/Architecture/FactoryEnvelopeKitRuntime_v001"
SOURCE_MANIFEST = SOURCE_ROOT / "FactoryEnvelopeKitRuntime_v001_manifest.json"
DEST = "/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001"
DEST_MATERIALS = f"{DEST}/Materials"
DEST_MESHES = f"{DEST}/Meshes/Shutter"
DEST_DISK = PROJECT / "Content/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001"
AUDIT_DIR = PROJECT / "Saved/Audits/Architecture/FactoryEnvelopeKitRuntime_v001"
RECEIPT = AUDIT_DIR / "import_receipt_v001.json"

MASTER_NAME = "M_LB_Architecture_Surface_Master_v001"
MATERIAL_SPECS = {
    "M_LB_Architecture_WarmOffWhite_v001": {
        "instance": "MI_LB_Architecture_WarmOffWhite_v001",
        "srgb_hex": "#E8E4DB",
        "metallic": 0.0,
        "roughness": 0.72,
    },
    "M_LB_Architecture_Graphite_v001": {
        "instance": "MI_LB_Architecture_Graphite_v001",
        "srgb_hex": "#30363B",
        "metallic": 0.18,
        "roughness": 0.50,
    },
    "M_LB_Shutter_NeutralSilver_v001": {
        "instance": "MI_LB_Shutter_NeutralSilver_v001",
        "srgb_hex": "#C9CED1",
        "metallic": 0.58,
        "roughness": 0.34,
    },
    "M_LB_Architecture_SafetyYellow_v001": {
        "instance": "MI_LB_Architecture_SafetyYellow_v001",
        "srgb_hex": "#F0B91D",
        "metallic": 0.05,
        "roughness": 0.44,
    },
}

MESH_SPECS = {
    "static_wall": {
        "asset": "SM_LB_ShutterBay_StaticWall_v001",
        "source_key": "static_wall",
        "triangles": [972],
        "simple_primitive_collision": 0,
        "convex_collision": 5,
        "lightmap_resolution": 128,
    },
    "frame": {
        "asset": "SM_LB_ShutterBay_Frame_v001",
        "source_key": "frame",
        "triangles": [432],
        "simple_primitive_collision": 0,
        "convex_collision": 4,
        "lightmap_resolution": 128,
    },
    "leaf": {
        "asset": "SM_LB_ShutterLeaf_v001",
        "source_key": "leaf_lod0",
        "lod_source_keys": ["leaf_lod1", "leaf_lod2"],
        "triangles": [3564, 1836, 972],
        "simple_primitive_collision": 0,
        "convex_collision": 0,
        "lightmap_resolution": 64,
    },
}

EXPECTED_ASSETS = [
    f"{DEST_MATERIALS}/{MASTER_NAME}",
    *[f"{DEST_MATERIALS}/{row['instance']}" for row in MATERIAL_SPECS.values()],
    *[f"{DEST_MESHES}/{row['asset']}" for row in MESH_SPECS.values()],
]
EXPECTED_PACKAGE_FILES = {
    str(Path(path.replace("/Game/", "")) .with_suffix(".uasset")).replace("\\", "/")
    for path in EXPECTED_ASSETS
}

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(f"FACTORY_ENVELOPE_SHUTTER_UNREAL_IMPORT_V001_FAIL: {message}")


def source_contract() -> tuple[dict, str]:
    if not SOURCE_MANIFEST.is_file():
        fail(f"runtime FBX manifest missing: {SOURCE_MANIFEST}")
    payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if payload.get("status") != "PASS__FROZEN_SHUTTER_RUNTIME_FBXS_WITH_AUTHORED_SIMPLE_COLLISION_V001":
        fail(f"runtime FBX manifest is not approved: {payload.get('status')}")
    if payload.get("source_assets_mutated") is not False:
        fail("runtime FBX manifest does not prove frozen sources remained immutable")
    if payload.get("runtime_binding_authorized") is not False or payload.get("map_binding_authorized") is not False:
        fail("source manifest unexpectedly authorizes map/runtime integration")
    expected_keys = {"static_wall", "frame", "leaf_lod0", "leaf_lod1", "leaf_lod2"}
    if set(payload.get("exports", {})) != expected_keys:
        fail(f"runtime FBX export inventory drift: {sorted(payload.get('exports', {}))}")
    for key, row in payload["exports"].items():
        path = SOURCE_ROOT / row["relative_path"]
        if not path.is_file():
            fail(f"runtime FBX missing for {key}: {path}")
        measured = sha256(path)
        if measured != row.get("sha256"):
            fail(f"runtime FBX hash mismatch for {key}: {measured} != {row.get('sha256')}")
    held = payload.get("held_modules", {})
    if set(held) != {"postless_infill", "warehouse_double_door", "loading_bay"}:
        fail(f"held architecture-module contract drift: {held}")
    return payload, sha256(SOURCE_MANIFEST)


def disk_inventory() -> set[str]:
    if not DEST_DISK.exists():
        return set()
    return {
        "LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/"
        + str(path.relative_to(DEST_DISK)).replace("\\", "/")
        for path in DEST_DISK.rglob("*.uasset")
        if path.is_file()
    }


def package_path(asset_path: str) -> Path:
    return PROJECT / "Content" / Path(asset_path.replace("/Game/", "")).with_suffix(".uasset")


def idempotent_existing(source_manifest_sha: str) -> bool:
    exists = DEST_DISK.exists() or any(library.does_asset_exist(path) for path in EXPECTED_ASSETS)
    if not exists:
        if RECEIPT.exists():
            fail(f"receipt exists while destination namespace is absent: {RECEIPT}")
        return False
    if not RECEIPT.is_file():
        fail(f"partial/unreceipted destination namespace exists: {DEST_DISK}")
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if receipt.get("status") != "PASS__FRESH_GUARDED_SHUTTER_UNREAL_INTAKE_V001":
        fail(f"existing receipt is not an approved PASS: {receipt.get('status')}")
    if receipt.get("source_manifest_sha256") != source_manifest_sha:
        fail("source preparation manifest changed since the received import")
    if set(receipt.get("asset_packages", {})) != set(EXPECTED_ASSETS):
        fail("existing receipt asset inventory does not match the v001 contract")
    if disk_inventory() != EXPECTED_PACKAGE_FILES:
        fail(f"destination package inventory drift: {sorted(disk_inventory())}")
    for asset_path in EXPECTED_ASSETS:
        if not library.does_asset_exist(asset_path):
            fail(f"received asset is missing: {asset_path}")
        path = package_path(asset_path)
        expected_hash = receipt["asset_packages"][asset_path]["sha256"]
        if not path.is_file() or sha256(path) != expected_hash:
            fail(f"received package drift: {path}")
    unreal.log("LINE_BOSS_FACTORY_ENVELOPE_SHUTTER_IMPORT_V001_IDEMPOTENT_NOOP")
    print(json.dumps({"status": "PASS__IDEMPOTENT_NOOP", "destination": DEST}, indent=2))
    return True


def srgb_hex(value: str) -> unreal.LinearColor:
    channels = [int(value[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return unreal.LinearColor(*linear, 1.0)


def expression(material, cls, x: int, y: int):
    return material_editing.create_material_expression(material, cls, x, y)


def create_materials() -> dict[str, unreal.MaterialInterface]:
    master_path = f"{DEST_MATERIALS}/{MASTER_NAME}"
    if library.does_asset_exist(master_path):
        fail(f"freshness violation before material creation: {master_path}")
    master = asset_tools.create_asset(MASTER_NAME, DEST_MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(master, unreal.Material):
        fail("could not create architecture surface material master")
    master.set_editor_properties({
        "two_sided": False,
        "used_with_instanced_static_meshes": True,
    })
    colour = expression(master, unreal.MaterialExpressionVectorParameter, -460, -140)
    colour.set_editor_properties({"parameter_name": "BaseColour", "default_value": srgb_hex("#E8E4DB")})
    roughness = expression(master, unreal.MaterialExpressionScalarParameter, -460, 20)
    roughness.set_editor_properties({"parameter_name": "Roughness", "default_value": 0.72})
    metallic = expression(master, unreal.MaterialExpressionScalarParameter, -460, 160)
    metallic.set_editor_properties({"parameter_name": "Metallic", "default_value": 0.0})
    material_editing.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_editing.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material_editing.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
    material_editing.recompile_material(master)
    library.save_loaded_asset(master, only_if_is_dirty=False)

    instances: dict[str, unreal.MaterialInterface] = {}
    for source_slot, spec in MATERIAL_SPECS.items():
        name = spec["instance"]
        path = f"{DEST_MATERIALS}/{name}"
        if library.does_asset_exist(path):
            fail(f"freshness violation before material-instance creation: {path}")
        instance = asset_tools.create_asset(name, DEST_MATERIALS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if not isinstance(instance, unreal.MaterialInstanceConstant):
            fail(f"could not create {path}")
        instance.set_editor_property("parent", master)
        material_editing.set_material_instance_vector_parameter_value(instance, "BaseColour", srgb_hex(spec["srgb_hex"]))
        material_editing.set_material_instance_scalar_parameter_value(instance, "Roughness", spec["roughness"])
        material_editing.set_material_instance_scalar_parameter_value(instance, "Metallic", spec["metallic"])
        material_editing.update_material_instance(instance)
        library.save_loaded_asset(instance, only_if_is_dirty=False)
        instances[source_slot] = instance
    return instances


def import_static_mesh(source: Path, name: str) -> unreal.StaticMesh:
    asset_path = f"{DEST_MESHES}/{name}"
    if library.does_asset_exist(asset_path):
        fail(f"freshness violation before static-mesh import: {asset_path}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": DEST_MESHES,
        "destination_name": name,
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
        "automated_import_should_detect_type": False,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "one_convex_hull_per_ucx": True,
        "remove_degenerates": True,
        "import_uniform_scale": 1.0,
    })
    task.options = options
    asset_tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = library.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        fail(f"static-mesh import failed: {asset_path}; returned={task.imported_object_paths}")
    return mesh


def expected_ue_bounds(source_row: dict) -> tuple[list[float], list[float]]:
    minimum = source_row["local_bounds_m"]["min"]
    maximum = source_row["local_bounds_m"]["max"]
    return (
        [minimum[0] * 100.0, -maximum[1] * 100.0, minimum[2] * 100.0],
        [maximum[0] * 100.0, -minimum[1] * 100.0, maximum[2] * 100.0],
    )


def vector(value) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def configure_and_measure(
    mesh_key: str,
    mesh: unreal.StaticMesh,
    materials: dict[str, unreal.MaterialInterface],
    source: dict,
    static_mesh_editor,
) -> tuple[dict, list[str]]:
    failures: list[str] = []
    spec = MESH_SPECS[mesh_key]
    if mesh_key == "leaf":
        for lod_index, source_key in enumerate(spec["lod_source_keys"], start=1):
            lod_path = SOURCE_ROOT / source["exports"][source_key]["relative_path"]
            result = static_mesh_editor.import_lod(mesh, lod_index, str(lod_path))
            if result != lod_index:
                failures.append(f"{mesh_key} custom LOD{lod_index} import returned {result}")
        if not static_mesh_editor.set_lod_screen_sizes(mesh, [1.0, 0.45, 0.18]):
            failures.append("leaf manual LOD screen-size assignment failed")

    nanite = static_mesh_editor.get_nanite_settings(mesh)
    nanite.set_editor_property("enabled", False)
    static_mesh_editor.set_nanite_settings(mesh, nanite, True)
    mesh.set_editor_property("light_map_resolution", spec["lightmap_resolution"])
    body = mesh.get_editor_property("body_setup")
    if body is None:
        failures.append(f"{mesh_key} body setup missing")
    else:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)

    slot_rows = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        material = materials.get(slot_name)
        if material is None:
            failures.append(f"{mesh_key} unmapped material slot {index}:{slot_name}")
            continue
        mesh.set_material(index, material)
        slot_rows.append({"index": index, "slot_name": slot_name, "material": material.get_path_name()})

    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

    lod_count = mesh.get_num_lods()
    triangles = [mesh.get_num_triangles(index) for index in range(lod_count)]
    if triangles != spec["triangles"]:
        failures.append(f"{mesh_key} triangle/LOD drift: {triangles} != {spec['triangles']}")
    expected_min, expected_max = expected_ue_bounds(source["exports"][spec["source_key"]])
    box = mesh.get_bounding_box()
    measured_min = vector(box.min)
    measured_max = vector(box.max)
    delta_cm = [
        measured_min[index] - expected_min[index] for index in range(3)
    ] + [
        measured_max[index] - expected_max[index] for index in range(3)
    ]
    if max(abs(value) for value in delta_cm) > 0.25:
        failures.append(f"{mesh_key} scale/pivot/handedness drift cm={delta_cm}")

    simple_primitive_collision = static_mesh_editor.get_simple_collision_count(mesh)
    convex_collision = static_mesh_editor.get_convex_collision_count(mesh)
    if simple_primitive_collision != spec["simple_primitive_collision"]:
        failures.append(
            f"{mesh_key} simple primitive collision count {simple_primitive_collision} "
            f"!= {spec['simple_primitive_collision']}"
        )
    if convex_collision != spec["convex_collision"]:
        failures.append(
            f"{mesh_key} authored UCX convex collision count {convex_collision} "
            f"!= {spec['convex_collision']}"
        )
    collision_flag = str(body.get_editor_property("collision_trace_flag")) if body is not None else None
    if collision_flag is not None and "USE_DEFAULT" not in collision_flag.upper():
        failures.append(f"{mesh_key} collision complexity is not simple/default: {collision_flag}")

    measured = {
        "asset": mesh.get_path_name(),
        "lod_count": lod_count,
        "triangles": triangles,
        "vertices": [mesh.get_num_vertices(index) for index in range(lod_count)],
        "bounds_cm": {
            "min": [round(value, 4) for value in measured_min],
            "max": [round(value, 4) for value in measured_max],
            "dimensions": [round(measured_max[index] - measured_min[index], 4) for index in range(3)],
        },
        "expected_bounds_cm_after_handedness": {
            "min": [round(value, 4) for value in expected_min],
            "max": [round(value, 4) for value in expected_max],
        },
        "bounds_delta_cm": [round(value, 5) for value in delta_cm],
        "material_slots": slot_rows,
        "simple_primitive_collision_count": simple_primitive_collision,
        "convex_collision_count": convex_collision,
        "collision_trace_flag": collision_flag,
        "nanite_enabled": bool(static_mesh_editor.get_nanite_settings(mesh).get_editor_property("enabled")),
        "light_map_resolution": int(mesh.get_editor_property("light_map_resolution")),
        "lod_screen_sizes": [round(float(value), 4) for value in static_mesh_editor.get_lod_screen_sizes(mesh)],
    }
    if measured["nanite_enabled"]:
        failures.append(f"{mesh_key} Nanite unexpectedly enabled")
    return measured, failures


def main() -> None:
    running_project_name = str(unreal.SystemLibrary.get_game_name())
    if running_project_name != "LineBossCarFactory":
        fail(f"running project name mismatch: {running_project_name!r}")
    running_content_dir = Path(unreal.Paths.project_content_dir()).resolve()
    expected_content_dir = (PROJECT / "Content").resolve()
    if running_content_dir != expected_content_dir:
        fail(f"running project content path mismatch: {running_content_dir} != {expected_content_dir}")
    source, source_manifest_sha = source_contract()
    if idempotent_existing(source_manifest_sha):
        return

    static_mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if static_mesh_editor is None:
        fail("StaticMeshEditorSubsystem unavailable; use full UnrealEditor -ExecutePythonScript, not commandlet mode")
    if DEST_DISK.exists():
        fail(f"fresh destination directory unexpectedly exists: {DEST_DISK}")
    if disk_inventory():
        fail(f"fresh destination has unexpected packages: {sorted(disk_inventory())}")

    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")

    materials = create_materials()
    meshes: dict[str, unreal.StaticMesh] = {}
    for key, spec in MESH_SPECS.items():
        export_key = spec["source_key"]
        fbx = SOURCE_ROOT / source["exports"][export_key]["relative_path"]
        meshes[key] = import_static_mesh(fbx, spec["asset"])

    measurements = {}
    failures = []
    for key, mesh in meshes.items():
        row, mesh_failures = configure_and_measure(key, mesh, materials, source, static_mesh_editor)
        measurements[key] = row
        failures.extend(mesh_failures)

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    for asset_path in EXPECTED_ASSETS:
        asset = library.load_asset(asset_path)
        if asset is None:
            failures.append(f"expected asset missing after intake: {asset_path}")
        elif not library.save_loaded_asset(asset, only_if_is_dirty=False):
            failures.append(f"failed to save intake asset: {asset_path}")
    inventory = disk_inventory()
    if inventory != EXPECTED_PACKAGE_FILES:
        failures.append(f"package inventory mismatch expected={sorted(EXPECTED_PACKAGE_FILES)} actual={sorted(inventory)}")
    if failures:
        fail("; ".join(failures))

    packages = {}
    for asset_path in EXPECTED_ASSETS:
        path = package_path(asset_path)
        if not path.is_file():
            fail(f"saved package missing on disk: {path}")
        packages[asset_path] = {
            "relative_file": str(path.relative_to(PROJECT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    payload = {
        "$schema": "cairnwell/audit/architecture/factory-envelope-kit-runtime-v001-import/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FRESH_GUARDED_SHUTTER_UNREAL_INTAKE_V001",
        "destination_namespace": DEST,
        "namespace_was_fresh": True,
        "source_manifest": str(SOURCE_MANIFEST.relative_to(PROJECT)).replace("\\", "/"),
        "source_manifest_sha256": source_manifest_sha,
        "source_exports": {
            key: {"relative_path": row["relative_path"], "sha256": row["sha256"]}
            for key, row in source["exports"].items()
        },
        "asset_packages": packages,
        "material_master": f"{DEST_MATERIALS}/{MASTER_NAME}",
        "material_instances": {
            slot: f"{DEST_MATERIALS}/{spec['instance']}" for slot, spec in MATERIAL_SPECS.items()
        },
        "meshes": measurements,
        "motion_contract": source["motion_contract"],
        "held_modules": source["held_modules"],
        "map_changes": [],
        "runtime_binding_changes": [],
        "source_assets_mutated": False,
        "failures": [],
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_FACTORY_ENVELOPE_SHUTTER_IMPORT_V001_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
