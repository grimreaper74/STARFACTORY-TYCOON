"""Read-only, fresh-process validation of native support-kit v001 Unreal packages.

This validator must run in the second UnrealEditor process launched by the
guarded lane.  It never saves an asset or level.  It independently rechecks the
frozen source, every protected project file, all twelve package hashes, all 36
source LODs, pivots/dimensions, materials, collision, Nanite and screen sizes.
"""

from __future__ import annotations

import hashlib
import json
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
BASELINE = PROJECT / "Scripts/body_shop_support_kit_native_unreal_import_baseline_v002.json"
EXPECTED_BASELINE_SHA256 = "E563879DC47887E5F99C9E7DD5D77308F080E6B0A7ECA2C185439669376A5915"
EXPECTED_BASELINE_STATUS = "FROZEN__BODYSHOP_SUPPORT_KIT_NATIVE_V001_UNREAL_IMPORT_BASELINE_V002"
DEST = "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/BodyShop/SupportKitNative_v001/UnrealImportLane_v002"
RUN_ROOT_ENV = "LINEBOSS_BS_SUPPORT_KIT_NATIVE_V002_RUN_ROOT"
ACK_ENV = "LINEBOSS_BS_SUPPORT_KIT_NATIVE_V002_ACK"
ACK_TOKEN = "IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_BASELINE_V002_ONCE"
IMPORT_RECEIPT_NAME = "import_receipt_v002.json"
IMPORT_FAILURE_NAME = "import_failure_v002.json"
VALIDATION_RECEIPT_NAME = "fresh_load_validation_receipt_v002.json"
VALIDATION_FAILURE_NAME = "fresh_load_validation_failure_v002.json"
EXPECTED_IMPORT_STATUS = (
    "PASS__HASH_GUARDED_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_BASELINE_V002_UNREAL_INTAKE"
)

library = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_SUPPORT_KIT_NATIVE_FRESH_VALIDATION_LANE_V002_FAIL: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT).as_posix()


def file_row(path: Path) -> dict:
    if not path.is_file():
        fail("required file is missing: " + str(path))
    stat = path.stat()
    return {
        "path": project_relative(path),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def canonical_inventory_hash(rows: list[dict]) -> str:
    canonical = [
        {
            "path": row["path"],
            "bytes": int(row["bytes"]),
            "mtime_ns": int(row["mtime_ns"]),
            "sha256": row["sha256"],
        }
        for row in sorted(rows, key=lambda item: item["path"].casefold())
    ]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def resolve_run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw:
        fail(f"{RUN_ROOT_ENV} is unset; use the guarded PowerShell lane")
    if os.environ.get(ACK_ENV, "").strip() != ACK_TOKEN:
        fail("exact one-shot acknowledgement is absent")
    run_root = Path(raw).resolve()
    if run_root == AUDIT_ROOT.resolve() or not is_inside(run_root, AUDIT_ROOT):
        fail("run directory escapes the dedicated audit root: " + str(run_root))
    if not run_root.is_dir():
        fail("runner-created audit directory is missing: " + str(run_root))
    return run_root


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT:
        fail(f"project identity drift: {PROJECT} != {EXPECTED_PROJECT}")
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("running game-name drift")
    if not BASELINE.is_file() or sha256(BASELINE) != EXPECTED_BASELINE_SHA256:
        fail("exact frozen import baseline is missing or changed")
    payload = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") != "lineboss/bodyshop-support-kit-native-v001-unreal-import-baseline/v2"
            or payload.get("status") != EXPECTED_BASELINE_STATUS
            or payload.get("destination", {}).get("namespace") != DEST
            or int(payload.get("destination", {}).get("expected_asset_count", -1)) != 12):
        fail("baseline identity/destination contract drift")
    return payload


