"""Freeze or verify the chained Cairnwell runtime recovery v004 offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v003 as prior


PROJECT = prior.PROJECT
CONTRACT = prior.CONTRACT
CONTRACT_SHA = prior.CONTRACT_SHA
BASELINE = prior.BASELINE
BASELINE_SHA = prior.BASELINE_SHA
V003_CONTRACT = prior.OUTPUT
V003_CONTRACT_SHA = prior.OUTPUT_SHA
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v004_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v004_contract.sha256"
DEST = prior.DEST
AUDIT_ROOT = prior.AUDIT_ROOT
V003_RUN_ID = "20260815T105958Z-79a98abc"
V003_RUN = AUDIT_ROOT / "Recovery_v003" / V003_RUN_ID
V003_IMPORT_FAILURE_SHA256 = (
    "3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C"
)
V003_CONTRACT_SHA256 = (
    "A5ED1D53A35A7D2D58BD533691C4207AF9BF820EBC4D0E0DD0D734254D34FF22"
)
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v004"
V003_QUARANTINE = (
    PROJECT / "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T105958Z-79a98abc_v003"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_ONCE"
RUN_ACK_TOKEN = "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V004_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V004__"
    "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"
)
V003_FILES = {
    "import_failure_recovery_v003.json": (
        7072, "3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C"),
    "lane_summary_recovery_v003.json": (
        3369, "6771F6D980A89CF32D92B7FD1013BAF297D1003AFAEC71B6EEDE824EA8183C45"),
    "quarantine_receipt_v003.json": (
        5195, "1BCE465D7D8CF731CBE6F17121149A74AA550EA12E31C53EAF80D6F55A198D80"),
    "unreal_import_recovery_v003.log": (
        380780, "BC70CA39AA8EEA93AFD9BB7E67AF0AADDA6DB7AE8485AD695BD73D3B0830144C"),
    "unreal_import_recovery_v003.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "unreal_import_recovery_v003.stdout.log": (
        380785, "34E586D561A7A1A9AE5C39E75F26359A8DEC4C22C94484856FCFBEB160FA1E63"),
}
V003_PARTIALS = {
    "Materials/M_LB_C2040_BIWGalvanized_v001.uasset": (
        6002, 1786791714569696100,
        "F81EA9E6D5214E263B2E103F74FC96BD242B6CB714F910DFF94D7C1A535D60E0"),
    "Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset": (
        11566, 1786791714628696400,
        "A27356BC5F25C906B5F873FC1356A27C0976E4AE63C47F6C4DE05AECFB944CBC"),
    "Materials/M_LB_C2040_EDCoat_v001.uasset": (
        5960, 1786791714685697000,
        "CC01EA6964DDBCFEE1550DBAAF5EA79EE998A0BE68A22841ECA14DF53FB7D884"),
    "Materials/M_LB_C2040_RollingGearPBR_v001.uasset": (
        7119, 1786791714741688700,
        "6896BEB2E1BED87248A3F0AD77177C3132B23CEE424055D9D18F988AEEB342F1"),
    "Meshes/SM_LB_C2040_BIW_AutomotiveSkeleton_v001.uasset": (
        2293043, 1786791718669688600,
        "CAFBD608BDD3302C86A8F2DD634C14B41B004DC8D12938DAEB2088628142D4D4"),
    "Meshes/SM_LB_C2040_BIW_UnderbodySubset_v001.uasset": (
        1329365, 1786791718689696200,
        "F174A0BD87165F5FA493A191831490FB2AD7814DD10C1774BC14920521AA1A18"),
    "Meshes/SM_LB_C2040_EmeraldBodyVisualAuthority_v001.uasset": (
        7355548, 1786791718729696200,
        "F6DE95F6D789324D6C62E7ACAC84CD513E71267486DDDC54857255BE4D995259"),
    "Meshes/SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001.uasset": (
        3756424, 1786791718758696200,
        "F287DD3924ED7632E5099F426600285F63310D64C724EB1026791FDBD6F1E2F5"),
    "Textures/T_LB_C2040_Emerald_BaseColor_v001.uasset": (
        3818680, 1786791714368688700,
        "C8D90B29C300F4ED308966226CBFF85930FE9FA9225B5ADEFED2DD440EC11607"),
    "Textures/T_LB_C2040_Emerald_MRBodyMask_v001.uasset": (
        5818244, 1786791714418696600,
        "803E008887DFC6AFB386A205580CF133C85EBC648A6A2B2FC0020EBDD393AA51"),
    "Textures/T_LB_C2040_Emerald_Normal_v001.uasset": (
        3973188, 1786791714455695900,
        "68079B26306853D680539042C8A824C8A2CF3091F8F091635A895267CCBA1BB8"),
}
V004_LANE_CHANGED = {
    "Scripts/cairnwell_2040_runtime_v001.py",
    "Scripts/import_cairnwell_2040_runtime_v001.py",
    "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
    "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
}
V004_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v004.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v003_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v003_contract.sha256",
}
FBX_IMPORT_SOURCE = Path(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Editor\UnrealEd\Private\Fbx\FbxStaticMeshImport.cpp"
)
FBX_IMPORT_SOURCE_SHA256 = (
    "D6E42F80894F87E580DD72FC2EE7F9A46E312DDE1AB006F18F01A068408523C6"
)
ASSET_TAG_PATTERN = re.compile(
    rb"Triangles\x00\x06\x00\x00\x0059998\x00"
    rb"\x0b\x00\x00\x00UVChannels\x00\x02\x00\x00\x001\x00"
    rb"\x09\x00\x00\x00Vertices\x00\x06\x00\x00\x0029109\x00"
)


class RecoveryError(RuntimeError):
    pass


def object_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest().upper()


def exact_prior_contract() -> dict:
    prior.exact_sidecar(
        V003_CONTRACT, V003_CONTRACT_SHA, V003_CONTRACT_SHA256, "v003 contract")
    payload = json.loads(V003_CONTRACT.read_text(encoding="utf-8"))
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v3"
            or payload.get("status") != prior.STATUS
            or payload.get("incident_chain", {}).get("v002", {}).get(
                "import_failure", {}).get("sha256") != prior.V002_IMPORT_FAILURE_SHA256):
        raise RecoveryError("frozen v003 recovery authority drift")
    return payload


def v003_run_rows() -> dict[str, dict]:
    if not V003_RUN.is_dir():
        raise RecoveryError("exact v003 failed-run root is absent")
    actual_names = {path.name for path in V003_RUN.iterdir() if path.is_file()}
    if actual_names != set(V003_FILES):
        raise RecoveryError("v003 failed-run file closure drift: " + repr(sorted(actual_names)))
    rows = {}
    for name, (size, digest) in V003_FILES.items():
        row = prior.file_row(V003_RUN / name)
        if row["bytes"] != size or row["sha256"] != digest:
            raise RecoveryError("v003 failed-run hash drift: " + name)
        rows[name] = row
    failure = json.loads((V003_RUN / "import_failure_recovery_v003.json").read_text())
    summary = json.loads((V003_RUN / "lane_summary_recovery_v003.json").read_text())
    quarantine = json.loads((V003_RUN / "quarantine_receipt_v003.json").read_text())
    process = summary.get("import_process", {})
    if (failure.get("$schema")
            != "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v003/unreal-import/v3"
            or failure.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_UNREAL_IMPORT"
            or failure.get("error") != (
                "CAIRNWELL_2040_RUNTIME_V001_UNREAL_LANE_FAIL: "
                "triangle/positive-vertex/UV drift: BIW_AutomotiveSkeleton:LOD0")
            or summary.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_UNREAL_IMPORT_LANE"
            or summary.get("error")
            != "Recovery importer emitted a failure receipt despite strict process exit gate"
            or int(process.get("exit_code", -1)) != 0
            or int(process.get("redirected_log_read_open_retry", {}).get(
                "stdout_attempts", -1)) != 9
            or quarantine.get("status")
            != "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_PARTIALS_QUARANTINED"):
        raise RecoveryError("v003 primary/wrapper/quarantine incident identity drift")
    return rows


def partial_rows(root: Path, label: str) -> dict[str, dict]:
    if not root.is_dir():
        raise RecoveryError(label + " root absent")
    actual = {path.relative_to(root).as_posix(): path
              for path in root.rglob("*") if path.is_file()}
    if set(actual) != set(V003_PARTIALS):
        raise RecoveryError(label + " eleven-package closure drift")
    rows = {}
    for rel, (size, mtime, digest) in V003_PARTIALS.items():
        row = prior.file_row(actual[rel])
        if (row["bytes"] != size or row["mtime_ns"] != mtime
                or row["sha256"] != digest):
            raise RecoveryError(label + " package hash/mtime drift: " + rel)
        rows[rel] = row
    return rows


def partial_contract_rows() -> dict[str, dict]:
    current = partial_rows(DEST, "v003 fresh destination")
    failure = json.loads((V003_RUN / "import_failure_recovery_v003.json").read_text())
    preserved = failure.get("namespace_files_preserved_for_recovery", {})
    output = {}
    for rel, row in current.items():
        source_path = prior.relative(DEST / rel)
        if preserved.get(source_path) != {
                key: row[key] for key in ("bytes", "mtime_ns", "sha256")}:
            raise RecoveryError("v003 failure receipt does not pin package: " + source_path)
        output[source_path] = {
            "source_path": source_path,
            "quarantine_path": prior.relative(V003_QUARANTINE / rel),
            "bytes": row["bytes"], "mtime_ns": row["mtime_ns"],
            "sha256": row["sha256"],
        }
    return output


def runtime_uv_sanitization(contract: dict) -> dict:
    if prior.sha256(FBX_IMPORT_SOURCE) != FBX_IMPORT_SOURCE_SHA256:
        raise RecoveryError("installed UE5.8 FBX static-mesh import source drift")
    roles = {}
    for role, spec in sorted(contract["modules"].items()):
        source = [int(lod["uv_channels"]) for lod in spec["lods"]]
        runtime = [max(1, value) for value in source]
        if len(source) != 3 or any(value not in (0, 1) for value in source):
            raise RecoveryError("unexpected source UV contract: " + role)
        forced = [value == 0 for value in source]
        if role in {"BIW_AutomotiveSkeleton", "BIW_UnderbodySubset"}:
            if source != [0, 0, 0] or runtime != [1, 1, 1] or forced != [True] * 3:
                raise RecoveryError("exact zero-source-UV BIW sanitation drift: " + role)
        elif source != [1, 1, 1] or runtime != [1, 1, 1] or any(forced):
            raise RecoveryError("unexpected non-BIW UV sanitation: " + role)
        roles[role] = {
            "source_uv_channels_by_lod": source,
            "expected_unreal_uv_channels_by_lod": runtime,
            "ue_forced_minimum_one_by_lod": forced,
        }
    evidence_root = V003_QUARANTINE if V003_QUARANTINE.is_dir() else DEST
    automotive = evidence_root / "Meshes/SM_LB_C2040_BIW_AutomotiveSkeleton_v001.uasset"
    data = automotive.read_bytes()
    matches = ASSET_TAG_PATTERN.findall(data)
    if len(matches) != 1:
        raise RecoveryError("v003 BIW LOD0 embedded AssetRegistry metric proof drift")
    return {
        "engine_source": {
            "path": str(FBX_IMPORT_SOURCE).replace("\\", "/"),
            "sha256": FBX_IMPORT_SOURCE_SHA256,
            "lines": "709-718",
            "proof": "NumUVs = FMath::Max(1, NumUVs) before both UV channel setters",
        },
        "roles": roles,
        "v003_observed_biw_automotive_skeleton_lod0": {
            "package_sha256": V003_PARTIALS[
                "Meshes/SM_LB_C2040_BIW_AutomotiveSkeleton_v001.uasset"][2],
            "evidence": "embedded StaticMesh AssetRegistry tags in preserved package",
            "expected_triangles": 59998,
            "actual_triangles": 59998,
            "source_vertices": 29092,
            "actual_render_vertices": 29109,
            "expected_source_uv_channels": 0,
            "actual_unreal_uv_channels": 1,
            "triangle_or_degenerate_removal_drift": False,
            "sole_failed_predicate": "actual_unreal_uv_channels != source_uv_channels",
        },
    }


def verify_v003_lane_drift(v003: dict) -> None:
    changed = set()
    for expected in v003["lane"]["files"]:
        if prior.file_row(PROJECT / expected["path"]) != expected:
            changed.add(expected["path"])
    if changed != V004_LANE_CHANGED:
        raise RecoveryError("v003 prepared-lane drift is not exact v004 patch: " + repr(changed))


def v004_lane_snapshot(v003: dict) -> dict:
    paths = {row["path"] for row in v003["lane"]["files"]} | V004_ADDITIONS
    snapshot = prior.inventory([PROJECT / rel for rel in paths])
    if {row["path"] for row in snapshot["files"]} != paths:
        raise RecoveryError("v004 prepared-lane path closure drift")
    return snapshot


def result_topology() -> dict:
    prefix = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v004/"
    return {
        "audit_root": prior.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": prior.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "quarantine_receipt": {"filename": "quarantine_receipt_v004.json",
            "$schema": prefix + "quarantine/v4",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_PARTIALS_QUARANTINED"},
        "import": {"receipt_filename": "import_receipt_recovery_v004.json",
            "failure_filename": "import_failure_recovery_v004.json",
            "$schema": prefix + "unreal-import/v4",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_FRESH_IMPORT__4_MESHES__12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE",
            "package_hash_field": "package_sha256"},
        "fresh_validation": {
            "receipt_filename": "fresh_process_validation_receipt_recovery_v004.json",
            "failure_filename": "fresh_process_validation_failure_recovery_v004.json",
            "$schema": prefix + "fresh-process-validation/v4",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED",
            "package_hash_fields": ["package_sha256_before_loads", "package_sha256_after_loads"]},
        "summary": {"filename": "lane_summary_recovery_v004.json",
            "$schema": prefix + "import-lane-summary/v4",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_GUARDED_IMPORT_AND_DISTINCT_READ_ONLY_RELOAD",
            "package_hash_field": "post_exit_package_sha256"},
        "required_incident_binding_fields": ["recovery_contract_sha256",
            "v001_failed_run_id", "v001_import_failure_sha256", "v002_failed_run_id",
            "v002_import_failure_sha256", "v003_failed_run_id",
            "v003_import_failure_sha256", "incident_chain_sha256", "quarantine_receipt"],
    }


def prior_state() -> tuple[dict, dict, dict, str, str]:
    contract, baseline, contract_digest, baseline_digest = prior.load_original()
    v002 = prior.load_v002_contract()
    prior.v002_run_rows()
    v003 = exact_prior_contract()
    v003_run_rows()
    prior.verify_snapshot(v003["prior_quarantines"]["v001_partial_packages"],
                          "v001 package quarantine")
    q2_paths = [PROJECT / row["quarantine_path"]
                for row in v003["partial_packages"].values()]
    q2 = prior.inventory(q2_paths)
    if q2["file_count"] != 7 or not all(prior.inside(path, prior.V002_QUARANTINE)
                                         for path in q2_paths):
        raise RecoveryError("v002 seven-package quarantine closure drift")
    for expected in v003["partial_packages"].values():
        actual = prior.file_row(PROJECT / expected["quarantine_path"])
        if any(actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256")):
            raise RecoveryError(
                "v002 quarantined package hash drift: " + expected["quarantine_path"])
    verify_v003_lane_drift(v003)
    return contract, baseline, v003, contract_digest, baseline_digest


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v004 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v004 recovery contract or sidecar")
    if RECOVERY_AUDIT_ROOT.exists() or V003_QUARANTINE.exists():
        raise RecoveryError("v004 result/quarantine already exists")
    contract, baseline, v003, contract_digest, baseline_digest = prior_state()
    run_rows = v003_run_rows()
    partials = partial_contract_rows()
    chain = {
        "v001": v003["incident_chain"]["v001"],
        "v002": v003["incident_chain"]["v002"],
        "v003": {
            "failed_run_id": V003_RUN_ID,
            "run_root": prior.relative(V003_RUN),
            "recovery_contract": prior.file_row(V003_CONTRACT),
            "recovery_contract_sidecar": prior.file_row(V003_CONTRACT_SHA),
            "import_failure": run_rows["import_failure_recovery_v003.json"],
            "lane_summary": run_rows["lane_summary_recovery_v003.json"],
            "quarantine_receipt": run_rows["quarantine_receipt_v003.json"],
            "files": run_rows,
            "primary_failure": "UE5.8 forced one runtime UV channel for zero-UV FBX",
            "wrapper_result": "strict process/log gate passed then failure receipt stopped lane",
        },
        "old_success_receipts_present": False,
    }
    chain["binding_sha256"] = object_hash(chain)
    q2_paths = [PROJECT / row["quarantine_path"]
                for row in v003["partial_packages"].values()]
    payload = {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v4",
        "status": STATUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": {"contract": prior.file_row(CONTRACT),
            "contract_sidecar": prior.file_row(CONTRACT_SHA),
            "baseline": prior.file_row(BASELINE),
            "baseline_sidecar": prior.file_row(BASELINE_SHA)},
        "approved_source": {key: baseline["source"][key]
                            for key in ("file_count", "inventory_sha256")},
        "protected_project": {key: baseline["protected"][key]
                              for key in ("file_count", "inventory_sha256")},
        "incident_chain": chain,
        "prior_quarantines": {
            "v001_partial_packages": v003["prior_quarantines"]["v001_partial_packages"],
            "v002_partial_packages": prior.inventory(q2_paths),
        },
        "partial_packages": partials,
        "slot_normalization": v003["slot_normalization"],
        "runtime_uv_sanitization": runtime_uv_sanitization(contract),
        "quarantine": {"source_root": prior.relative(DEST),
            "destination_root": prior.relative(V003_QUARANTINE),
            "operation": "MOVE_DIRECTORY_ONLY__NO_DELETE",
            "automatic_delete_authorized": False,
            "rerun_after_any_recovery_result_authorized": False},
        "lane": v004_lane_snapshot(v003),
        "result_topology": result_topology(),
        "policy": {"unreal_launch_authorized_by_freeze": False,
            "source_config_maps_saves_writes_authorized": False,
            "map_load_save_authorized": False,
            "runtime_binding_or_promotion_authorized": False,
            "panel_module_namespace_or_packages_authorized": False,
            "strict_editor_exit_code_zero_required": True,
            "post_receipt_fatal_or_crash_accepted": False,
            "source_uv_authority_must_remain_unmodified": True,
            "runtime_uv_expectation_is_exact_not_relaxed": True},
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = prior.sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    contract, baseline, v003, contract_digest, baseline_digest = prior_state()
    digest = prior.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise RecoveryError("v004 recovery sidecar drift")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    chain = payload.get("incident_chain", {})
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v4"
            or payload.get("status") != STATUS or payload.get("acknowledgement") != RUN_ACK_TOKEN
            or payload.get("original_authorities", {}).get("contract", {}).get("sha256")
            != contract_digest
            or payload.get("original_authorities", {}).get("baseline", {}).get("sha256")
            != baseline_digest
            or chain.get("v001", {}).get("import_failure", {}).get("sha256")
            != prior.V001_IMPORT_FAILURE_SHA256
            or chain.get("v002", {}).get("import_failure", {}).get("sha256")
            != prior.V002_IMPORT_FAILURE_SHA256
            or chain.get("v003", {}).get("import_failure", {}).get("sha256")
            != V003_IMPORT_FAILURE_SHA256):
        raise RecoveryError("v004 recovery contract identity drift")
    prior.verify_snapshot(payload["prior_quarantines"]["v001_partial_packages"],
                          "v001 quarantine")
    prior.verify_snapshot(payload["prior_quarantines"]["v002_partial_packages"],
                          "v002 quarantine")
    prior.verify_snapshot(payload["lane"], "v004 prepared lane")
    if payload["slot_normalization"] != v003["slot_normalization"]:
        raise RecoveryError("v004 slot-normalization authority drift")
    if payload["runtime_uv_sanitization"] != runtime_uv_sanitization(contract):
        raise RecoveryError("v004 runtime UV sanitation authority drift")
    return payload, baseline


def verify_partial_contract(payload: dict, root: Path, label: str) -> None:
    rows = partial_rows(root, label)
    for rel, actual in rows.items():
        source = prior.relative(DEST / rel)
        expected = payload["partial_packages"][source]
        expected_path = source if root == DEST else expected["quarantine_path"]
        if (actual["path"] != expected_path or any(
                actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256"))):
            raise RecoveryError(label + " does not match contract: " + rel)


def verify_pre_quarantine() -> None:
    payload, _ = load_frozen()
    if V003_QUARANTINE.exists() or RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v004 quarantine/result already exists")
    verify_partial_contract(payload, DEST, "v003 fresh destination")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_PRE_QUARANTINE_REVERIFIED")
    print(prior.sha256(OUTPUT))


def verify_post_quarantine() -> None:
    payload, _ = load_frozen()
    if DEST.exists():
        raise RecoveryError("fresh destination remains after v004 quarantine move")
    verify_partial_contract(payload, V003_QUARANTINE, "v003 package quarantine")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_POST_QUARANTINE_REVERIFIED")
    print(prior.sha256(OUTPUT))


def verify_post_import() -> None:
    payload, baseline = load_frozen()
    verify_partial_contract(payload, V003_QUARANTINE, "v003 package quarantine")
    expected = set(baseline["destination"]["expected_package_paths"])
    actual = {"/Game/" + path.relative_to(PROJECT / "Content").with_suffix("").as_posix()
              for path in DEST.rglob("*.uasset")} if DEST.is_dir() else set()
    if actual != expected or len(actual) != 11:
        raise RecoveryError("post-import destination is not exact eleven-package closure")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_POST_IMPORT_REVERIFIED")
    print(prior.sha256(OUTPUT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledgement", default="")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verify-pre-quarantine", action="store_true")
    group.add_argument("--verify-post-quarantine", action="store_true")
    group.add_argument("--verify-post-import", action="store_true")
    args = parser.parse_args()
    if args.verify_pre_quarantine:
        verify_pre_quarantine()
    elif args.verify_post_quarantine:
        verify_post_quarantine()
    elif args.verify_post_import:
        verify_post_import()
    else:
        create_contract(args.acknowledgement)


if __name__ == "__main__":
    main()
