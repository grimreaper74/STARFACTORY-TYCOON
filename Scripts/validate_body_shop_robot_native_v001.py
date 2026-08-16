"""Independent, read-only, fresh-process validation of the v001 robot intake.

The PowerShell lane launches this script only after the import editor exits.  It
fresh-loads all eight packages, validates all three LODs from source data, and
proves that loading did not change the target packages or protected artifacts.
It writes receipts only under Saved and never saves an asset or map.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
BASELINE = PROJECT / "Scripts/body_shop_robot_native_unreal_import_baseline_v001.json"
EXPECTED_BASELINE_SHA256 = "D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31"
EXPECTED_BASELINE_STATUS = (
    "FROZEN__HIGH_ELBOW_STRICT_MONOTONIC_BODYSHOP_ROBOT_NATIVE_V001_"
    "CLEAN_UNREAL_IMPORT_BASELINE"
)
DISPOSITION_CONTRACT = PROJECT / "Scripts/body_shop_robot_native_unreal_recovery_contract_v001.json"
EXPECTED_DISPOSITION_CONTRACT_SHA256 = "E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3"
EXPECTED_DISPOSITION_STATUS = (
    "FROZEN__TWO_FAILED_RUNS_AND_EXACT_INVALID_NAMESPACE__"
    "ARCHIVE_AND_ATOMIC_MOVE__CLEAN_IMPORT_ONLY"
)
DEST = "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane"
RUN_ROOT_ENV = "LINEBOSS_BS_ROBOT_NATIVE_RUN_ROOT"
IMPORT_RECEIPT_NAME = "import_receipt_v001.json"
VALIDATION_RECEIPT_NAME = "fresh_load_validation_receipt_v001.json"
VALIDATION_FAILURE_NAME = "fresh_load_validation_failure_v001.json"
EXPECTED_IMPORT_STATUS = (
    "PASS__INCIDENT_ARCHIVED_AND_INVALID_NAMESPACE_MOVED__FRESH_8_ASSET_"
    "3_LOD_HIGH_ELBOW_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001_IMPORT"
)

library = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_ROBOT_NATIVE_FRESH_LOAD_VALIDATION_V001_FAIL: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_exclusive_json(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT).as_posix()


def file_row(path: Path) -> dict:
    if not path.is_file():
        fail("required file is missing: " + str(path))
    stat = path.stat()
    return {"path": project_relative(path), "bytes": stat.st_size, "sha256": sha256(path)}


def canonical_inventory_hash(rows: list[dict]) -> str:
    canonical = [
        {"path": row["path"], "bytes": int(row["bytes"]), "sha256": row["sha256"]}
        for row in sorted(rows, key=lambda item: item["path"].casefold())
    ]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def resolve_run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw:
        fail(f"{RUN_ROOT_ENV} is unset; use the guarded PowerShell lane")
    run_root = Path(raw).resolve()
    allowed = AUDIT_ROOT.resolve()
    if run_root == allowed or not is_inside(run_root, allowed):
        fail("run receipt directory escapes the dedicated audit root: " + str(run_root))
    if not run_root.is_dir():
        fail("import run directory is missing: " + str(run_root))
    return run_root


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT:
        fail(f"project identity drift: {PROJECT} != {EXPECTED_PROJECT}")
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("running game-name drift")
    if Path(unreal.Paths.project_content_dir()).resolve() != (PROJECT / "Content").resolve():
        fail("running project Content path drift")
    if not BASELINE.is_file() or sha256(BASELINE) != EXPECTED_BASELINE_SHA256:
        fail("exact frozen import baseline is missing or changed")
    payload = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") != "lineboss/bodyshop-robot-native-v001-unreal-import-baseline/v1"
            or payload.get("status") != EXPECTED_BASELINE_STATUS
            or payload.get("destination", {}).get("namespace") != DEST
            or payload.get("destination", {}).get("expected_asset_count") != 8):
        fail("baseline identity/destination contract drift")
    return payload


def load_disposition_contract() -> dict:
    if (not DISPOSITION_CONTRACT.is_file()
            or sha256(DISPOSITION_CONTRACT) != EXPECTED_DISPOSITION_CONTRACT_SHA256):
        fail("exact frozen clean disposition contract is missing or changed")
    payload = json.loads(DISPOSITION_CONTRACT.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") !=
            "lineboss/bodyshop-robot-native-v001-clean-import-disposition-contract/v1"
            or payload.get("status") != EXPECTED_DISPOSITION_STATUS
            or payload.get("baseline", {}).get("sha256") != EXPECTED_BASELINE_SHA256
            or payload.get("invalid_namespace", {}).get("namespace") != DEST
            or payload.get("invalid_namespace", {}).get("package_count") != 8):
        fail("clean disposition contract identity/scope drift")
    return payload


def verify_explicit_inventory(expected_rows: list[dict], root: Path, expected_hash: str, label: str) -> dict:
    expected = {str(row["path"]): row for row in expected_rows}
    actual_paths = {project_relative(path) for path in root.rglob("*") if path.is_file()}
    if len(expected) != len(expected_rows) or actual_paths != set(expected):
        fail(label + " exact path inventory drift")
    rows = []
    for relative in sorted(expected, key=str.casefold):
        actual = file_row(PROJECT / relative)
        wanted = expected[relative]
        if actual["bytes"] != int(wanted["bytes"]) or actual["sha256"] != str(wanted["sha256"]).upper():
            fail(label + " file drift: " + relative)
        rows.append(actual)
    digest = canonical_inventory_hash(rows)
    if digest != expected_hash:
        fail(label + " canonical inventory hash drift")
    return {"file_count": len(rows), "inventory_sha256": digest}


def scan_protected_group(group: dict) -> set[str]:
    selected: set[Path] = set()
    for relative in group.get("files", []):
        selected.add(PROJECT / relative)
    for relative in group.get("roots", []):
        root = PROJECT / relative
        if not root.is_dir():
            fail("protected root missing for " + group["name"] + ": " + str(root))
        selected.update(path for path in root.rglob("*") if path.is_file())
    for pattern in group.get("globs", []):
        selected.update(path for path in PROJECT.glob(pattern) if path.is_file())
    excludes = [PROJECT / relative for relative in group.get("excludes", [])]
    selected = {path for path in selected if not any(is_inside(path, excluded) for excluded in excludes)}
    return {project_relative(path) for path in selected}


def verify_protected(baseline: dict) -> dict:
    protected = baseline["protected"]
    expected_rows = {row["path"]: row for row in protected["files"]}
    union: set[str] = set()
    groups = []
    for group in protected["groups"]:
        actual = scan_protected_group(group)
        wanted = set(group["paths"])
        if actual != wanted:
            fail("protected group inventory drift: " + group["name"])
        union.update(actual)
        groups.append({"name": group["name"], "file_count": len(actual)})
    if union != set(expected_rows):
        fail("protected union inventory drift")
    rows = []
    for relative in sorted(union, key=str.casefold):
        actual = file_row(PROJECT / relative)
        wanted = expected_rows[relative]
        if actual["bytes"] != int(wanted["bytes"]) or actual["sha256"] != str(wanted["sha256"]).upper():
            fail("protected file hash drift: " + relative)
        rows.append(actual)
    digest = canonical_inventory_hash(rows)
    if digest != protected["inventory_sha256"]:
        fail("protected canonical inventory hash drift")
    return {"file_count": len(rows), "inventory_sha256": digest, "groups": groups}


def verify_source(baseline: dict) -> dict:
    source = baseline["source"]
    return verify_explicit_inventory(
        source["all_files"], PROJECT / source["root"], source["inventory_sha256"], "frozen source"
    )


def verify_active_body_shop_binding(baseline: dict) -> dict:
    gate = baseline.get("active_body_shop_binding", {})
    expected_status = "PASS__ACTIVE_BODYSHOP_BINDINGS_USE_ONLY_NATIVE_V001_ROBOT_AND_OPEN_CGUN"
    if gate.get("status") != expected_status or gate.get("forbidden_matches") != []:
        fail("active Body Shop native-binding baseline gate is not PASS")
    forbidden = str(gate.get("forbidden_old_runtime_token", ""))
    if not forbidden:
        fail("active Body Shop binding has no forbidden old-runtime token")
    matches = []
    for relative in gate.get("scanned_files", []):
        path = PROJECT / relative
        for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            if forbidden in line:
                matches.append({"path": relative, "line": line_number})
    if matches:
        fail("old WeldRobotRuntime_v001 path remains in active Body Shop binding: " + repr(matches))
    required = list(gate.get("required_object_paths", []))
    expected = [baseline["assets"][key]["object_path"] for key in ("Base", "J1", "J2", "J3", "J4", "J5", "J6", "CGun")]
    if required != expected:
        fail("active Body Shop native object-path inventory drift")
    authority = PROJECT / gate["binding_authority"]
    authority_text = authority.read_text(encoding="utf-8-sig")
    missing = [path for path in required if path not in authority_text]
    if missing:
        fail("active Body Shop binding authority is missing native object paths: " + repr(missing))
    return {
        "status": expected_status,
        "scanned_file_count": len(gate["scanned_files"]),
        "forbidden_old_runtime_token": forbidden,
        "forbidden_matches": [],
        "binding_authority": gate["binding_authority"],
        "required_object_paths": required,
        "archived_legacy_scope_not_rejected": gate["archived_legacy_scope_not_semantically_rejected"],
    }


def content_metadata_snapshot() -> dict:
    rows = []
    for path in sorted((PROJECT / "Content").rglob("*"), key=lambda item: str(item).casefold()):
        if not path.is_file() or is_inside(path, DEST_DISK):
            continue
        stat = path.stat()
        rows.append({"path": project_relative(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"file_count": len(rows), "metadata_sha256": hashlib.sha256(encoded).hexdigest().upper()}


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
            output[row["path"]] = {"bytes": row["bytes"], "sha256": row["sha256"]}
    return output


def verify_row_at(path: Path, expected: dict, label: str) -> dict:
    if not path.is_file():
        fail(label + " missing: " + str(path))
    actual = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    if (actual["bytes"] != int(expected["bytes"])
            or actual["sha256"] != str(expected["sha256"]).upper()):
        fail(label + " hash/size drift: " + str(path))
    return actual


def verify_windows_read_only(path: Path, label: str) -> None:
    attributes = int(getattr(path.stat(), "st_file_attributes", 0))
    if not attributes & int(stat.FILE_ATTRIBUTE_READONLY):
        fail(label + " lacks the Windows read-only archive attribute: " + str(path))


def verify_exact_project_path_inventory(root: Path, expected: set[str], label: str) -> None:
    if not root.is_dir():
        fail(label + " root is missing: " + str(root))
    actual = {project_relative(path) for path in root.rglob("*") if path.is_file()}
    if actual != expected:
        fail(label + " exact recursive path inventory drift")


def verify_failed_runs(disposition: dict) -> dict:
    output = []
    for failed_run in disposition["failed_runs"]:
        root = PROJECT / failed_run["root"]
        actual_paths = {
            path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
        }
        expected = {row["path"]: row for row in failed_run["files"]}
        if actual_paths != set(expected):
            fail("failed run path inventory drift: " + failed_run["id"])
        rows = []
        for relative in sorted(expected, key=str.casefold):
            actual = verify_row_at(root / relative, expected[relative], "failed run")
            rows.append({"path": relative, **actual})
        digest = canonical_inventory_hash(rows)
        if digest != failed_run["inventory_sha256"]:
            fail("failed run canonical inventory drift: " + failed_run["id"])
        output.append({
            "id": failed_run["id"], "root": failed_run["root"],
            "file_count": len(rows), "inventory_sha256": digest,
        })
    return {"run_count": len(output), "runs": output}


def verify_clean_disposition_archive(run_root: Path, disposition: dict) -> dict:
    contract = disposition["archive_and_move"]
    receipt_path = run_root / contract["receipt_name"]
    failure_path = run_root / contract["failure_name"]
    if failure_path.exists() or not receipt_path.is_file():
        fail("valid offline clean disposition PASS receipt is unavailable")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    expected_status = (
        "PASS__TWO_FAILED_RUNS_AND_INVALID_NAMESPACE_ARCHIVED_BYTE_FOR_BYTE__"
        "INVALID_NAMESPACE_ATOMICALLY_MOVED__CONTENT_PATH_ABSENT"
    )
    expected_failed_count = sum(row["file_count"] for row in disposition["failed_runs"])
    package_count = disposition["invalid_namespace"]["package_count"]
    if (receipt.get("$schema") !=
            "lineboss/audit/bodyshop-robot-native-v001-pre-clean-import-disposition/v1"
            or receipt.get("status") != expected_status
            or receipt.get("clean_disposition_contract_sha256") !=
               EXPECTED_DISPOSITION_CONTRACT_SHA256
            or receipt.get("failed_run_archive_count") != expected_failed_count
            or receipt.get("invalid_namespace_archive_count") != package_count
            or receipt.get("recoverably_moved_package_count") != package_count
            or receipt.get("namespace_move_completed") is not True
            or receipt.get("content_namespace_absent") is not True
            or receipt.get("content_packages_deleted") != 0
            or receipt.get("content_files_written") != 0):
        fail("offline clean disposition receipt contract drift")

    failed_expected = {}
    for failed_run in disposition["failed_runs"]:
        root = (PROJECT / failed_run["root"]).resolve()
        for row in failed_run["files"]:
            failed_expected[str((root / row["path"]).resolve())] = row
    package_expected = {
        str((PROJECT / row["path"]).resolve()): row
        for row in disposition["invalid_namespace"]["packages"]
    }
    verified_groups = {}
    for receipt_key, expected in (
            ("failed_run_archives", failed_expected),
            ("invalid_namespace_archives", package_expected)):
        rows = receipt.get(receipt_key, [])
        if {str(Path(row.get("source_path", "")).resolve()) for row in rows} != set(expected):
            fail("clean disposition archived-source inventory drift: " + receipt_key)
        verified = []
        for row in rows:
            wanted = expected[str(Path(row["source_path"]).resolve())]
            actual = verify_row_at(PROJECT / row["archived_path"], wanted, "clean archive")
            if row.get("archive_read_only") is not True:
                fail("clean disposition archive is not marked immutable: " + row["archived_path"])
            verify_windows_read_only(PROJECT / row["archived_path"], "clean disposition archive")
            verified.append({"path": row["archived_path"], **actual})
        verified_groups[receipt_key] = verified
    verify_exact_project_path_inventory(
        run_root / contract["failed_runs_archive_folder"],
        {row["archived_path"] for row in receipt["failed_run_archives"]},
        "failed-run byte archive",
    )
    verify_exact_project_path_inventory(
        run_root / contract["invalid_namespace_copy_folder"],
        {row["archived_path"] for row in receipt["invalid_namespace_archives"]},
        "invalid-namespace byte archive",
    )
    expected_by_original = {row["path"]: row for row in disposition["invalid_namespace"]["packages"]}
    moved_rows = receipt.get("recoverably_moved_packages", [])
    if {row.get("original_path") for row in moved_rows} != set(expected_by_original):
        fail("recoverably moved package inventory drift")
    moved_verified = []
    for row in moved_rows:
        actual = verify_row_at(
            PROJECT / row["moved_path"], expected_by_original[row["original_path"]],
            "recoverably moved package",
        )
        if row.get("moved_copy_read_only") is not True:
            fail("recoverably moved package is not marked immutable: " + row["moved_path"])
        verify_windows_read_only(PROJECT / row["moved_path"], "recoverably moved package")
        moved_verified.append({"path": row["moved_path"], **actual})
    verify_exact_project_path_inventory(
        run_root / contract["invalid_namespace_move_folder"] / contract["move_target_leaf"],
        {row["moved_path"] for row in moved_rows},
        "recoverably moved invalid namespace",
    )
    return {
        "receipt": project_relative(receipt_path),
        "receipt_sha256": sha256(receipt_path),
        "status": receipt["status"],
        "failed_run_archive_count": len(verified_groups["failed_run_archives"]),
        "invalid_namespace_archive_count": len(verified_groups["invalid_namespace_archives"]),
        "recoverably_moved_package_count": len(moved_verified),
        "content_namespace_absent_at_disposition": True,
        "verified_files": verified_groups,
        "moved_packages": moved_verified,
    }


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


def assert_vector_contract(actual: dict, expected: dict, tolerance: float, label: str) -> None:
    for field in ("minimum_cm", "maximum_cm", "dimensions_cm", "pivot_cm"):
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
            fail(f"invalid section material index: {mesh.get_name()}:LOD{lod_index}:{section_index}:{slot_index}")
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
        fail("legacy FBX import setting drift: " + mesh.get_name() + ": " + repr(output))
    return output


def validate_mesh(key: str, spec: dict, baseline: dict, imported: dict, subsystem) -> dict:
    imported_row = imported.get("assets", {}).get(key)
    if not imported_row:
        fail("import receipt is missing asset row: " + key)
    if (imported_row.get("initial_lod_count") != 0
            or imported_row.get("lod0_created_fresh") is not True
            or imported_row.get("missing_lods_appended") != [1, 2]
            or imported_row.get("existing_lods_reimported") != []
            or imported_row.get("strict_triangle_monotonicity") is not True):
        fail("import receipt does not prove fresh, append-only three-LOD creation: " + key)
    package = package_file(spec["package_path"])
    package_before = file_row(package)
    if (package_before["sha256"] != imported_row.get("package_sha256")
            or package_before["bytes"] != int(imported_row.get("package_bytes", -1))):
        fail("asset package hash/size changed since import: " + key)

    # This is the first asset load performed by this independent process.
    mesh = unreal.load_asset(spec["package_path"])
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
        fail("fresh-loaded StaticMesh/object path drift: " + key)
    if int(mesh.get_num_lods()) != 3:
        fail("fresh-loaded LOD count drift: " + key)
    screen_sizes = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
    expected_screens = [round(float(value), 6) for value in baseline["import_contract"]["lod_screen_sizes"]]
    auto_compute_screen_sizes = bool(mesh.is_lod_screen_size_auto_computed())
    if (screen_sizes != expected_screens or screen_sizes != imported_row.get("lod_screen_sizes")
            or auto_compute_screen_sizes
            or imported_row.get("lod_screen_size_auto_computed") is not False):
        fail("fresh-loaded LOD screen-size drift: " + key)
    write_evidence = imported_row.get("screen_size_persistence", {})
    passes = write_evidence.get("passes", [])
    if (write_evidence.get("write_order") != baseline["import_contract"]["screen_size_write_order"]
            or len(passes) != int(baseline["import_contract"]["screen_size_persistence_passes"])
            or write_evidence.get("global_final_phase_after_all_mesh_preparation") is not True
            or write_evidence.get("no_build_after_final_set") is not True
            or passes[-1].get("post_final_save_readback") != expected_screens
            or passes[-1].get("post_final_save_auto_compute") is not False):
        fail("import receipt lacks exact final screen-size persistence evidence: " + key)

    slots = global_slot_names(mesh)
    if slots != list(spec["lods"][0]["material_slots"]) or slots != imported_row.get("global_material_slots"):
        fail("fresh-loaded global semantic material slots drift: " + key)
    bound_materials = [
        mesh.get_material(index).get_path_name() if mesh.get_material(index) else None
        for index in range(len(slots))
    ]
    expected_materials = [object_path(baseline["import_contract"]["material_bindings"][slot]) for slot in slots]
    if bound_materials != expected_materials or bound_materials != imported_row.get("bound_materials"):
        fail("fresh-loaded protected presentation-material binding drift: " + key)

    tolerance = float(baseline["import_contract"]["bounds_tolerance_cm"])
    lod_rows = []
    for lod_index, expected_lod in enumerate(spec["lods"]):
        receipt_lod = imported_row["lods"][lod_index]
        triangles = int(mesh.get_num_triangles(lod_index))
        vertices = int(mesh.get_num_vertices(lod_index))
        uv_channels = int(mesh.get_num_tex_coords(lod_index))
        bounds = lod_bounds(mesh, lod_index)
        section_slots = section_slot_names(mesh, subsystem, lod_index, slots)
        if triangles != int(expected_lod["triangles"]) or triangles != int(receipt_lod["triangles"]):
            fail(f"fresh-loaded triangle drift: {key}:LOD{lod_index}")
        if vertices != int(receipt_lod["vertices"]):
            fail(f"fresh-loaded vertex drift from import receipt: {key}:LOD{lod_index}")
        expected_uv_channels = int(baseline["import_contract"]["expected_uv_channels_per_lod"])
        if (uv_channels != expected_uv_channels
                or int(expected_lod["source_uv_layers"]) != expected_uv_channels
                or uv_channels != int(receipt_lod["uv_channels"])):
            fail(f"fresh-loaded UV channel contract drift: {key}:LOD{lod_index}")
        assert_vector_contract(bounds, expected_lod["expected_unreal_bounds"], tolerance, f"{key}:LOD{lod_index}:source")
        assert_vector_contract(bounds, receipt_lod["bounds"], 0.0001, f"{key}:LOD{lod_index}:receipt")
        if section_slots != list(expected_lod["material_slots"]) or section_slots != receipt_lod["section_material_slots"]:
            fail(f"fresh-loaded per-LOD semantic material sections drift: {key}:LOD{lod_index}")
        source = PROJECT / expected_lod["source"]
        if sha256(source) != expected_lod["source_sha256"]:
            fail(f"bound source FBX changed: {key}:LOD{lod_index}")
        lod_rows.append({
            "lod": lod_index,
            "triangles": triangles,
            "vertices": vertices,
            "uv_channels": uv_channels,
            "bounds": bounds,
            "section_material_slots": section_slots,
            "source": expected_lod["source"],
            "source_sha256": expected_lod["source_sha256"],
        })
    triangle_order = [row["triangles"] for row in lod_rows]
    if not triangle_order[0] > triangle_order[1] > triangle_order[2]:
        fail("fresh-loaded strict triangle monotonicity drift: " + key + ":" + repr(triangle_order))

    body = mesh.get_editor_property("body_setup")
    if body is None:
        fail("fresh-loaded BodySetup missing: " + key)
    simple = int(subsystem.get_simple_collision_count(mesh))
    convex = int(subsystem.get_convex_collision_count(mesh))
    trace = str(body.get_editor_property("collision_trace_flag"))
    nanite = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    if (simple != 0 or convex != 0 or "SIMPLE_AS_COMPLEX" not in trace.upper() or nanite
            or simple != imported_row["simple_collision_count"]
            or convex != imported_row["convex_collision_count"]):
        fail("fresh-loaded presentation collision/Nanite drift: " + key)
    settings = import_data_contract(mesh)
    if settings != imported_row["legacy_import_data"]:
        fail("fresh-loaded import settings differ from import receipt: " + key)
    package_after = file_row(package)
    if package_after != package_before:
        fail("fresh-loading changed package bytes/hash: " + key)
    return {
        "package_path": spec["package_path"],
        "object_path": mesh.get_path_name(),
        "package_before_load": package_before,
        "package_after_load": package_after,
        "package_hash_unchanged_by_fresh_load": True,
        "lod_count": 3,
        "lod_screen_sizes": screen_sizes,
        "lod_screen_size_auto_computed": auto_compute_screen_sizes,
        "screen_size_persistence": {
            "expected": expected_screens,
            "fresh_process_readback": screen_sizes,
            "auto_compute_disabled": not auto_compute_screen_sizes,
            "import_write_evidence": write_evidence,
        },
        "lods": lod_rows,
        "strict_triangle_monotonicity": True,
        "global_material_slots": slots,
        "bound_materials": bound_materials,
        "simple_collision_count": simple,
        "convex_collision_count": convex,
        "collision_trace_flag": trace,
        "nanite_enabled": nanite,
        "legacy_import_data": settings,
    }


def main() -> None:
    run_root = resolve_run_root()
    import_receipt = run_root / IMPORT_RECEIPT_NAME
    receipt = run_root / VALIDATION_RECEIPT_NAME
    failure_receipt = run_root / VALIDATION_FAILURE_NAME
    evidence = {
        "$schema": "lineboss/audit/bodyshop-robot-native-v001-fresh-load-validation/v1",
        "generated_utc": now(),
        "process_id": os.getpid(),
        "destination_namespace": DEST,
        "writes_authorized": [str(run_root)],
        "content_asset_saves": 0,
        "map_loads_or_saves": 0,
        "runtime_binding_changes": [],
        "promotion_authorized": False,
    }
    protected_before = None
    source_before = None
    target_before = None
    failed_runs_before = None
    disposition_archive_before = None
    try:
        if receipt.exists() or failure_receipt.exists():
            fail("fresh validation result already exists in this run directory")
        baseline = load_baseline()
        disposition = load_disposition_contract()
        if not import_receipt.is_file():
            fail("guarded import receipt missing: " + str(import_receipt))
        imported = json.loads(import_receipt.read_text(encoding="utf-8-sig"))
        if (imported.get("$schema") != "lineboss/audit/bodyshop-robot-native-v001-unreal-import/v1"
                or imported.get("status") != EXPECTED_IMPORT_STATUS
                or imported.get("baseline_sha256") != EXPECTED_BASELINE_SHA256
                or imported.get("clean_disposition_contract_sha256") !=
                   EXPECTED_DISPOSITION_CONTRACT_SHA256
                or imported.get("destination_namespace") != DEST
                or imported.get("fresh_destination_import_only") is not True
                or imported.get("replace_existing") is not False
                or imported.get("reuse_existing_packages") is not False
                or imported.get("asset_count") != 8
                or imported.get("lod_count_per_asset") != 3
                or imported.get("source_fbx_count") != 24
                or imported.get("map_changes") != []
                or imported.get("config_changes") != []
                or imported.get("runtime_binding_changes") != []):
            fail("guarded import receipt contract drift")
        clean_proof = imported.get("clean_import_proof", {})
        cvar = clean_proof.get("interchange_fbx_cvar", {})
        if (clean_proof.get("failed_run_count") != 2
                or clean_proof.get("both_failed_runs_hash_verified") is not True
                or clean_proof.get("invalid_package_count_archived_and_moved") != 8
                or clean_proof.get("content_namespace_absent_before_unreal_mutation") is not True
                or clean_proof.get("fresh_lod0_packages_created") != 8
                or clean_proof.get("replace_existing") is not False
                or clean_proof.get("reuse_existing_packages") is not False
                or clean_proof.get("existing_lods_reimported") != 0
                or clean_proof.get("missing_lods_appended") != 16
                or clean_proof.get("strict_per_asset_triangle_monotonicity") is not True
                or clean_proof.get("one_uv_per_asset_lod") is not True
                or clean_proof.get("screen_size_write_order") !=
                   baseline["import_contract"]["screen_size_write_order"]
                or clean_proof.get("screen_size_persistence_passes") != 2
                or cvar.get("name") != "Interchange.FeatureFlags.Import.FBX"
                or cvar.get("disabled_value") != 0
                or cvar.get("restored_value") != cvar.get("previous_value")
                or cvar.get("restore_attempted_in_finally") is not True
                or cvar.get("set_false_only_around_custom_lod_imports") is not True
                or cvar.get("custom_lods_requested") != 16
                or len(cvar.get("custom_lods_imported", [])) != 16):
            fail("incident-bound clean import provenance contract drift")
        import_pid = int(imported.get("process_id", -1))
        if import_pid <= 0 or import_pid == os.getpid():
            fail("validator is not running in a process distinct from the import process")

        source_before = verify_source(baseline)
        protected_before = verify_protected(baseline)
        active_binding_before = verify_active_body_shop_binding(baseline)
        failed_runs_before = verify_failed_runs(disposition)
        disposition_archive_before = verify_clean_disposition_archive(run_root, disposition)
        if (failed_runs_before != imported.get("failed_runs_before")
                or failed_runs_before != imported.get("failed_runs_after")):
            fail("import receipt/two-failed-run proof drift")
        if (disposition_archive_before != imported.get("clean_disposition_archive_after")
                or disposition_archive_before != imported.get("pre_clean_import_disposition")):
            fail("import receipt/clean-disposition archive proof drift")
        outside_before = content_metadata_snapshot()
        if outside_before != disposition["invalid_namespace"]["outside_destination_content"]:
            fail("Content outside destination differs from incident-bound contract")
        target_before = namespace_disk_inventory()
        expected_disk = {spec["disk_path"] for spec in baseline["assets"].values()}
        if set(target_before) != expected_disk:
            fail("exact eight-package disk inventory drift before fresh load")
        if target_before != imported.get("namespace_disk_files"):
            fail("fresh-process package inventory/hash drift from import receipt")
        registry = {
            str(path).rsplit(".", 1)[0]
            for path in library.list_assets(DEST, recursive=True, include_folder=False)
        }
        expected_registry = {spec["package_path"] for spec in baseline["assets"].values()}
        if registry != expected_registry:
            fail("exact eight-asset registry inventory drift before fresh load")
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None:
            fail("StaticMeshEditorSubsystem unavailable; use full UnrealEditor -ExecutePythonScript")

        meshes = {}
        for key, spec in sorted(baseline["assets"].items()):
            meshes[key] = validate_mesh(key, spec, baseline, imported, subsystem)
        if len(meshes) != 8:
            fail("fresh-loaded asset count drift")

        target_after = namespace_disk_inventory()
        source_after = verify_source(baseline)
        protected_after = verify_protected(baseline)
        active_binding_after = verify_active_body_shop_binding(baseline)
        failed_runs_after = verify_failed_runs(disposition)
        disposition_archive_after = verify_clean_disposition_archive(run_root, disposition)
        outside_after = content_metadata_snapshot()
        if target_after != target_before:
            fail("target package hashes changed during read-only fresh load")
        if source_after != source_before:
            fail("frozen source changed during read-only fresh load")
        if protected_after != protected_before:
            fail("protected artifact snapshot changed during read-only fresh load")
        if active_binding_after != active_binding_before:
            fail("active Body Shop binding changed during read-only fresh load")
        if failed_runs_after != failed_runs_before:
            fail("one or both failed run trees changed during fresh-load validation")
        if disposition_archive_after != disposition_archive_before:
            fail("clean disposition archive changed during fresh-load validation")
        if outside_after != outside_before:
            fail("Content outside destination changed during read-only fresh load")

        evidence.update({
            "status": (
                "PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__"
                "8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001"
            ),
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "baseline_sha256": sha256(BASELINE),
            "clean_disposition_contract_sha256": sha256(DISPOSITION_CONTRACT),
            "import_receipt": project_relative(import_receipt),
            "import_receipt_sha256": sha256(import_receipt),
            "fresh_process_proof": {
                "import_process_id": import_pid,
                "validation_process_id": os.getpid(),
                "distinct": True,
            },
            "asset_count": len(meshes),
            "lod_count_per_asset": 3,
            "source_fbx_count": 24,
            "assets": meshes,
            "asset_registry_packages": sorted(registry),
            "target_packages_before_load": target_before,
            "target_packages_after_load": target_after,
            "target_package_hashes_unchanged_by_fresh_load": True,
            "source_before": source_before,
            "source_after": source_after,
            "protected_before": protected_before,
            "protected_after": protected_after,
            "active_body_shop_binding_before": active_binding_before,
            "active_body_shop_binding_after": active_binding_after,
            "failed_runs_before": failed_runs_before,
            "failed_runs_after": failed_runs_after,
            "clean_disposition_archive_before": disposition_archive_before,
            "clean_disposition_archive_after": disposition_archive_after,
            "outside_destination_content_before": outside_before,
            "outside_destination_content_after": outside_after,
            "body_shop_map_sha256_unchanged": baseline["protected"]["body_shop_map_sha256"],
            "press_v913_map_sha256_unchanged": baseline["protected"]["press_v913_map_sha256"],
            "config_and_existing_promoted_asset_hashes_unchanged": True,
            "high_elbow_source_gate": baseline["source"]["high_elbow_gate"],
            "manual_lod_screen_sizes_persisted_after_fresh_process_load": True,
            "auto_compute_lod_screen_size_disabled_on_all_assets": all(
                not row["lod_screen_size_auto_computed"] for row in meshes.values()
            ),
            "strict_per_asset_triangle_monotonicity": all(
                row["strict_triangle_monotonicity"] for row in meshes.values()
            ),
            "exactly_one_uv_channel_on_all_24_lods": all(
                lod["uv_channels"] == 1 for row in meshes.values() for lod in row["lods"]
            ),
            "fresh_import_no_overwrite_or_reuse_proven": True,
            "interchange_fbx_cvar_restored_before_validator_process": True,
            "failures": [],
        })
        write_exclusive_json(receipt, evidence)
        unreal.log("LINE_BOSS_BODYSHOP_ROBOT_NATIVE_V001_FRESH_LOAD_VALIDATION_PASS")
        print(json.dumps(evidence, indent=2))
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        record = dict(evidence)
        record.update({
            "status": "FAIL_CLOSED__BODYSHOP_ROBOT_NATIVE_V001_FRESH_LOAD_VALIDATION",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "source_before": source_before,
            "protected_before": protected_before,
            "failed_runs_before": failed_runs_before,
            "clean_disposition_archive_before": disposition_archive_before,
            "target_packages_before_load": target_before,
            "content_or_maps_written_by_validator": "NOT_PROVEN__VALIDATION_FAILED",
            "automatic_cleanup": "NOT_PERFORMED__IMPORT_OUTPUT_AND_FAILURE_EVIDENCE_PRESERVED",
        })
        write_exclusive_json(failure_receipt, record)
        unreal.log_error("LINE_BOSS_BODYSHOP_ROBOT_NATIVE_V001_FRESH_LOAD_VALIDATION_FAIL: " + str(error))
        print(json.dumps(record, indent=2))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


if __name__ == "__main__":
    main()