def verify_source(baseline: dict) -> dict:
    expected_rows = {row["path"]: row for row in baseline["source"]["all_files"]}
    root = PROJECT / baseline["source"]["root"]
    actual_paths = {project_relative(path) for path in root.rglob("*") if path.is_file()}
    if actual_paths != set(expected_rows):
        fail("frozen source path inventory drift")
    rows = []
    for relative in sorted(expected_rows, key=str.casefold):
        actual = file_row(PROJECT / relative)
        wanted = expected_rows[relative]
        if (actual["bytes"] != int(wanted["bytes"])
                or actual["mtime_ns"] != int(wanted["mtime_ns"])
                or actual["sha256"] != str(wanted["sha256"]).upper()):
            fail("frozen source file drift: " + relative)
        rows.append(actual)
    digest = canonical_inventory_hash(rows)
    if digest != baseline["source"]["inventory_sha256"]:
        fail("frozen source canonical inventory hash drift")
    return {"file_count": len(rows), "inventory_sha256": digest}


def scan_protected_group(group: dict) -> set[str]:
    selected: set[Path] = set()
    for relative in group.get("files", []):
        selected.add(PROJECT / relative)
    for relative in group.get("roots", []):
        root = PROJECT / relative
        if not root.is_dir():
            if group.get("allow_empty"):
                continue
            fail("protected root missing: " + str(root))
        selected.update(path for path in root.rglob("*") if path.is_file())
    excludes = [PROJECT / relative for relative in group.get("excludes", [])]
    selected = {
        path for path in selected
        if not any(path.resolve() == excluded.resolve() or is_inside(path, excluded) for excluded in excludes)
    }
    return {project_relative(path) for path in selected}


def verify_protected_full(baseline: dict) -> dict:
    protected = baseline["protected"]
    expected = {row["path"]: row for row in protected["files"]}
    actual_union: set[str] = set()
    groups = []
    for group in protected["groups"]:
        actual = scan_protected_group(group)
        wanted = set(group["paths"])
        if actual != wanted:
            fail("protected group inventory drift: " + group["name"])
        actual_union.update(actual)
        groups.append({"name": group["name"], "file_count": len(actual)})
    if actual_union != set(expected):
        fail("protected union inventory drift")
    rows = []
    for relative in sorted(actual_union, key=str.casefold):
        actual = file_row(PROJECT / relative)
        wanted = expected[relative]
        if (actual["bytes"] != int(wanted["bytes"])
                or actual["mtime_ns"] != int(wanted["mtime_ns"])
                or actual["sha256"] != str(wanted["sha256"]).upper()):
            fail("protected file drift: " + relative)
        rows.append(actual)
    digest = canonical_inventory_hash(rows)
    if digest != protected["inventory_sha256"]:
        fail("protected canonical inventory hash drift")
    return {"file_count": len(rows), "inventory_sha256": digest, "groups": groups}


def package_file(package_path: str) -> Path:
    return PROJECT / "Content" / Path(package_path.removeprefix("/Game/")).with_suffix(".uasset")


def object_path(package_path: str) -> str:
    return package_path + "." + package_path.rsplit("/", 1)[-1]


def namespace_disk_inventory() -> dict:
    if not DEST_DISK.is_dir():
        return {}
    output = {}
    for path in sorted(DEST_DISK.rglob("*"), key=lambda item: str(item).casefold()):
        if path.is_file():
            row = file_row(path)
            output[row["path"]] = {
                "bytes": row["bytes"], "mtime_ns": row["mtime_ns"], "sha256": row["sha256"]
            }
    return output


