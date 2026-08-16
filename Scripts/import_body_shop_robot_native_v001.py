"""Incident-bound, clean UE 5.8 import for the native Body Shop robot.

Run only through the guarded PowerShell lane after the offline disposition step
has archived both failed runs and atomically moved the exact invalid namespace
out of Content.  This process creates eight new packages and appends 16 custom
LODs.  It never overwrites/reuses an asset, binds actors, or loads/saves a map.
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
DISPOSITION_MODE_ENV = "LINEBOSS_BS_ROBOT_NATIVE_DISPOSITION_MODE"
DISPOSITION_MODE_TOKEN = (
    "ARCHIVE_TWO_FAILED_RUNS_MOVE_INVALID_NAMESPACE_AND_CLEAN_IMPORT_"
    "HIGH_ELBOW_MONOTONIC_V001_ONCE"
)
INTERCHANGE_FBX_CVAR = "Interchange.FeatureFlags.Import.FBX"
IMPORT_RECEIPT_NAME = "import_receipt_v001.json"
IMPORT_FAILURE_NAME = "import_failure_v001.json"

library = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_ROBOT_NATIVE_UNREAL_IMPORT_V001_FAIL: " + message)


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
    run_root.mkdir(parents=True, exist_ok=True)
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
    mode = os.environ.get(DISPOSITION_MODE_ENV, "").strip()
    if mode != DISPOSITION_MODE_TOKEN:
        fail("exact incident-bound clean disposition mode is not acknowledged")
    if (not DISPOSITION_CONTRACT.is_file()
            or sha256(DISPOSITION_CONTRACT) != EXPECTED_DISPOSITION_CONTRACT_SHA256):
        fail("exact frozen clean disposition contract is missing or changed")
    payload = json.loads(DISPOSITION_CONTRACT.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") !=
            "lineboss/bodyshop-robot-native-v001-clean-import-disposition-contract/v1"
            or payload.get("status") != EXPECTED_DISPOSITION_STATUS
            or payload.get("disposition_mode_token") != DISPOSITION_MODE_TOKEN
            or payload.get("baseline", {}).get("sha256") != EXPECTED_BASELINE_SHA256
            or payload.get("invalid_namespace", {}).get("namespace") != DEST
            or payload.get("invalid_namespace", {}).get("package_count") != 8):
        fail("clean disposition contract identity/scope drift")
    policy = payload.get("policy", {})
    fresh = payload.get("fresh_import", {})
    if (policy.get("one_shot_clean_import") is not True
            or policy.get("content_package_delete_authorized") is not False
            or fresh.get("replace_existing") is not False
            or fresh.get("reuse_existing_packages") is not False
            or fresh.get("existing_lods_reimported") != 0):
        fail("clean disposition safety policy drift")
    return payload


def verify_explicit_inventory(expected_rows: list[dict], root: Path, expected_hash: str, label: str) -> dict:
    expected = {str(row["path"]): row for row in expected_rows}
    if len(expected) != len(expected_rows):
        fail(label + " contains duplicate baseline paths")
    actual_paths = {
        project_relative(path) for path in root.rglob("*") if path.is_file()
    }
    if actual_paths != set(expected):
        fail(label + " path inventory drift: missing=" + repr(sorted(set(expected) - actual_paths))
             + " added=" + repr(sorted(actual_paths - set(expected))))
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
    return {"file_count": len(rows), "inventory_sha256": digest, "files": rows}


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
    actual_union: set[str] = set()
    groups = []
    for group in protected["groups"]:
        actual = scan_protected_group(group)
        wanted = set(group["paths"])
        if actual != wanted:
            fail("protected group inventory drift: " + group["name"]
                 + ": missing=" + repr(sorted(wanted - actual))
                 + " added=" + repr(sorted(actual - wanted)))
        actual_union.update(actual)
        groups.append({"name": group["name"], "file_count": len(actual)})
    if actual_union != set(expected_rows):
        fail("protected union inventory drift")
    rows = []
    for relative in sorted(actual_union, key=str.casefold):
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
    source_root = PROJECT / source["root"]
    return verify_explicit_inventory(
        source["all_files"], source_root, source["inventory_sha256"], "frozen source"
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
    content = PROJECT / "Content"
    for path in sorted(content.rglob("*"), key=lambda item: str(item).casefold()):
        if not path.is_file() or is_inside(path, DEST_DISK):
            continue
        stat = path.stat()
        rows.append({"path": project_relative(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"file_count": len(rows), "metadata_sha256": hashlib.sha256(encoded).hexdigest().upper()}


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
            verified = verify_row_at(root / relative, expected[relative], "failed run")
            rows.append({"path": relative, **verified})
        digest = canonical_inventory_hash(rows)
        if digest != failed_run["inventory_sha256"]:
            fail("failed run canonical inventory drift: " + failed_run["id"])
        output.append({
            "id": failed_run["id"],
            "root": failed_run["root"],
            "file_count": len(rows),
            "inventory_sha256": digest,
        })
    return {"run_count": len(output), "runs": output}


def verify_clean_disposition_archive(
        run_root: Path, disposition: dict, require_destination_absent: bool) -> dict:
    contract = disposition["archive_and_move"]
    receipt_path = run_root / contract["receipt_name"]
    failure_path = run_root / contract["failure_name"]
    if failure_path.exists():
        fail("offline clean disposition emitted a failure receipt")
    if not receipt_path.is_file():
        fail("offline clean disposition PASS receipt is missing")
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

    groups = (
        ("failed_run_archives", failed_expected),
        ("invalid_namespace_archives", package_expected),
    )
    verified_groups = {}
    for receipt_key, expected in groups:
        rows = receipt.get(receipt_key, [])
        if {str(Path(row.get("source_path", "")).resolve()) for row in rows} != set(expected):
            fail("clean disposition archived-source inventory drift: " + receipt_key)
        verified = []
        for row in rows:
            source_path = str(Path(row["source_path"]).resolve())
            wanted = expected[source_path]
            archive_path = PROJECT / row["archived_path"]
            actual = verify_row_at(archive_path, wanted, "clean disposition archive")
            if row.get("archive_read_only") is not True:
                fail("clean disposition archive is not marked immutable: " + row["archived_path"])
            verify_windows_read_only(archive_path, "clean disposition archive")
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

    moved_rows = receipt.get("recoverably_moved_packages", [])
    expected_by_original = {row["path"]: row for row in disposition["invalid_namespace"]["packages"]}
    if {row.get("original_path") for row in moved_rows} != set(expected_by_original):
        fail("recoverably moved package inventory drift")
    moved_verified = []
    for row in moved_rows:
        wanted = expected_by_original[row["original_path"]]
        actual = verify_row_at(PROJECT / row["moved_path"], wanted, "recoverably moved package")
        if row.get("moved_copy_read_only") is not True:
            fail("recoverably moved package is not marked immutable: " + row["moved_path"])
        verify_windows_read_only(PROJECT / row["moved_path"], "recoverably moved package")
        moved_verified.append({"path": row["moved_path"], **actual})

    verify_exact_project_path_inventory(
        run_root / contract["invalid_namespace_move_folder"] / contract["move_target_leaf"],
        {row["moved_path"] for row in moved_rows},
        "recoverably moved invalid namespace",
    )

    if require_destination_absent and (DEST_DISK.exists() or library.does_directory_exist(DEST)):
        fail("invalid namespace is not absent after offline atomic move")
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


def package_file(package_path: str) -> Path:
    return PROJECT / "Content" / Path(package_path.removeprefix("/Game/")).with_suffix(".uasset")


def object_path(package_path: str) -> str:
    return package_path + "." + package_path.rsplit("/", 1)[-1]


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
            fail(f"section-to-material slot index invalid: {mesh.get_name()}:LOD{lod_index}:{section_index}:{slot_index}")
        output.append(slots[slot_index])
    return output


def import_data_contract(mesh: unreal.StaticMesh) -> dict:
    data = mesh.get_editor_property("asset_import_data")
    try:
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
    except Exception as error:
        fail("legacy FBX import settings are unavailable: " + mesh.get_name() + ": " + str(error))
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


def make_lod0_import_task(spec: dict) -> unreal.AssetImportTask:
    lod0 = spec["lods"][0]
    source = PROJECT / lod0["source"]
    if not source.is_file() or sha256(source) != lod0["source_sha256"]:
        fail("LOD0 source hash drift before import: " + str(source))
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": spec["package_path"].rsplit("/", 1)[0],
        "destination_name": spec["asset_name"],
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": False,
        "factory": unreal.FbxFactory(),
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "import_animations": False,
        "create_physics_asset": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "original_import_type": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False,
        "override_full_name": True,
        "auto_compute_lod_distances": False,
        "lod_number": 1,
        "minimum_lod_number": 0,
    })
    options.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True,
        "import_mesh_lods": False,
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "build_nanite": False,
        "reorder_material_to_fbx_order": True,
    })
    task.set_editor_property("options", options)
    return task


def validate_fresh_lod0(
        key: str, spec: dict, baseline: dict, subsystem) -> tuple[unreal.StaticMesh, dict]:
    mesh = library.load_asset(spec["package_path"])
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
        fail("fresh LOD0 object missing/wrong type: " + key)
    if int(mesh.get_num_lods()) != 1:
        fail("fresh LOD0 import unexpectedly created multiple LODs: " + key)
    expected = spec["lods"][0]
    slots = global_slot_names(mesh)
    triangles = int(mesh.get_num_triangles(0))
    uv_channels = int(mesh.get_num_tex_coords(0))
    bounds = lod_bounds(mesh, 0)
    sections = section_slot_names(mesh, subsystem, 0, slots)
    if triangles != int(expected["triangles"]):
        fail(f"fresh LOD0 triangle drift: {key}:{triangles}!={expected['triangles']}")
    if uv_channels != 1 or int(expected["source_uv_layers"]) != 1:
        fail(f"fresh LOD0 one-UV contract drift: {key}:{uv_channels}")
    assert_bounds(
        bounds, expected["expected_unreal_bounds"],
        float(baseline["import_contract"]["bounds_tolerance_cm"]), f"fresh:{key}:LOD0",
    )
    if slots != list(expected["material_slots"]) or sections != list(expected["material_slots"]):
        fail("fresh LOD0 semantic material-slot drift: " + key)
    return mesh, {
        "asset_key": key,
        "object_path": mesh.get_path_name(),
        "lod_count": 1,
        "triangles": triangles,
        "uv_channels": uv_channels,
        "bounds": bounds,
        "global_material_slots": slots,
        "section_material_slots": sections,
        "legacy_import_data": import_data_contract(mesh),
    }


def append_all_custom_lods_legacy(
        meshes: dict, baseline: dict, subsystem, evidence: dict) -> dict:
    previous = int(unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR))
    evidence.update({
        "name": INTERCHANGE_FBX_CVAR,
        "previous_value": previous,
        "disabled_value": None,
        "restored_value": None,
        "set_false_only_around_custom_lod_imports": True,
        "custom_lods_requested": 16,
        "custom_lods_imported": [],
        "restore_attempted_in_finally": False,
    })
    if previous not in (0, 1):
        fail("unexpected Interchange FBX feature flag value: " + str(previous))
    import_error = None
    try:
        unreal.SystemLibrary.execute_console_command(None, INTERCHANGE_FBX_CVAR + " 0")
        disabled = int(unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR))
        evidence["disabled_value"] = disabled
        if disabled != 0:
            fail("could not disable Interchange FBX translator for legacy custom LOD import")
        for key, spec in sorted(baseline["assets"].items()):
            mesh = meshes[key]
            for lod in spec["lods"][1:]:
                lod_index = int(lod["lod"])
                if int(mesh.get_num_lods()) != lod_index:
                    fail(f"fresh append-only LOD precondition failed: {key}:LOD{lod_index}")
                source = PROJECT / lod["source"]
                if not source.is_file() or sha256(source) != lod["source_sha256"]:
                    fail(f"custom LOD source hash drift: {key}:LOD{lod_index}")
                result = subsystem.import_lod(mesh, lod_index, str(source))
                if int(result) != lod_index:
                    fail(f"legacy custom LOD import failed: {key}:LOD{lod_index}:returned={result}")
                unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
                evidence["custom_lods_imported"].append({
                    "asset_key": key,
                    "lod": lod_index,
                    "source": lod["source"],
                    "source_sha256": lod["source_sha256"],
                })
    except Exception as error:
        import_error = error
    finally:
        evidence["restore_attempted_in_finally"] = True
        unreal.SystemLibrary.execute_console_command(None, f"{INTERCHANGE_FBX_CVAR} {previous}")
        evidence["restored_value"] = int(
            unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR)
        )
    if evidence["restored_value"] != previous:
        fail("Interchange FBX feature flag restoration drift: " + repr(evidence))
    if import_error is not None:
        raise import_error
    if len(evidence["custom_lods_imported"]) != 16:
        fail("legacy custom LOD import count drift")
    evidence["status"] = "PASS__INTERCHANGE_FBX_DISABLED_ONLY_FOR_16_LEGACY_CUSTOM_LOD_IMPORTS__RESTORED"
    return evidence


def prepare_mesh_before_screen_phase(
        key: str, spec: dict, baseline: dict, subsystem, materials: dict,
        mesh: unreal.StaticMesh) -> None:
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
        fail("fresh StaticMesh/object path drift: " + key)
    if int(mesh.get_num_lods()) != 3:
        fail("fresh three-LOD precondition drift: " + key)

    nanite = subsystem.get_nanite_settings(mesh)
    nanite.set_editor_property("enabled", False)
    subsystem.set_nanite_settings(mesh, nanite, True)
    if (int(subsystem.get_simple_collision_count(mesh)) != 0
            or int(subsystem.get_convex_collision_count(mesh)) != 0):
        if not subsystem.remove_collisions(mesh):
            fail("could not remove presentation-only simple collision: " + key)
    body = mesh.get_editor_property("body_setup")
    if body is None:
        fail("BodySetup missing: " + key)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)

    expected_global_slots = list(spec["lods"][0]["material_slots"])
    slots = global_slot_names(mesh)
    if slots != expected_global_slots:
        fail("LOD0/global semantic material-slot order drift: " + key + ": " + repr(slots))
    for index, slot_name in enumerate(slots):
        material = materials.get(slot_name)
        if material is None:
            fail("unbound semantic material slot: " + key + ":" + slot_name)
        mesh.set_material(index, material)
    if not library.save_loaded_asset(mesh, only_if_is_dirty=False):
        fail("pre-screen fresh StaticMesh save failed: " + key)


def persist_all_manual_screen_sizes(meshes: dict, baseline: dict, subsystem) -> dict:
    # Every operation that can rebuild any mesh is complete before this function.
    # Pass one is saved and globally compiled; pass two is then the final edit/save
    # phase for all meshes, with no subsequent compilation or PostEditChange call.
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    screen_sizes = [float(value) for value in baseline["import_contract"]["lod_screen_sizes"]]
    expected = [round(value, 6) for value in screen_sizes]
    if int(baseline["import_contract"]["screen_size_persistence_passes"]) != 2:
        fail("screen-size persistence pass-count contract drift")
    output = {key: {"passes": []} for key in meshes}

    for key, mesh in sorted(meshes.items()):
        if not subsystem.set_lod_screen_sizes(mesh, screen_sizes):
            fail("first manual LOD screen-size assignment failed: " + key)
        immediate = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
        auto = bool(mesh.is_lod_screen_size_auto_computed())
        if immediate != expected or auto:
            fail("first LOD screen-size write/readback drift: " + key + ":" + repr(immediate))
        if not library.save_loaded_asset(mesh, only_if_is_dirty=False):
            fail("first screen-size persistence save failed: " + key)
        output[key]["passes"].append({
            "pass": 1,
            "immediate_readback": immediate,
            "immediate_auto_compute": auto,
        })

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    for key, mesh in sorted(meshes.items()):
        readback = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
        auto = bool(mesh.is_lod_screen_size_auto_computed())
        output[key]["passes"][0].update({
            "post_save_compile_readback_before_reapply": readback,
            "post_save_compile_auto_compute_before_reapply": auto,
        })

    for key, mesh in sorted(meshes.items()):
        if not subsystem.set_lod_screen_sizes(mesh, screen_sizes):
            fail("final manual LOD screen-size assignment failed: " + key)
        immediate = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
        auto = bool(mesh.is_lod_screen_size_auto_computed())
        if immediate != expected or auto:
            fail("final pre-save LOD screen-size drift: " + key + ":" + repr(immediate))
        if not library.save_loaded_asset(mesh, only_if_is_dirty=False):
            fail("final screen-size persistence save failed: " + key)
        final = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
        final_auto = bool(mesh.is_lod_screen_size_auto_computed())
        if final != expected or final_auto:
            fail("final LOD screen-size persistence drift: " + key + ":" + repr(final))
        output[key]["passes"].append({
            "pass": 2,
            "immediate_readback": immediate,
            "immediate_auto_compute": auto,
            "post_final_save_readback": final,
            "post_final_save_auto_compute": final_auto,
        })
        output[key].update({
            "write_order": baseline["import_contract"]["screen_size_write_order"],
            "global_final_phase_after_all_mesh_preparation": True,
            "no_build_after_final_set": True,
            "fresh_process_readback_required": True,
        })
    return output


def measure_final_mesh(
        key: str, spec: dict, baseline: dict, subsystem,
        mesh: unreal.StaticMesh, screen_write_evidence: dict) -> dict:
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
        fail("final StaticMesh/object path drift: " + key)
    if int(mesh.get_num_lods()) != 3:
        fail("final three-LOD precondition drift: " + key)
    body = mesh.get_editor_property("body_setup")
    if body is None:
        fail("final BodySetup missing: " + key)
    slots = global_slot_names(mesh)
    expected_global_slots = list(spec["lods"][0]["material_slots"])
    if slots != expected_global_slots:
        fail("final global semantic material-slot drift: " + key)

    screen_sizes = [float(value) for value in baseline["import_contract"]["lod_screen_sizes"]]
    expected_screen_sizes = [round(value, 6) for value in screen_sizes]
    actual_screen_sizes = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
    auto_compute_screen_sizes = bool(mesh.is_lod_screen_size_auto_computed())
    if actual_screen_sizes != expected_screen_sizes or auto_compute_screen_sizes:
        fail("final LOD screen-size persistence drift: " + key + ":" + repr(actual_screen_sizes))
    if (screen_write_evidence.get("global_final_phase_after_all_mesh_preparation") is not True
            or len(screen_write_evidence.get("passes", [])) != 2):
        fail("global final screen-size phase evidence drift: " + key)

    lod_count = int(mesh.get_num_lods())
    if lod_count != 3:
        fail("LOD count drift: " + key + ":" + str(lod_count))

    tolerance = float(baseline["import_contract"]["bounds_tolerance_cm"])
    lod_rows = []
    for lod_index, expected_lod in enumerate(spec["lods"]):
        triangles = int(mesh.get_num_triangles(lod_index))
        if triangles != int(expected_lod["triangles"]):
            fail(f"triangle contract drift: {key}:LOD{lod_index}:{triangles}!={expected_lod['triangles']}")
        bounds = lod_bounds(mesh, lod_index)
        assert_bounds(bounds, expected_lod["expected_unreal_bounds"], tolerance, f"{key}:LOD{lod_index}")
        section_slots = section_slot_names(mesh, subsystem, lod_index, slots)
        if section_slots != list(expected_lod["material_slots"]):
            fail(f"per-LOD semantic section/material order drift: {key}:LOD{lod_index}:{section_slots}")
        uv_channels = int(mesh.get_num_tex_coords(lod_index))
        expected_uv_channels = int(baseline["import_contract"]["expected_uv_channels_per_lod"])
        if uv_channels != expected_uv_channels:
            fail(f"UV channel contract drift: {key}:LOD{lod_index}:{uv_channels}!={expected_uv_channels}")
        lod_rows.append({
            "lod": lod_index,
            "triangles": triangles,
            "vertices": int(mesh.get_num_vertices(lod_index)),
            "uv_channels": uv_channels,
            "bounds": bounds,
            "expected_bounds": expected_lod["expected_unreal_bounds"],
            "section_material_slots": section_slots,
            "source": expected_lod["source"],
            "source_sha256": expected_lod["source_sha256"],
        })
    triangle_order = [row["triangles"] for row in lod_rows]
    if not triangle_order[0] > triangle_order[1] > triangle_order[2]:
        fail("strict per-asset triangle monotonicity drift: " + key + ":" + repr(triangle_order))

    simple = int(subsystem.get_simple_collision_count(mesh))
    convex = int(subsystem.get_convex_collision_count(mesh))
    trace_flag = str(body.get_editor_property("collision_trace_flag"))
    nanite_enabled = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    if simple != 0 or convex != 0 or "SIMPLE_AS_COMPLEX" not in trace_flag.upper() or nanite_enabled:
        fail("presentation collision/Nanite contract drift: " + key)
    bound_materials = [
        mesh.get_material(index).get_path_name() if mesh.get_material(index) else None
        for index in range(len(slots))
    ]
    expected_materials = [object_path(baseline["import_contract"]["material_bindings"][slot]) for slot in slots]
    if bound_materials != expected_materials:
        fail("semantic presentation-material binding drift: " + key)
    package = package_file(spec["package_path"])
    if not package.is_file():
        fail("saved package missing: " + str(package))
    return {
        "asset_key": key,
        "package_path": spec["package_path"],
        "object_path": mesh.get_path_name(),
        "package_file": project_relative(package),
        "package_bytes": package.stat().st_size,
        "package_sha256": sha256(package),
        "initial_lod_count": 0,
        "lod0_created_fresh": True,
        "missing_lods_appended": [1, 2],
        "existing_lods_reimported": [],
        "lod_count": lod_count,
        "lod_screen_sizes": actual_screen_sizes,
        "lod_screen_size_auto_computed": auto_compute_screen_sizes,
        "screen_size_persistence": {
            **screen_write_evidence,
        },
        "lods": lod_rows,
        "strict_triangle_monotonicity": True,
        "global_material_slots": slots,
        "bound_materials": bound_materials,
        "simple_collision_count": simple,
        "convex_collision_count": convex,
        "collision_trace_flag": trace_flag,
        "nanite_enabled": nanite_enabled,
        "legacy_import_data": import_data_contract(mesh),
    }


def prior_success_receipts() -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    results = []
    for path in AUDIT_ROOT.rglob(IMPORT_RECEIPT_NAME):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if str(payload.get("status", "")).startswith("PASS__"):
            results.append(str(path))
    return sorted(results)


def main() -> None:
    run_root = resolve_run_root()
    receipt = run_root / IMPORT_RECEIPT_NAME
    failure_receipt = run_root / IMPORT_FAILURE_NAME
    evidence = {
        "$schema": "lineboss/audit/bodyshop-robot-native-v001-unreal-import/v1",
        "generated_utc": now(),
        "process_id": os.getpid(),
        "destination_namespace": DEST,
        "writes_authorized": [str(DEST_DISK), str(run_root)],
        "map_changes": [],
        "config_changes": [],
        "source_changes": [],
        "runtime_binding_changes": [],
        "promotion_authorized": False,
        "clean_disposition_mode": DISPOSITION_MODE_TOKEN,
        "fresh_destination_import_only": True,
        "replace_existing": False,
        "reuse_existing_packages": False,
    }
    content_before = None
    protected_before = None
    source_before = None
    failed_runs_before = None
    disposition_archive_before = None
    fresh_lod0_validation = None
    cvar_evidence = {}
    try:
        if receipt.exists() or failure_receipt.exists():
            fail("clean import run directory already contains an import result")
        baseline = load_baseline()
        disposition = load_disposition_contract()
        evidence["baseline_sha256"] = sha256(BASELINE)
        evidence["baseline_status"] = baseline["status"]
        evidence["clean_disposition_contract_sha256"] = sha256(DISPOSITION_CONTRACT)
        evidence["clean_disposition_contract_status"] = disposition["status"]
        source_before = verify_source(baseline)
        protected_before = verify_protected(baseline)
        active_binding_before = verify_active_body_shop_binding(baseline)
        failed_runs_before = verify_failed_runs(disposition)
        evidence["source_before"] = source_before
        evidence["protected_before"] = protected_before
        evidence["active_body_shop_binding_before"] = active_binding_before
        evidence["failed_runs_before"] = failed_runs_before
        if prior_success_receipts():
            fail("one-shot lane already has a PASS receipt: " + repr(prior_success_receipts()))
        disposition_archive_before = verify_clean_disposition_archive(
            run_root, disposition, require_destination_absent=True
        )
        evidence["pre_clean_import_disposition"] = disposition_archive_before
        if DEST_DISK.exists() or library.does_directory_exist(DEST):
            fail("fresh destination is not absent before import")
        if namespace_disk_inventory():
            fail("fresh destination disk inventory is not empty")
        preexisting_registry = list(library.list_assets(DEST, recursive=True, include_folder=False))
        if preexisting_registry:
            fail("fresh destination asset registry is not empty: " + repr(preexisting_registry))
        for spec in baseline["assets"].values():
            if library.does_asset_exist(spec["package_path"]):
                fail("fresh object path already exists: " + spec["package_path"])

        materials = {}
        for slot, package_path in baseline["import_contract"]["material_bindings"].items():
            material = library.load_asset(package_path)
            if not isinstance(material, unreal.MaterialInterface):
                fail("protected presentation material missing/wrong type: " + package_path)
            materials[slot] = material
        content_before = content_metadata_snapshot()
        if content_before != disposition["invalid_namespace"]["outside_destination_content"]:
            fail("Content outside destination differs from the incident-bound snapshot")
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None:
            fail("StaticMeshEditorSubsystem unavailable; use full UnrealEditor -ExecutePythonScript")

        expected_registry = {spec["package_path"] for spec in baseline["assets"].values()}
        tasks = []
        task_keys = []
        for key, spec in sorted(baseline["assets"].items()):
            package = package_file(spec["package_path"])
            if package.exists():
                fail("fresh LOD0 package appeared before import task: " + key)
            tasks.append(make_lod0_import_task(spec))
            task_keys.append(key)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        evidence["lod0_import_tasks"] = [
            {
                "asset_key": key,
                "imported_object_paths": [str(path) for path in task.imported_object_paths],
                "replace_existing": False,
                "factory": "FbxFactory",
            }
            for key, task in zip(task_keys, tasks)
        ]
        registry_lod0 = {
            str(path).rsplit(".", 1)[0]
            for path in library.list_assets(DEST, recursive=True, include_folder=False)
        }
        if registry_lod0 != expected_registry:
            fail("fresh LOD0 registry is not the exact eight-package set: " + repr(sorted(registry_lod0)))

        loaded_meshes = {}
        fresh_lod0_validation = {}
        for key, spec in sorted(baseline["assets"].items()):
            mesh, row = validate_fresh_lod0(key, spec, baseline, subsystem)
            loaded_meshes[key] = mesh
            fresh_lod0_validation[key] = row
        evidence["fresh_lod0_validation"] = fresh_lod0_validation

        append_all_custom_lods_legacy(
            loaded_meshes, baseline, subsystem, cvar_evidence
        )
        evidence["interchange_fbx_legacy_custom_lod_guard"] = cvar_evidence

        for key, spec in sorted(baseline["assets"].items()):
            prepare_mesh_before_screen_phase(
                key, spec, baseline, subsystem, materials, loaded_meshes[key],
            )
        screen_phase = persist_all_manual_screen_sizes(
            loaded_meshes, baseline, subsystem
        )
        evidence["global_final_screen_size_phase"] = screen_phase

        meshes = {}
        for key, spec in sorted(baseline["assets"].items()):
            meshes[key] = measure_final_mesh(
                key, spec, baseline, subsystem, loaded_meshes[key], screen_phase[key],
            )

        registry = {
            str(path).rsplit(".", 1)[0]
            for path in library.list_assets(DEST, recursive=True, include_folder=False)
        }
        if registry != expected_registry:
            fail("exact eight-asset registry inventory drift: " + repr(sorted(registry)))
        disk = namespace_disk_inventory()
        expected_disk = {spec["disk_path"] for spec in baseline["assets"].values()}
        if set(disk) != expected_disk:
            fail("exact eight-package disk inventory drift: " + repr(sorted(disk)))

        source_after = verify_source(baseline)
        protected_after = verify_protected(baseline)
        active_binding_after = verify_active_body_shop_binding(baseline)
        failed_runs_after = verify_failed_runs(disposition)
        disposition_archive_after = verify_clean_disposition_archive(
            run_root, disposition, require_destination_absent=False
        )
        content_after = content_metadata_snapshot()
        if source_after != source_before:
            fail("frozen source changed during import")
        if protected_after != protected_before:
            fail("protected artifact snapshot changed during import")
        if active_binding_after != active_binding_before:
            fail("active Body Shop binding changed during import")
        if failed_runs_after != failed_runs_before:
            fail("one or both failed run trees changed during clean import")
        if disposition_archive_after != disposition_archive_before:
            fail("clean disposition archive changed during import")
        if content_after != content_before:
            fail("Content outside the isolated destination changed during import")
        if int(unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR)) != int(
                cvar_evidence["previous_value"]):
            fail("Interchange FBX feature flag changed after restoration")

        evidence.update({
            "status": (
                "PASS__INCIDENT_ARCHIVED_AND_INVALID_NAMESPACE_MOVED__FRESH_8_ASSET_"
                "3_LOD_HIGH_ELBOW_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001_IMPORT"
            ),
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "source_after": source_after,
            "protected_after": protected_after,
            "active_body_shop_binding_after": active_binding_after,
            "failed_runs_after": failed_runs_after,
            "clean_disposition_archive_after": disposition_archive_after,
            "outside_destination_content_before": content_before,
            "outside_destination_content_after": content_after,
            "assets": meshes,
            "asset_registry_packages": sorted(registry),
            "namespace_disk_files": disk,
            "asset_count": len(meshes),
            "lod_count_per_asset": 3,
            "source_fbx_count": 24,
            "clean_import_proof": {
                "failed_run_count": len(disposition["failed_runs"]),
                "both_failed_runs_hash_verified": True,
                "invalid_package_count_archived_and_moved": 8,
                "content_namespace_absent_before_unreal_mutation": True,
                "fresh_lod0_packages_created": 8,
                "replace_existing": False,
                "reuse_existing_packages": False,
                "existing_lods_reimported": 0,
                "missing_lods_appended": sum(len(row["missing_lods_appended"]) for row in meshes.values()),
                "strict_per_asset_triangle_monotonicity": all(
                    row["strict_triangle_monotonicity"] for row in meshes.values()
                ),
                "one_uv_per_asset_lod": all(
                    lod["uv_channels"] == 1 for row in meshes.values() for lod in row["lods"]
                ),
                "interchange_fbx_cvar": cvar_evidence,
                "screen_size_write_order": baseline["import_contract"]["screen_size_write_order"],
                "screen_size_persistence_passes": baseline["import_contract"]["screen_size_persistence_passes"],
            },
            "material_policy": "IMPORT_NONE__BIND_PROTECTED_BODYSHOP_PRESENTATION_MATERIALS_V002",
            "collision_policy": baseline["import_contract"]["collision"],
            "fresh_process_validator_required": True,
            "automatic_cleanup": "NOT_PERFORMED__FRESH_PACKAGES_AND_ALL_INCIDENT_EVIDENCE_PRESERVED",
            "failures": [],
        })
        write_exclusive_json(receipt, evidence)
        unreal.log("LINE_BOSS_BODYSHOP_ROBOT_NATIVE_V001_CLEAN_FRESH_IMPORT_PASS")
        print(json.dumps(evidence, indent=2))
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        record = dict(evidence)
        record.update({
            "status": "FAIL_CLOSED__BODYSHOP_ROBOT_NATIVE_V001_INCIDENT_BOUND_CLEAN_IMPORT",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "source_before": source_before,
            "protected_before": protected_before,
            "failed_runs_before": failed_runs_before,
            "pre_clean_import_disposition": disposition_archive_before,
            "fresh_lod0_validation": fresh_lod0_validation,
            "interchange_fbx_legacy_custom_lod_guard": cvar_evidence,
            "outside_destination_content_before": content_before,
            "namespace_files_preserved_for_incident_review": namespace_disk_inventory(),
            "automatic_cleanup": "NOT_PERFORMED__PARTIAL_FRESH_IMPORT_AND_ALL_ARCHIVES_PRESERVED",
            "failure_next_action": (
                "Do not rerun. Archive this failed clean-import run and review the exact current namespace; "
                "the prior invalid namespace remains recoverable under this run's Saved/Audits archive."
            ),
        })
        write_exclusive_json(failure_receipt, record)
        unreal.log_error("LINE_BOSS_BODYSHOP_ROBOT_NATIVE_V001_IMPORT_FAIL: " + str(error))
        print(json.dumps(record, indent=2))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


if __name__ == "__main__":
    main()
