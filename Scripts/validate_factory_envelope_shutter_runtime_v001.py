"""Read-only exact validation for FactoryEnvelopeKitRuntime_v001 Unreal assets."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(__file__).resolve().parent.parent
UPROJECT = PROJECT / "LineBossCarFactory.uproject"
if not UPROJECT.is_file():
    raise RuntimeError(f"FACTORY_ENVELOPE_SHUTTER_RUNTIME_V001_FAIL: exact project descriptor missing: {UPROJECT}")
SOURCE_ROOT = PROJECT / "SourceAssets/UnrealDerived/Architecture/FactoryEnvelopeKitRuntime_v001"
SOURCE_MANIFEST = SOURCE_ROOT / "FactoryEnvelopeKitRuntime_v001_manifest.json"
DEST = "/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001"
DEST_MATERIALS = f"{DEST}/Materials"
DEST_MESHES = f"{DEST}/Meshes/Shutter"
DEST_DISK = PROJECT / "Content/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001"
AUDIT_DIR = PROJECT / "Saved/Audits/Architecture/FactoryEnvelopeKitRuntime_v001"
IMPORT_RECEIPT = AUDIT_DIR / "import_receipt_v001.json"
VALIDATION_RECEIPT = AUDIT_DIR / "validation_receipt_v001.json"
FROZEN_ROOT = PROJECT / "SourceAssets/Candidate/Architecture/FactoryEnvelopeKit_v001"

MASTER_PATH = f"{DEST_MATERIALS}/M_LB_Architecture_Surface_Master_v001"
MATERIAL_SPECS = {
    "M_LB_Architecture_WarmOffWhite_v001": {
        "path": f"{DEST_MATERIALS}/MI_LB_Architecture_WarmOffWhite_v001",
        "srgb_hex": "#E8E4DB", "metallic": 0.0, "roughness": 0.72,
    },
    "M_LB_Architecture_Graphite_v001": {
        "path": f"{DEST_MATERIALS}/MI_LB_Architecture_Graphite_v001",
        "srgb_hex": "#30363B", "metallic": 0.18, "roughness": 0.50,
    },
    "M_LB_Shutter_NeutralSilver_v001": {
        "path": f"{DEST_MATERIALS}/MI_LB_Shutter_NeutralSilver_v001",
        "srgb_hex": "#C9CED1", "metallic": 0.58, "roughness": 0.34,
    },
    "M_LB_Architecture_SafetyYellow_v001": {
        "path": f"{DEST_MATERIALS}/MI_LB_Architecture_SafetyYellow_v001",
        "srgb_hex": "#F0B91D", "metallic": 0.05, "roughness": 0.44,
    },
}
MESH_SPECS = {
    "static_wall": {
        "path": f"{DEST_MESHES}/SM_LB_ShutterBay_StaticWall_v001",
        "source_key": "static_wall", "triangles": [972],
        "simple_primitive_collision": 0, "convex_collision": 5,
        "lightmap_resolution": 128,
    },
    "frame": {
        "path": f"{DEST_MESHES}/SM_LB_ShutterBay_Frame_v001",
        "source_key": "frame", "triangles": [432],
        "simple_primitive_collision": 0, "convex_collision": 4,
        "lightmap_resolution": 128,
    },
    "leaf": {
        "path": f"{DEST_MESHES}/SM_LB_ShutterLeaf_v001",
        "source_key": "leaf_lod0", "triangles": [3564, 1836, 972],
        "simple_primitive_collision": 0, "convex_collision": 0,
        "lightmap_resolution": 64, "lod_screen_sizes": [1.0, 0.45, 0.18],
    },
}
EXPECTED_ASSETS = [MASTER_PATH, *[row["path"] for row in MATERIAL_SPECS.values()], *[row["path"] for row in MESH_SPECS.values()]]
EXPECTED_FILES = {
    "LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/"
    + str(Path(path.replace(f"{DEST}/", ""))).replace("\\", "/")
    + ".uasset"
    for path in EXPECTED_ASSETS
}

library = unreal.EditorAssetLibrary
material_editing = unreal.MaterialEditingLibrary


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_path(asset_path: str) -> Path:
    return PROJECT / "Content" / Path(asset_path.replace("/Game/", "")).with_suffix(".uasset")


def object_path(package_path: str) -> str:
    asset_name = package_path.rsplit("/", 1)[-1]
    return f"{package_path}.{asset_name}"


def srgb_linear(value: str) -> list[float]:
    channels = [int(value[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    return [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]


def vec(value) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def expected_ue_bounds(source_row: dict) -> tuple[list[float], list[float]]:
    minimum = source_row["local_bounds_m"]["min"]
    maximum = source_row["local_bounds_m"]["max"]
    return (
        [minimum[0] * 100.0, -maximum[1] * 100.0, minimum[2] * 100.0],
        [maximum[0] * 100.0, -minimum[1] * 100.0, maximum[2] * 100.0],
    )


def disk_inventory() -> set[str]:
    if not DEST_DISK.is_dir():
        return set()
    return {
        "LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/"
        + str(path.relative_to(DEST_DISK)).replace("\\", "/")
        for path in DEST_DISK.rglob("*.uasset")
        if path.is_file()
    }


def main() -> None:
    failures: list[str] = []
    evidence = {
        "source": {}, "materials": {}, "meshes": {}, "packages": {}, "immutability": {},
    }
    static_mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if static_mesh_editor is None:
        raise RuntimeError("StaticMeshEditorSubsystem unavailable; use full UnrealEditor -ExecutePythonScript")
    running_project_name = str(unreal.SystemLibrary.get_game_name())
    if running_project_name != "LineBossCarFactory":
        raise RuntimeError(f"running project name mismatch: {running_project_name!r}")
    running_content_dir = Path(unreal.Paths.project_content_dir()).resolve()
    expected_content_dir = (PROJECT / "Content").resolve()
    if running_content_dir != expected_content_dir:
        raise RuntimeError(f"running project content path mismatch: {running_content_dir} != {expected_content_dir}")

    if not SOURCE_MANIFEST.is_file():
        failures.append(f"source manifest missing: {SOURCE_MANIFEST}")
        source = {}
        source_sha = None
    else:
        source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        source_sha = sha256(SOURCE_MANIFEST)
        evidence["source"] = {"manifest": str(SOURCE_MANIFEST), "sha256": source_sha, "status": source.get("status")}
        if source.get("status") != "PASS__FROZEN_SHUTTER_RUNTIME_FBXS_WITH_AUTHORED_SIMPLE_COLLISION_V001":
            failures.append(f"source manifest is not approved: {source.get('status')}")
        if source.get("source_assets_mutated") is not False:
            failures.append("source manifest does not preserve immutable SourceAssets")
        for key, row in source.get("exports", {}).items():
            path = SOURCE_ROOT / row["relative_path"]
            if not path.is_file() or sha256(path) != row.get("sha256"):
                failures.append(f"source runtime FBX drift: {key}:{path}")

    if not IMPORT_RECEIPT.is_file():
        failures.append(f"import receipt missing: {IMPORT_RECEIPT}")
        imported = {}
    else:
        imported = json.loads(IMPORT_RECEIPT.read_text(encoding="utf-8"))
        if imported.get("status") != "PASS__FRESH_GUARDED_SHUTTER_UNREAL_INTAKE_V001":
            failures.append(f"import receipt is not approved: {imported.get('status')}")
        if source_sha and imported.get("source_manifest_sha256") != source_sha:
            failures.append("import receipt source-manifest hash drift")
        if imported.get("map_changes") != [] or imported.get("runtime_binding_changes") != []:
            failures.append("import receipt unexpectedly records map/runtime changes")

    inventory = disk_inventory()
    if inventory != EXPECTED_FILES:
        failures.append(f"namespace package inventory drift expected={sorted(EXPECTED_FILES)} actual={sorted(inventory)}")

    for asset_path in EXPECTED_ASSETS:
        path = package_path(asset_path)
        package_row = {"file": str(path.relative_to(PROJECT)).replace("\\", "/"), "exists": path.is_file()}
        if not path.is_file():
            failures.append(f"asset package missing: {path}")
        else:
            package_row.update({"bytes": path.stat().st_size, "sha256": sha256(path)})
            expected_row = imported.get("asset_packages", {}).get(asset_path)
            if not expected_row or package_row["sha256"] != expected_row.get("sha256"):
                failures.append(f"asset package changed since guarded import: {asset_path}")
        evidence["packages"][asset_path] = package_row

    master = library.load_asset(MASTER_PATH)
    if not isinstance(master, unreal.Material):
        failures.append(f"material master missing/wrong type: {MASTER_PATH}")
    else:
        used_hism = bool(master.get_editor_property("used_with_instanced_static_meshes"))
        if not used_hism:
            failures.append("architecture master lacks instanced-static-mesh usage")
        evidence["materials"][MASTER_PATH] = {"type": str(type(master)), "used_with_instanced_static_meshes": used_hism}

    expected_material_paths = {slot: object_path(row["path"]) for slot, row in MATERIAL_SPECS.items()}
    for slot, spec in MATERIAL_SPECS.items():
        instance = library.load_asset(spec["path"])
        if not isinstance(instance, unreal.MaterialInstanceConstant):
            failures.append(f"material instance missing/wrong type: {spec['path']}")
            continue
        parent = instance.get_editor_property("parent")
        parent_path = parent.get_path_name() if parent else None
        colour = material_editing.get_material_instance_vector_parameter_value(instance, "BaseColour")
        roughness = float(material_editing.get_material_instance_scalar_parameter_value(instance, "Roughness"))
        metallic = float(material_editing.get_material_instance_scalar_parameter_value(instance, "Metallic"))
        measured_colour = [float(colour.r), float(colour.g), float(colour.b)]
        expected_colour = srgb_linear(spec["srgb_hex"])
        if parent_path != object_path(MASTER_PATH):
            failures.append(f"material parent drift: {spec['path']} -> {parent_path}")
        if max(abs(measured_colour[index] - expected_colour[index]) for index in range(3)) > 1e-5:
            failures.append(f"material colour drift: {spec['path']} {measured_colour} != {expected_colour}")
        if abs(roughness - spec["roughness"]) > 1e-5 or abs(metallic - spec["metallic"]) > 1e-5:
            failures.append(f"material scalar drift: {spec['path']} rough={roughness} metal={metallic}")
        evidence["materials"][spec["path"]] = {
            "source_slot": slot, "parent": parent_path, "base_colour_linear": measured_colour,
            "roughness": roughness, "metallic": metallic,
        }

    for key, spec in MESH_SPECS.items():
        mesh = library.load_asset(spec["path"])
        if not isinstance(mesh, unreal.StaticMesh):
            failures.append(f"static mesh missing/wrong type: {spec['path']}")
            continue
        lod_count = mesh.get_num_lods()
        triangles = [mesh.get_num_triangles(index) for index in range(lod_count)]
        vertices = [mesh.get_num_vertices(index) for index in range(lod_count)]
        if triangles != spec["triangles"]:
            failures.append(f"{key} LOD/triangle drift: {triangles} != {spec['triangles']}")
        box = mesh.get_bounding_box()
        measured_min, measured_max = vec(box.min), vec(box.max)
        source_row = source.get("exports", {}).get(spec["source_key"])
        if source_row:
            expected_min, expected_max = expected_ue_bounds(source_row)
            delta_cm = [measured_min[index] - expected_min[index] for index in range(3)] + [measured_max[index] - expected_max[index] for index in range(3)]
            if max(abs(value) for value in delta_cm) > 0.25:
                failures.append(f"{key} scale/pivot/handedness drift cm={delta_cm}")
        else:
            expected_min, expected_max, delta_cm = [], [], []
            failures.append(f"{key} source bounds contract missing")

        simple_primitive = static_mesh_editor.get_simple_collision_count(mesh)
        convex = static_mesh_editor.get_convex_collision_count(mesh)
        if simple_primitive != spec["simple_primitive_collision"]:
            failures.append(
                f"{key} simple primitive collision drift: {simple_primitive} "
                f"!= {spec['simple_primitive_collision']}"
            )
        if convex != spec["convex_collision"]:
            failures.append(
                f"{key} authored UCX convex collision drift: {convex} "
                f"!= {spec['convex_collision']}"
            )
        body = mesh.get_editor_property("body_setup")
        trace = str(body.get_editor_property("collision_trace_flag")) if body else None
        if trace is None or "USE_DEFAULT" not in trace.upper():
            failures.append(f"{key} collision trace is not default/simple: {trace}")
        nanite = bool(static_mesh_editor.get_nanite_settings(mesh).get_editor_property("enabled"))
        if nanite:
            failures.append(f"{key} Nanite unexpectedly enabled")
        lightmap_resolution = int(mesh.get_editor_property("light_map_resolution"))
        if lightmap_resolution != spec["lightmap_resolution"]:
            failures.append(f"{key} lightmap resolution drift: {lightmap_resolution}")

        slots = []
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            slot_name = str(slot.get_editor_property("material_slot_name"))
            material = mesh.get_material(index)
            material_path = material.get_path_name() if material else None
            expected_path = expected_material_paths.get(slot_name)
            if expected_path is None:
                failures.append(f"{key} unexpected material slot {index}:{slot_name}")
            elif material_path != expected_path:
                failures.append(f"{key} material binding drift {slot_name}: {material_path} != {expected_path}")
            slots.append({"index": index, "slot_name": slot_name, "material": material_path})

        lod_screens = [round(float(value), 4) for value in static_mesh_editor.get_lod_screen_sizes(mesh)]
        if "lod_screen_sizes" in spec and lod_screens != spec["lod_screen_sizes"]:
            failures.append(f"{key} LOD screen-size drift: {lod_screens} != {spec['lod_screen_sizes']}")
        evidence["meshes"][key] = {
            "asset": spec["path"], "lod_count": lod_count, "triangles": triangles, "vertices": vertices,
            "bounds_cm": {
                "min": [round(value, 4) for value in measured_min],
                "max": [round(value, 4) for value in measured_max],
                "dimensions": [round(measured_max[index] - measured_min[index], 4) for index in range(3)],
            },
            "expected_bounds_cm_after_handedness": {"min": expected_min, "max": expected_max},
            "bounds_delta_cm": [round(value, 5) for value in delta_cm],
            "material_slots": slots,
            "simple_primitive_collision_count": simple_primitive,
            "convex_collision_count": convex,
            "collision_trace_flag": trace, "nanite_enabled": nanite,
            "light_map_resolution": lightmap_resolution, "lod_screen_sizes": lod_screens,
        }

    # The selected frozen files are re-hashed here.  The preparation manifest
    # also records matching before/after hashes from the Blender-derived pass.
    immutable_files = [
        FROZEN_ROOT / "README.md",
        FROZEN_ROOT / "Audits/FactoryEnvelopeKit_manifest_v001.json",
        FROZEN_ROOT / "Audits/SHA256SUMS_v001.txt",
        FROZEN_ROOT / "Derived/ShutterProductionPrep/LB_Architecture_ShutterBay_ProductionPrep_v001.blend",
        FROZEN_ROOT / "Derived/ShutterProductionPrep/Exports/LB_ShutterBay_ProductionPrep_v001.fbx",
        FROZEN_ROOT / "Derived/ShutterProductionPrep/Exports/LB_ShutterLeaf_LOD1_v001.fbx",
        FROZEN_ROOT / "Derived/ShutterProductionPrep/Exports/LB_ShutterLeaf_LOD2_v001.fbx",
    ]
    source_before = source.get("source_hashes_before", {})
    source_after = source.get("source_hashes_after", {})
    for path in immutable_files:
        if not path.is_file():
            failures.append(f"frozen immutable file missing: {path}")
            continue
        measured = sha256(path)
        if source_before.get(str(path)) != measured or source_after.get(str(path)) != measured:
            failures.append(f"frozen immutable hash drift: {path}")
        evidence["immutability"][str(path)] = measured

    held = source.get("held_modules", {})
    if set(held) != {"postless_infill", "warehouse_double_door", "loading_bay"}:
        failures.append(f"held module contract drift: {held}")

    payload = {
        "$schema": "cairnwell/audit/architecture/factory-envelope-kit-runtime-v001-validation/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__SHUTTER_SCALE_PIVOT_MATERIAL_COLLISION_LOD_NAMESPACE_AND_IMMUTABILITY_V001" if not failures else "FAIL__FACTORY_ENVELOPE_SHUTTER_RUNTIME_V001",
        "destination_namespace": DEST,
        "source_manifest_sha256": source_sha,
        "import_receipt_sha256": sha256(IMPORT_RECEIPT) if IMPORT_RECEIPT.is_file() else None,
        "evidence": evidence,
        "motion_contract": source.get("motion_contract"),
        "held_modules": held,
        "map_changes": [],
        "runtime_binding_changes": [],
        "failures": failures,
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if failures:
        raise RuntimeError("; ".join(failures))
    unreal.log("LINE_BOSS_FACTORY_ENVELOPE_SHUTTER_VALIDATION_V001_PASS")


if __name__ == "__main__":
    main()