def vector(value) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def lod_bounds(mesh: unreal.StaticMesh, lod_index: int) -> dict:
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    requested_lod = unreal.GeometryScriptMeshReadLOD()
    requested_lod.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": lod_index,
    })
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, options, requested_lod, False
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail(f"source LOD bounds extraction failed: {mesh.get_name()}:LOD{lod_index}:{outcome}")
    box = dynamic_mesh.get_mesh_bounding_box()
    minimum = vector(box.min)
    maximum = vector(box.max)
    return {
        "minimum_cm": minimum,
        "maximum_cm": maximum,
        "dimensions_cm": [maximum[index] - minimum[index] for index in range(3)],
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def assert_bounds(actual: dict, expected: dict, tolerance: float, label: str) -> None:
    for field in ("minimum_cm", "maximum_cm", "dimensions_cm"):
        delta = [float(actual[field][index]) - float(expected[field][index]) for index in range(3)]
        if max(abs(value) for value in delta) > tolerance:
            fail(label + " " + field + " drift: " + repr(delta))


def global_slot_names(mesh: unreal.StaticMesh) -> list[str]:
    return [
        str(row.get_editor_property("material_slot_name"))
        for row in mesh.get_editor_property("static_materials")
    ]


def section_slot_names(mesh: unreal.StaticMesh, subsystem, lod_index: int, slots: list[str]) -> list[str]:
    output = []
    for section_index in range(int(mesh.get_num_sections(lod_index))):
        slot_index = int(subsystem.get_lod_material_slot(mesh, lod_index, section_index))
        if slot_index < 0 or slot_index >= len(slots):
            fail(f"section material index invalid: {mesh.get_name()}:LOD{lod_index}:{section_index}")
        output.append(slots[slot_index])
    return output


def import_data_contract(mesh: unreal.StaticMesh) -> dict:
    data = mesh.get_editor_property("asset_import_data")
    output = {
        "import_uniform_scale": float(data.get_editor_property("import_uniform_scale")),
        "convert_scene": bool(data.get_editor_property("convert_scene")),
        "convert_scene_unit": bool(data.get_editor_property("convert_scene_unit")),
        "force_front_x_axis": bool(data.get_editor_property("force_front_x_axis")),
        "transform_vertex_to_absolute": bool(data.get_editor_property("transform_vertex_to_absolute")),
        "bake_pivot_in_vertex": bool(data.get_editor_property("bake_pivot_in_vertex")),
        "generate_lightmap_u_vs": bool(data.get_editor_property("generate_lightmap_u_vs")),
        "auto_generate_collision": bool(data.get_editor_property("auto_generate_collision")),
        "remove_degenerates": bool(data.get_editor_property("remove_degenerates")),
    }
    expected = {
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
    }
    if output != expected:
        fail("legacy FBX import setting drift: " + mesh.get_name() + ":" + repr(output))
    return output


def validate_mesh(key: str, spec: dict, baseline: dict, subsystem) -> dict:
    mesh = library.load_asset(spec["package_path"])
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
        fail("fresh-load StaticMesh/object path drift: " + key)
    if int(mesh.get_num_lods()) != 3:
        fail("fresh-load LOD count drift: " + key)
    expected_screens = [round(float(value), 6) for value in baseline["import_contract"]["lod_screen_sizes"]]
    screens = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
    auto = bool(mesh.is_lod_screen_size_auto_computed())
    if screens != expected_screens or auto:
        fail("fresh-process manual LOD screen-size persistence drift: " + key + ":" + repr(screens))
    slots = global_slot_names(mesh)
    expected_slots = list(spec["lods"][0]["material_slots"])
    if slots != expected_slots:
        fail("fresh-load global material-slot order drift: " + key)

    tolerance = float(baseline["import_contract"]["bounds_tolerance_cm"])
    pivot_tolerance = float(baseline["import_contract"]["pivot_tolerance_cm"])
    lod_rows = []
    for lod_index, expected_lod in enumerate(spec["lods"]):
        triangles = int(mesh.get_num_triangles(lod_index))
        if triangles != int(expected_lod["triangles"]):
            fail(f"fresh-load triangle drift: {key}:LOD{lod_index}:{triangles}")
        bounds = lod_bounds(mesh, lod_index)
        assert_bounds(bounds, expected_lod["expected_unreal_bounds"], tolerance, f"fresh:{key}:LOD{lod_index}")
        if (abs(bounds["minimum_cm"][2]) > pivot_tolerance
                or abs((bounds["minimum_cm"][0] + bounds["maximum_cm"][0]) * 0.5) > tolerance
                or abs((bounds["minimum_cm"][1] + bounds["maximum_cm"][1]) * 0.5) > tolerance):
            fail(f"fresh-load floor-centred pivot drift: {key}:LOD{lod_index}")
        sections = section_slot_names(mesh, subsystem, lod_index, slots)
        if sections != list(expected_lod["material_slots"]):
            fail(f"fresh-load section/material drift: {key}:LOD{lod_index}:{sections}")
        uv_channels = int(mesh.get_num_tex_coords(lod_index))
        if uv_channels != int(baseline["import_contract"]["expected_uv_channels_per_lod"]):
            fail(f"fresh-load UV channel drift: {key}:LOD{lod_index}:{uv_channels}")
        lod_rows.append({
            "lod": lod_index,
            "triangles": triangles,
            "vertices": int(mesh.get_num_vertices(lod_index)),
            "uv_channels": uv_channels,
            "bounds": bounds,
            "section_material_slots": sections,
        })
    triangle_chain = [row["triangles"] for row in lod_rows]
    if not (triangle_chain[0] > triangle_chain[1] > triangle_chain[2] > 0):
        fail("fresh-load strict monotonic triangle drift: " + key + ":" + repr(triangle_chain))

    expected_materials = [
        object_path(baseline["import_contract"]["material_bindings"][slot]) for slot in slots
    ]
    bound_materials = [
        mesh.get_material(index).get_path_name() if mesh.get_material(index) else None
        for index in range(len(slots))
    ]
    if bound_materials != expected_materials:
        fail("fresh-load deterministic material binding drift: " + key)
    body = mesh.get_editor_property("body_setup")
    if body is None:
        fail("fresh-load BodySetup missing: " + key)
    simple = int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh))
    convex = int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh))
    trace = str(body.get_editor_property("collision_trace_flag"))
    nanite = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    collision = spec["collision"]
    if (simple != int(collision["simple_count"])
            or convex != int(collision["convex_count"])
            or "USE_DEFAULT" not in trace.upper()
            or nanite):
        fail("fresh-load collision/Nanite drift: " + key + f":{simple}:{convex}:{trace}:{nanite}")
    return {
        "asset_key": key,
        "object_path": mesh.get_path_name(),
        "lod_count": 3,
        "lod_screen_sizes": screens,
        "lod_screen_size_auto_computed": auto,
        "lods": lod_rows,
        "triangle_chain": triangle_chain,
        "strict_monotonic_triangles": True,
        "global_material_slots": slots,
        "bound_materials": bound_materials,
        "simple_collision_count": simple,
        "convex_collision_count": convex,
        "collision_trace_flag": trace,
        "nanite_enabled": nanite,
        "legacy_import_data": import_data_contract(mesh),
    }


