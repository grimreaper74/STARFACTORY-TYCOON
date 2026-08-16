"""Freeze the incident-bound disposition authority for a clean v001 import.

Pure CPython only: this script never launches Unreal and never changes Content.
It proves the exact identity of both failed runs and all eight invalid packages.
The separate archive step is the only component authorized to copy those bytes
and atomically move the invalid namespace into Saved/Audits before a fresh import.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUTPUT = PROJECT / "Scripts/body_shop_robot_native_unreal_recovery_contract_v001.json"
BASELINE = PROJECT / "Scripts/body_shop_robot_native_unreal_import_baseline_v001.json"
EXPECTED_BASELINE_SHA256 = "D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31"
DESTINATION = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"
DESTINATION_NAMESPACE = "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"
DISPOSITION_MODE_TOKEN = (
    "ARCHIVE_TWO_FAILED_RUNS_MOVE_INVALID_NAMESPACE_AND_CLEAN_IMPORT_"
    "HIGH_ELBOW_MONOTONIC_V001_ONCE"
)

FAILED_RUNS = (
    {
        "id": "screen_size_failure",
        "root": "Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane/20260814T191133Z-7adb326b",
        "file_count": 7,
        "total_bytes": 387684,
        "inventory_sha256": "F25A877C4F0388F7468E848FFE60CD1D8F627D215FF219004E0FBD7CA6DE04BA",
        "failure_status": "FAIL_CLOSED__BODYSHOP_ROBOT_NATIVE_V001_UNREAL_IMPORT",
        "failure_error": (
            "BODYSHOP_ROBOT_NATIVE_UNREAL_IMPORT_V001_FAIL: "
            "LOD screen-size persistence drift: Base:[0.0, 0.0, 0.0]"
        ),
        "lane_status": "FAIL_CLOSED__BODYSHOP_ROBOT_NATIVE_V001_UNREAL_IMPORT_LANE",
        "acknowledgement": "IMPORT_HIGH_ELBOW_BODYSHOP_ROBOT_NATIVE_V001_ONCE",
        "baseline_sha256": "2809D2C3950A21CDC7EE19A64C62E4D7F7C7E50277A5377ADA5E36EDF78AC19B",
    },
    {
        "id": "uv_precondition_failure",
        "root": "Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane/20260814T193800Z-f02f2baa",
        "file_count": 27,
        "total_bytes": 1198787,
        "inventory_sha256": "5AD7F15B28E41B8FC4023B6E5EECD48ECBDC0E20951AC930B5C3E56029111C3E",
        "failure_status": "FAIL_CLOSED__BODYSHOP_ROBOT_NATIVE_V001_HASH_GUARDED_RECOVERY",
        "failure_error": (
            "BODYSHOP_ROBOT_NATIVE_UNREAL_IMPORT_V001_FAIL: "
            "partial recovery UV precondition drift: Base:LOD1"
        ),
        "lane_status": "FAIL_CLOSED__BODYSHOP_ROBOT_NATIVE_V001_HASH_GUARDED_RECOVERY_LANE",
        "acknowledgement": "RECOVER_EXACT_FAILED_HIGH_ELBOW_BODYSHOP_ROBOT_NATIVE_V001_ONCE",
        "baseline_sha256": "3F9EAA19BDF88AF4D3E70AC807A0E5C83D64E09CF15F724B2166D39A017A5304",
        "recovery_contract_sha256": "F41EC783FBDE2208E02FB841ECA1D93F80BC221FD412ED7DD558B10E4F86B75B",
    },
)

EXPECTED_INVALID_PACKAGES = {
    "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_Base_v001.uasset":
        (249391, "7E1DB3F376CF83B245AD6C55718F7B6076D3A7EC53B5D34177BA46EE3C7E8B49", "Base", 3),
    "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J1_v001.uasset":
        (27162, "D08CC68E2073C9247E59BC596D5EA8563A49869568EAA17613F00C4E6D6C9AD3", "J1", 1),
    "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J2_v001.uasset":
        (24694, "8DE689EB5BB2087EC08570E23E7D1BA18E1591DE37A534EE1EB0B2664D1300B2", "J2", 1),
    "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J3_v001.uasset":
        (23880, "4FA06895F71B11572DC4798E31B7D666F55A96CF81F48F69D5329D57E8718F39", "J3", 1),
    "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J4_v001.uasset":
        (21099, "CCBF85A3C3F3DEB3EACADC9E056D8853663A58E90DCA7F8EB85E13C296E1994B", "J4", 1),
    "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J5_v001.uasset":
        (19559, "9630E512D7BED3DA0A6670952E4745C8BA1DD907B5EE436764BD80C7A8CF6FF0", "J5", 1),
    "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J6_v001.uasset":
        (21521, "FCF17F4485A698E5FBBB92639123D78A01A5F01BE0ABF7A543CADF7B95A34326", "J6", 1),
    "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.uasset":
        (29064, "E66AC3DAD4AA8C35D9052F281D208EA6481D78305E5B896FAA0331848946D64A", "CGun", 1),
}

EXPECTED_OUTSIDE_CONTENT = {
    "file_count": 15297,
    "metadata_sha256": "0F74E99F24B4CE90EEA8D4C24577EC6EE203FC00EDC0DBD2408EED85E93E39BB",
}

ENGINE_EVIDENCE = (
    {
        "path": r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Editor\StaticMeshEditor\Private\StaticMeshEditorSubsystem.cpp",
        "bytes": 89363,
        "sha256": "8C9E71501320F6EF9CB4A3D6AB668EEE6184230A2F85A8B9E3748E1831CA6760",
        "tokens": (
            "StaticMesh->SetAutoComputeLODScreenSize(false)",
            "RenderData->ScreenSize[i].Default = ScreenSizeForLOD",
            "StaticMesh->GetSourceModel(i).ScreenSize = ScreenSizeForLOD",
        ),
        "line_contract": "986-1096__AUTHORITATIVE_GET_SET_SCREEN_SIZES",
    },
    {
        "path": r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\Engine\Private\StaticMesh.cpp",
        "bytes": 380614,
        "sha256": "19AA05147F931D774F68BB3F4A921D5B659677D34B5DB821291E12788FAD3871",
        "tokens": (
            "int32 UStaticMesh::GetNumTexCoords(int32 LODIndex) const",
            "GetRenderData()->LODResources[LODIndex].GetNumTexCoords()",
        ),
        "line_contract": "5012-5019__NONZERO_LOD_UV_READS_RENDER_DATA",
    },
    {
        "path": r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Editor\UnrealEd\Private\FbxMeshUtils.cpp",
        "bytes": 50723,
        "sha256": "8776725B682A1355C8CEF2C49C757BAD5E4203E3C66136D4908E1D3F49E76D4E",
        "tokens": (
            "bool ImportStaticMeshLOD( UStaticMesh* BaseStaticMesh",
            "InterchangeManager.CanTranslateSourceData(SourceData)",
            "UInterchangeMeshUtilities::ImportCustomLod",
            "UE_LOGF(LogExportMeshUtils, Log, \"Fbx LOD loading\")",
        ),
        "line_contract": "189-279__INTERCHANGE_OR_LEGACY_CUSTOM_LOD_BRANCH",
    },
    {
        "path": r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Interchange\Runtime\Source\Import\Private\Fbx\InterchangeFbxTranslator.cpp",
        "bytes": 38457,
        "sha256": "D93D22384C6E55AF1A4EC1FF2B3F5E55936697A943820F9437ED4B5F922DD250",
        "tokens": (
            "Interchange.FeatureFlags.Import.FBX",
            "if (GInterchangeEnableFBXImport)",
            "return TArray<FString>{};",
        ),
        "line_contract": "34-40_AND_260-269__FALSE_REMOVES_FBX_TRANSLATOR_FORMAT",
    },
    {
        "path": "Intermediate/PythonStub/unreal.py",
        "bytes": 36751726,
        "sha256": "213EB7BDD30D2E2DAE622A23A01D0BB519C6B87CC65035E46DE0D2C1FD3B1D25",
        "tokens": ("def set_lod_screen_sizes", "def get_lod_screen_sizes", "def import_lod"),
        "line_contract": "648978-649491__PYTHON_STATIC_MESH_EDITOR_API",
    },
)


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_ROBOT_NATIVE_CLEAN_DISPOSITION_FREEZE_V001_FAIL: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT.resolve()).as_posix()


def file_row(path: Path, reported_path: str | None = None) -> dict:
    if not path.is_file():
        fail("required incident input is missing: " + str(path))
    stat = path.stat()
    return {
        "path": reported_path if reported_path is not None else project_relative(path),
        "bytes": stat.st_size,
        "sha256": sha256(path),
    }


def canonical_inventory_hash(rows: list[dict]) -> str:
    canonical = [
        {"path": item["path"], "bytes": int(item["bytes"]), "sha256": item["sha256"]}
        for item in sorted(rows, key=lambda item: item["path"].casefold())
    ]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as error:
        fail(f"could not parse {path}: {error}")


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def content_metadata_snapshot() -> dict:
    rows = []
    for path in sorted((PROJECT / "Content").rglob("*"), key=lambda item: str(item).casefold()):
        if not path.is_file() or is_inside(path, DESTINATION):
            continue
        stat = path.stat()
        rows.append({"path": project_relative(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"file_count": len(rows), "metadata_sha256": hashlib.sha256(encoded).hexdigest().upper()}


def freeze_failed_run(spec: dict) -> dict:
    root = PROJECT / spec["root"]
    if not root.is_dir():
        fail("failed run root is missing: " + str(root))
    rows = []
    for path in sorted(root.rglob("*"), key=lambda item: str(item).casefold()):
        if path.is_file():
            rows.append(file_row(path, path.relative_to(root).as_posix()))
    if (len(rows) != spec["file_count"]
            or sum(row["bytes"] for row in rows) != spec["total_bytes"]
            or canonical_inventory_hash(rows) != spec["inventory_sha256"]):
        fail("failed run recursive inventory drift: " + spec["id"])

    failure = load_json(root / "import_failure_v001.json")
    summary = load_json(root / "lane_summary_v001.json")
    if (failure.get("status") != spec["failure_status"]
            or failure.get("error") != spec["failure_error"]
            or failure.get("baseline_sha256") != spec["baseline_sha256"]
            or failure.get("destination_namespace") != DESTINATION_NAMESPACE
            or failure.get("automatic_cleanup") !=
               "NOT_PERFORMED__PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW"):
        fail("failed importer semantic identity drift: " + spec["id"])
    if (summary.get("status") != spec["lane_status"]
            or summary.get("acknowledgement") != spec["acknowledgement"]
            or summary.get("validation_process") is not None
            or summary.get("validation_receipt") is not None):
        fail("failed lane semantic identity drift: " + spec["id"])
    if spec.get("recovery_contract_sha256") is not None:
        if failure.get("recovery_contract_sha256") != spec["recovery_contract_sha256"]:
            fail("failed recovery contract identity drift: " + spec["id"])
        archive = summary.get("archive_receipt") or {}
        if (archive.get("status") !=
                "PASS__FAILED_EVIDENCE_AND_EXACT_PARTIAL_NAMESPACE_ARCHIVED_BEFORE_RECOVERY"):
            fail("second failed run does not contain its PASS pre-recovery archive receipt")
    return {
        "id": spec["id"],
        "root": spec["root"],
        "file_count": len(rows),
        "total_bytes": sum(row["bytes"] for row in rows),
        "inventory_sha256": canonical_inventory_hash(rows),
        "files": rows,
        "failure_status": spec["failure_status"],
        "failure_error": spec["failure_error"],
        "lane_status": spec["lane_status"],
        "acknowledgement": spec["acknowledgement"],
    }


def build_payload() -> dict:
    if PROJECT.resolve() != Path.cwd().resolve():
        fail("run from the exact project root: " + str(PROJECT))
    if sha256(BASELINE) != EXPECTED_BASELINE_SHA256:
        fail("clean import baseline hash drift")
    baseline = load_json(BASELINE)
    source = baseline.get("source", {})
    contract = baseline.get("import_contract", {})
    if (baseline.get("status") !=
            "FROZEN__HIGH_ELBOW_STRICT_MONOTONIC_BODYSHOP_ROBOT_NATIVE_V001_CLEAN_UNREAL_IMPORT_BASELINE"
            or source.get("freeze_status") !=
            "FROZEN__HIGH_ELBOW__STRICT_MONOTONIC_LODS__ONE_UV_LAYER__SOURCEASSETS_ONLY__"
            "50_EXPORT_ROUNDTRIPS_PASS__UNREAL_IMPORT_PENDING"
            or contract.get("strict_per_asset_triangle_order") != "LOD0_GT_LOD1_GT_LOD2"
            or contract.get("expected_uv_channels_per_lod") != 1
            or contract.get("custom_lod_route") !=
               "LEGACY_FBX_WITH_INTERCHANGE_FEATURE_FLAG_TEMPORARILY_DISABLED"):
        fail("baseline is not the corrected clean-import authority")

    failed_runs = [freeze_failed_run(spec) for spec in FAILED_RUNS]

    actual_paths = {project_relative(path) for path in DESTINATION.rglob("*") if path.is_file()}
    if actual_paths != set(EXPECTED_INVALID_PACKAGES):
        fail("exact invalid namespace path inventory drift")
    packages = []
    for relative in sorted(EXPECTED_INVALID_PACKAGES, key=str.casefold):
        expected_bytes, expected_hash, key, lod_count = EXPECTED_INVALID_PACKAGES[relative]
        actual = file_row(PROJECT / relative)
        if actual["bytes"] != expected_bytes or actual["sha256"] != expected_hash:
            fail("invalid package drift: " + relative)
        actual.update({"asset_key": key, "observed_lod_count": lod_count})
        packages.append(actual)

    engine_rows = []
    for expected in ENGINE_EVIDENCE:
        raw_path = expected["path"]
        path = Path(raw_path) if Path(raw_path).is_absolute() else PROJECT / raw_path
        actual = file_row(path, raw_path)
        if actual["bytes"] != expected["bytes"] or actual["sha256"] != expected["sha256"]:
            fail("installed UE 5.8 evidence drift: " + raw_path)
        text = path.read_text(encoding="utf-8-sig")
        missing = [token for token in expected["tokens"] if token not in text]
        if missing:
            fail(f"installed UE 5.8 evidence tokens missing in {raw_path}: {missing!r}")
        actual["line_contract"] = expected["line_contract"]
        engine_rows.append(actual)

    outside_content = content_metadata_snapshot()
    if outside_content != EXPECTED_OUTSIDE_CONTENT:
        fail("Content outside the invalid namespace changed since incident freeze")

    assets = baseline.get("assets", {})
    if set(assets) != {"Base", "CGun", "J1", "J2", "J3", "J4", "J5", "J6"}:
        fail("baseline asset contract drift")
    if any([row["source_uv_layers"] for row in asset["lods"]] != [1, 1, 1]
           for asset in assets.values()):
        fail("corrected authority does not prove one UV on every source LOD")

    return {
        "$schema": "lineboss/bodyshop-robot-native-v001-clean-import-disposition-contract/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "FROZEN__TWO_FAILED_RUNS_AND_EXACT_INVALID_NAMESPACE__"
            "ARCHIVE_AND_ATOMIC_MOVE__CLEAN_IMPORT_ONLY"
        ),
        "project_root": str(PROJECT),
        "disposition_mode_token": DISPOSITION_MODE_TOKEN,
        "baseline": {"path": project_relative(BASELINE), "sha256": EXPECTED_BASELINE_SHA256},
        "failed_runs": failed_runs,
        "invalid_namespace": {
            "namespace": DESTINATION_NAMESPACE,
            "disk_path": project_relative(DESTINATION),
            "package_count": len(packages),
            "packages": packages,
            "inventory_sha256": canonical_inventory_hash(packages),
            "outside_destination_content": outside_content,
        },
        "diagnosis": {
            "first_failure": "SCREEN_SIZE_WRITE_WAS_INVALIDATED_BY_LATER_REBUILD",
            "second_failure": "INTERCHANGE_CUSTOM_LOD_LOST_BASE_LOD1_UV_RENDER_DATA",
            "source_uv_evidence": "CORRECTED_AUTHORITY_AND_EXACT_FBX_HAVE_ONE_UV_PER_ASSET_LOD",
            "ue_uv_query_evidence": "USTATICMESH_GETNUMTEXCOORDS_READS_REQUESTED_RENDER_LOD",
            "custom_lod_fix": (
                "CAPTURE_INTERCHANGE_FBX_CVAR__SET_0_ONLY_AROUND_ALL_16_CUSTOM_LOD_IMPORTS__"
                "RESTORE_IN_FINALLY__VERIFY_RESTORED"
            ),
            "screen_fix": (
                "FINISH_ALL_ASSET_COMPILATION__SET_SAVE_COMPILE__REAPPLY_SET_SAVE__"
                "FRESH_PROCESS_READBACK"
            ),
            "superseding_source": (
                "HIGH_ELBOW__STRICT_PER_ASSET_LOD0_GT_LOD1_GT_LOD2__ONE_UV_LAYER"
            ),
            "installed_engine_evidence": engine_rows,
        },
        "archive_and_move": {
            "receipt_name": "pre_clean_import_disposition_receipt_v001.json",
            "failure_name": "pre_clean_import_disposition_failure_v001.json",
            "failed_runs_archive_folder": "failed_runs_byte_archive",
            "invalid_namespace_copy_folder": "invalid_namespace_byte_archive",
            "invalid_namespace_move_folder": "invalid_namespace_recoverable_move",
            "copy_policy": "CREATE_NEW_EXCLUSIVE_FILES__VERIFY_BYTES_AND_SHA256",
            "move_policy": "SAME_VOLUME_ATOMIC_DIRECTORY_RENAME__NEVER_DELETE",
            "archive_files_marked_windows_read_only": True,
            "move_target_leaf": "BodyShopRobotNative_v001",
            "destination_must_be_absent_after_move": True,
        },
        "fresh_import": {
            "destination_must_be_absent_before_unreal_process": True,
            "asset_registry_must_report_all_eight_object_paths_absent": True,
            "replace_existing": False,
            "reuse_existing_packages": False,
            "lod0_packages_created": 8,
            "legacy_custom_lods_appended": 16,
            "existing_lods_reimported": 0,
        },
        "policy": {
            "one_shot_clean_import": True,
            "archive_both_failed_runs_before_unreal": True,
            "archive_invalid_packages_before_move": True,
            "content_namespace_move_authorized": True,
            "content_package_delete_authorized": False,
            "automatic_failure_cleanup": False,
            "maps_source_config_saves_and_content_outside_destination_writable": False,
            "failure_must_leave_auditable_receipt_or_process_log": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    if args.write and args.verify_existing:
        fail("--write and --verify-existing are mutually exclusive")
    payload = build_payload()
    if args.verify_existing:
        if not OUTPUT.is_file():
            fail("clean disposition contract is missing: " + str(OUTPUT))
        existing = load_json(OUTPUT)
        for key in (
            "$schema", "status", "project_root", "disposition_mode_token", "baseline",
            "failed_runs", "invalid_namespace", "diagnosis", "archive_and_move",
            "fresh_import", "policy",
        ):
            if existing.get(key) != payload.get(key):
                fail("existing clean disposition contract differs at key: " + key)
        print("PASS__TWO_FAILED_RUNS_AND_INVALID_NAMESPACE_MATCH_CLEAN_DISPOSITION_CONTRACT")
        print("CLEAN_DISPOSITION_CONTRACT_SHA256 " + sha256(OUTPUT))
    elif args.write:
        OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("WROTE " + str(OUTPUT))
        print("SHA256 " + sha256(OUTPUT))
    else:
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