def main() -> None:
    run_root = resolve_run_root()
    import_receipt_path = run_root / IMPORT_RECEIPT_NAME
    import_failure_path = run_root / IMPORT_FAILURE_NAME
    receipt = run_root / VALIDATION_RECEIPT_NAME
    failure_receipt = run_root / VALIDATION_FAILURE_NAME
    evidence = {
        "$schema": "lineboss/audit/bodyshop-support-kit-native-v001-fresh-load-validation/v2",
        "generated_utc": now(),
        "process_id": os.getpid(),
        "destination_namespace": DEST,
        "write_scope": [str(receipt), str(failure_receipt)],
        "asset_or_level_saves": [],
    }
    source_before = None
    protected_before = None
    target_before = None
    try:
        if receipt.exists() or failure_receipt.exists():
            fail("run directory already contains a fresh-validation result")
        if import_failure_path.exists():
            fail("import failure receipt exists; validation is forbidden")
        if not import_receipt_path.is_file():
            fail("same-run import receipt is missing")
        baseline = load_baseline()
        evidence["baseline_sha256"] = sha256(BASELINE)
        source_before = verify_source(baseline)
        protected_before = verify_protected_full(baseline)

        imported = json.loads(import_receipt_path.read_text(encoding="utf-8-sig"))
        import_pid = int(imported.get("process_id", -1))
        if (imported.get("$schema") != "lineboss/audit/bodyshop-support-kit-native-v001-unreal-import/v2"
                or imported.get("status") != EXPECTED_IMPORT_STATUS
                or imported.get("baseline_sha256") != EXPECTED_BASELINE_SHA256
                or import_pid <= 0
                or import_pid == os.getpid()
                or int(imported.get("asset_count", -1)) != 12
                or int(imported.get("source_fbx_count", -1)) != 36):
            fail("same-run import receipt identity/fresh-process gate drift")
        if set(imported.get("assets", {})) != set(baseline["assets"]):
            fail("import receipt asset inventory drift")

        target_before = namespace_disk_inventory()
        expected_disk_paths = {spec["disk_path"] for spec in baseline["assets"].values()}
        if set(target_before) != expected_disk_paths:
            fail("fresh-process target disk inventory drift before loading")
        for key, spec in baseline["assets"].items():
            wanted = imported["assets"][key]["package"]
            actual = target_before[spec["disk_path"]]
            if (actual["bytes"] != int(wanted["bytes"])
                    or actual["mtime_ns"] != int(wanted["mtime_ns"])
                    or actual["sha256"] != str(wanted["sha256"]).upper()):
                fail("target package pre-load hash drift: " + key)

        expected_registry = {spec["package_path"] for spec in baseline["assets"].values()}
        registry = {
            str(path).rsplit(".", 1)[0]
            for path in library.list_assets(DEST, recursive=True, include_folder=False)
        }
        if registry != expected_registry:
            fail("fresh-process asset-registry inventory drift")
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None:
            fail("StaticMeshEditorSubsystem unavailable")
        assets = {
            key: validate_mesh(key, spec, baseline, subsystem)
            for key, spec in baseline["assets"].items()
        }

        target_after = namespace_disk_inventory()
        if target_after != target_before:
            fail("loading target packages changed bytes, hash or mtime")
        source_after = verify_source(baseline)
        protected_after = verify_protected_full(baseline)
        if source_after != source_before:
            fail("frozen source changed during fresh validation")
        if protected_after != protected_before:
            fail("Source/Config/saves/maps/materials or existing Content changed during fresh validation")

        evidence.update({
            "status": (
                "PASS__INDEPENDENT_FRESH_PROCESS_LOAD_12_ASSETS_3_LODS_BODYSHOP_"
                "SUPPORT_KIT_NATIVE_V001_LANE_V002"
            ),
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "import_receipt": {
                "path": project_relative(import_receipt_path),
                "sha256": sha256(import_receipt_path),
                "status": imported["status"],
            },
            "fresh_process_proof": {
                "import_process_id": import_pid,
                "validation_process_id": os.getpid(),
                "distinct": import_pid != os.getpid(),
            },
            "source_before": source_before,
            "source_after": source_after,
            "protected_before": protected_before,
            "protected_after": protected_after,
            "assets": assets,
            "asset_registry_packages": sorted(registry),
            "target_packages_before": target_before,
            "target_packages_after": target_after,
            "asset_count": len(assets),
            "lod_count_per_asset": 3,
            "target_package_hashes_unchanged_by_fresh_load": True,
            "source_config_saves_maps_and_existing_content_hashes_unchanged": True,
            "manual_lod_screen_sizes_persisted_after_fresh_process_load": True,
            "auto_compute_lod_screen_size_disabled_on_all_assets": True,
            "deterministic_material_bindings_persisted": True,
            "deterministic_box_collision_persisted": True,
            "floor_centred_pivots_and_dimensions_persisted": True,
            "strict_per_asset_monotonic_triangles_persisted": True,
            "exact_one_uv_channel_per_lod_persisted": True,
            "protected_press_v913_restored_press_body_map_config_source_saves_and_native_robot": True,
            "new_material_or_texture_assets": 0,
            "failures": [],
        })
        receipt.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_BODYSHOP_SUPPORT_KIT_NATIVE_V001_LANE_V002_FRESH_LOAD_VALIDATION_PASS")
        print(json.dumps(evidence, indent=2))
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        record = dict(evidence)
        record.update({
            "status": "FAIL_CLOSED__BODYSHOP_SUPPORT_KIT_NATIVE_V001_LANE_V002_FRESH_LOAD_VALIDATION",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "source_before": source_before,
            "protected_before": protected_before,
            "target_packages_before": target_before,
            "target_packages_after_failure": namespace_disk_inventory(),
            "recovery": "Preserve the importer/validator evidence and packages; do not rerun lane v002.",
        })
        failure_receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log_error("LINE_BOSS_BODYSHOP_SUPPORT_KIT_NATIVE_V001_LANE_V002_VALIDATION_FAIL: " + str(error))
        print(json.dumps(record, indent=2))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


if __name__ == "__main__":
    main()
