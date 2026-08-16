"""Freeze or verify the incident-bound Cairnwell runtime recovery v006 offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v005 as prior


PROJECT = prior.PROJECT
CONTRACT = prior.CONTRACT
CONTRACT_SHA = prior.CONTRACT_SHA
BASELINE = prior.BASELINE
BASELINE_SHA = prior.BASELINE_SHA
V005_CONTRACT = prior.OUTPUT
V005_CONTRACT_SHA = prior.OUTPUT_SHA
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v006_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v006_contract.sha256"
DEST = prior.DEST
AUDIT_ROOT = prior.AUDIT_ROOT
V005_RUN_ID = "20260815T115847Z-92ea69dd"
V005_RUN = AUDIT_ROOT / "Recovery_v005" / V005_RUN_ID
V005_IMPORT_FAILURE_SHA256 = (
    "435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB"
)
V005_CONTRACT_SHA256 = (
    "E5E9F4CF0E003C0B5936E0EED581D6E697E1C20AD0BC1B390E6FA7D3ADD2E239"
)
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v006"
V005_QUARANTINE = (
    PROJECT / "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T115847Z-92ea69dd_v005"
)
TEXTURE_FORENSICS_ROOT = AUDIT_ROOT / "Recovery_v005_TextureForensics"
TEXTURE_DIAGNOSTIC_RUN = TEXTURE_FORENSICS_ROOT / "Run_readonly_20260815T121015Z"
TEXTURE_DIAGNOSTIC_RECEIPT = (
    TEXTURE_DIAGNOSTIC_RUN / "texture_runtime_properties_read_only.json"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_ONCE"
RUN_ACK_TOKEN = "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V006_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V006__"
    "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"
)
V005_FILES = {
    "import_failure_recovery_v005.json": (
        7486, "435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB"),
    "lane_summary_recovery_v005.json": (
        3691, "58D984424C0132820D05283327751D636D7B32FFC04EBED1E44F2CA68B45C99C"),
    "quarantine_receipt_v005.json": (
        8093, "17CCF587D92D0FBE85E704112B70CA17937E047EB2F4BB3003C40EDB5DD9315E"),
    "unreal_import_recovery_v005.log": (
        406774, "25C565460931492017AE3FE9AD023A5F44971B3AE6BAFA2EE16CE4C2867CF1F6"),
    "unreal_import_recovery_v005.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "unreal_import_recovery_v005.stdout.log": (
        406787, "70C81AEFF22C31F3F8712D49E298B8A1C514B4998F3F302A9DC7C4E0900B6DCC"),
}
V005_PARTIALS = {
    "Materials/M_LB_C2040_BIWGalvanized_v001.uasset": (
        6002, 1786795253747427700,
        "48653B767DA34619873A63EC67DC151E1E9BD0C565A14A4C1C4FA105E96F95AF"),
    "Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset": (
        11566, 1786795253805426900,
        "3670BB2739D78DEABCB169F771F342CDB7FF789C59163EA8C20BC24E203F527A"),
    "Materials/M_LB_C2040_EDCoat_v001.uasset": (
        5960, 1786795253861437900,
        "39EBB5ADA41F1236AE0805D06A5D7BE7116C5F97219665D9D15A856A6F09194B"),
    "Materials/M_LB_C2040_RollingGearPBR_v001.uasset": (
        7119, 1786795253915426800,
        "23F372167D9AA1604176E35C9DD626587A66383A12D547CA76DC494680DD7128"),
    "Meshes/SM_LB_C2040_BIW_AutomotiveSkeleton_v001.uasset": (
        2293043, 1786795257845427400,
        "D3EDFE4656581961BB1A7C06218730D2359AD7A063AB0A8D8EC7B0FA7A9F8F27"),
    "Meshes/SM_LB_C2040_BIW_UnderbodySubset_v001.uasset": (
        1329365, 1786795257865428100,
        "AC4D1F896515CD515907C4CCA7C11E202D08526993A9CAE3103753F7DC24F19F"),
    "Meshes/SM_LB_C2040_EmeraldBodyVisualAuthority_v001.uasset": (
        7355548, 1786795257906426700,
        "FB0A4CEC489DF3AFDF8E89B67FA90B29A6C99AB9135D1231016D3FF3C05A09C4"),
    "Meshes/SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001.uasset": (
        3756424, 1786795257934427100,
        "D5685F0C9300AB0CE0ABCA2921B53F4F6982350889BDD23150135E5004EF843A"),
    "Textures/T_LB_C2040_Emerald_BaseColor_v001.uasset": (
        3818680, 1786795253542265800,
        "1B3E9E256D435B0BF93133F726C3F15F5CD8BD7F7C859D7B45169C7C0E85BE3D"),
    "Textures/T_LB_C2040_Emerald_MRBodyMask_v001.uasset": (
        5818244, 1786795253587265800,
        "5E64D13250AA226AB4D60A66A6291ABA3D892A8EB7968ADF595F6C5F2483AB9E"),
    "Textures/T_LB_C2040_Emerald_Normal_v001.uasset": (
        3973188, 1786795253624266000,
        "46AB631B0F07F67A202EFE7F97ED46178CCB86980D986A23A0E5575CB0A84146"),
}
TEXTURE_FORENSIC_FILES = {
    "20260815T120715Z-readonly/diagnose_textures_read_only.py": (
        7060, "50589A4BAA76925072139FC1D92C0F09E49143A6396412CF800B2EC0023CD77A"),
    "20260815T120715Z-readonly/diagnostic.log": (
        308251, "54AA87B60703486AF6BBE6805DFD0BF4AE95A6F19973BC7B9F5DB438A09F0AD1"),
    "20260815T120715Z-readonly/diagnostic.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "20260815T120715Z-readonly/diagnostic.stdout.log": (
        308153, "CB893F9AA903FA7849477B902C4C170CAB5DDA24A27DE5457CC334439042F7EA"),
    "Run_readonly_20260815T121015Z/diagnostic.log": (
        308531, "2F6584057130D6E0601DA7222F345B0FD5EB25FE13F79C39F626D0BC72C63F49"),
    "Run_readonly_20260815T121015Z/diagnostic.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "Run_readonly_20260815T121015Z/diagnostic.stdout.log": (
        308403, "C580023F915EE4E89EA33BD91C5F114B35002611BEC248AD62FC89295FEE773D"),
    "Run_readonly_20260815T121015Z/texture_runtime_properties_read_only.json": (
        5562, "8476C9EF8CFE8A3E58C383FEC80085370F2554F91618569598FDE5D975E79A4A"),
}
V006_LANE_CHANGED = {
    "Scripts/cairnwell_2040_runtime_v001.py",
    "Scripts/import_cairnwell_2040_runtime_v001.py",
    "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
    "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
}
V006_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v006.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v005_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v005_contract.sha256",
}
PY_WRAPPER_ENUM_SOURCE = Path(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Source\PythonScriptPlugin\Private\PyWrapperEnum.cpp"
)
PY_WRAPPER_ENUM_SOURCE_SHA256 = (
    "54488C18B0C2916E89BF416EAC8F008E79AF430AC2F4EA8299A603D5809693AA"
)


class RecoveryError(RuntimeError):
    pass


def object_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def exact_prior_contract() -> dict:
    prior.prior.prior.exact_sidecar(
        V005_CONTRACT, V005_CONTRACT_SHA, V005_CONTRACT_SHA256, "v005 contract")
    payload = json.loads(V005_CONTRACT.read_text(encoding="utf-8"))
    prior_chain = dict(payload.get("incident_chain", {}))
    declared_binding = prior_chain.pop("binding_sha256", None)
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v5"
            or payload.get("status") != prior.STATUS
            or declared_binding != object_hash(prior_chain)
            or payload.get("incident_chain", {}).get("v004", {}).get(
                "import_failure", {}).get("sha256") != prior.V004_IMPORT_FAILURE_SHA256):
        raise RecoveryError("frozen v005 recovery authority drift")
    return payload


def v005_run_rows() -> dict[str, dict]:
    if not V005_RUN.is_dir():
        raise RecoveryError("exact v005 failed-run root is absent")
    actual_names = {path.name for path in V005_RUN.iterdir() if path.is_file()}
    if actual_names != set(V005_FILES):
        raise RecoveryError("v005 failed-run file closure drift: " + repr(sorted(actual_names)))
    rows = {}
    for name, (size, digest) in V005_FILES.items():
        row = prior.prior.prior.file_row(V005_RUN / name)
        if row["bytes"] != size or row["sha256"] != digest:
            raise RecoveryError("v005 failed-run hash drift: " + name)
        rows[name] = row
    failure = json.loads((V005_RUN / "import_failure_recovery_v005.json").read_text())
    summary = json.loads((V005_RUN / "lane_summary_recovery_v005.json").read_text())
    quarantine = json.loads((V005_RUN / "quarantine_receipt_v005.json").read_text())
    process = summary.get("import_process", {})
    retry = process.get("redirected_log_read_open_retry", {})
    expected_error = (
        "CAIRNWELL_2040_RUNTIME_V001_UNREAL_LANE_FAIL: "
        "texture dimensions/colour/compression drift: base_color"
    )
    if (failure.get("$schema")
            != "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v005/unreal-import/v5"
            or failure.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_UNREAL_IMPORT"
            or failure.get("error") != expected_error
            or summary.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_UNREAL_IMPORT_LANE"
            or summary.get("error")
            != "Recovery importer emitted a failure receipt despite strict process exit gate"
            or int(process.get("exit_code", -1)) != 0
            or int(process.get("process_id", -1)) != 22444
            or process.get("fatal_log_patterns") != []
            or int(retry.get("log_attempts", -1)) != 1
            or int(retry.get("stdout_attempts", -1)) != 6
            or int(retry.get("stderr_attempts", -1)) != 1
            or int(retry.get("bounded_timeout_milliseconds", -1)) != 15000
            or summary.get("post_exit_reverify") is not None
            or summary.get("validation_process") is not None
            or summary.get("import_receipt") is not None
            or summary.get("validation_receipt") is not None
            or summary.get("post_exit_package_sha256") is not None
            or int(summary.get("editor_process_count", -1)) != 1
            or summary.get("no_build_tool_invoked") is not True
            or quarantine.get("status")
            != "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_PARTIALS_QUARANTINED"):
        raise RecoveryError("v005 primary/wrapper/quarantine incident identity drift")
    if set(failure.get("namespace_files_preserved_for_recovery", {})) != {
            prior.prior.prior.relative(DEST / rel) for rel in V005_PARTIALS}:
        raise RecoveryError("v005 failure receipt partial-package closure drift")
    return rows


def partial_rows(root: Path, label: str) -> dict[str, dict]:
    if not root.is_dir():
        raise RecoveryError(label + " root absent")
    actual = {path.relative_to(root).as_posix(): path
              for path in root.rglob("*") if path.is_file()}
    if set(actual) != set(V005_PARTIALS):
        raise RecoveryError(label + " eleven-package closure drift")
    rows = {}
    for rel, (size, mtime, digest) in V005_PARTIALS.items():
        row = prior.prior.prior.file_row(actual[rel])
        if (row["bytes"] != size or row["mtime_ns"] != mtime
                or row["sha256"] != digest):
            raise RecoveryError(label + " package hash/mtime drift: " + rel)
        rows[rel] = row
    return rows


def partial_contract_rows() -> dict[str, dict]:
    current = partial_rows(DEST, "v005 fresh destination")
    failure = json.loads((V005_RUN / "import_failure_recovery_v005.json").read_text())
    preserved = failure.get("namespace_files_preserved_for_recovery", {})
    output = {}
    for rel, row in current.items():
        source_path = prior.prior.prior.relative(DEST / rel)
        if preserved.get(source_path) != {
                key: row[key] for key in ("bytes", "mtime_ns", "sha256")}:
            raise RecoveryError("v005 failure receipt does not pin package: " + source_path)
        output[source_path] = {
            "source_path": source_path,
            "quarantine_path": prior.prior.prior.relative(V005_QUARANTINE / rel),
            "bytes": row["bytes"], "mtime_ns": row["mtime_ns"],
            "sha256": row["sha256"],
        }
    return output


def texture_forensic_rows() -> dict[str, dict]:
    if not TEXTURE_FORENSICS_ROOT.is_dir():
        raise RecoveryError("v005 texture-forensics root is absent")
    actual = {path.relative_to(TEXTURE_FORENSICS_ROOT).as_posix(): path
              for path in TEXTURE_FORENSICS_ROOT.rglob("*") if path.is_file()}
    if set(actual) != set(TEXTURE_FORENSIC_FILES):
        raise RecoveryError("v005 texture-forensics file closure drift")
    rows = {}
    for rel, (size, digest) in TEXTURE_FORENSIC_FILES.items():
        row = prior.prior.prior.file_row(actual[rel])
        if row["bytes"] != size or row["sha256"] != digest:
            raise RecoveryError("v005 texture-forensics hash drift: " + rel)
        rows[rel] = row
    return rows


def enum_validation_authority() -> dict:
    rows = texture_forensic_rows()
    receipt = json.loads(TEXTURE_DIAGNOSTIC_RECEIPT.read_text(encoding="utf-8"))
    expected = {
        "base_color": ([2048, 2048], True, "TC_DEFAULT", 0, False),
        "metallic_roughness": ([2048, 2048], False, "TC_MASKS", 2, False),
        "normal": ([2048, 2048], False, "TC_NORMALMAP", 1, True),
    }
    if (receipt.get("$schema")
            != "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v005/texture-read-only-diagnostic/v1"
            or receipt.get("status")
            != "PASS__READ_ONLY_TEXTURE_RUNTIME_PROPERTIES_CAPTURED__PACKAGES_UNCHANGED"
            or receipt.get("package_hashes_before") != receipt.get("package_hashes_after")
            or set(receipt.get("textures", {})) != set(expected)):
        raise RecoveryError("v005 read-only texture diagnostic identity drift")
    measured = {}
    for semantic, (dimensions, srgb, name, value, flip) in expected.items():
        row = receipt["textures"][semantic]
        actual = row.get("actual", {})
        expected_repr = f"<TextureCompressionSettings.{name}: {value}>"
        if (actual.get("dimensions") != dimensions
                or actual.get("srgb") is not srgb
                or actual.get("flip_green_channel") is not flip
                or actual.get("compression_repr") != expected_repr
                or actual.get("compression_str") != expected_repr):
            raise RecoveryError("v005 texture diagnostic measured-value drift: " + semantic)
        measured[semantic] = {
            "dimensions": dimensions, "srgb": srgb,
            "compression_enum_name": name, "compression_enum_value": value,
            "decorated_runtime_repr": expected_repr,
            "flip_green_channel": flip,
        }
    if prior.prior.prior.sha256(PY_WRAPPER_ENUM_SOURCE) != PY_WRAPPER_ENUM_SOURCE_SHA256:
        raise RecoveryError("installed UE5.8 Python enum wrapper source drift")
    return {
        "classification": (
            "DETERMINISTIC_VALIDATOR_FALSE_NEGATIVE__UE_ENUM_STRING_REPR_HAS_NUMERIC_SUFFIX__"
            "TEXTURE_ASSETS_AND_IMPORTER_SETTINGS_ARE_CORRECT"),
        "comparison_rule": "exact UE Python enum type and value identity",
        "string_suffix_comparison_forbidden": True,
        "semantic_gates_relaxed": False,
        "affected_fields": [
            "Texture2D.compression_settings", "MaterialExpressionTextureSample.sampler_type",
            "MaterialExpressionClamp.clamp_mode", "BodySetup.collision_trace_flag",
            "Material.blend_mode", "Material.material_domain",
        ],
        "engine_source": {
            "path": str(PY_WRAPPER_ENUM_SOURCE).replace("\\", "/"),
            "sha256": PY_WRAPPER_ENUM_SOURCE_SHA256,
            "repr_lines": "378-385", "exact_comparison_lines": "388-410",
            "name_value_lines": "461-462",
        },
        "read_only_diagnostic": {
            "run_root": prior.prior.prior.relative(TEXTURE_DIAGNOSTIC_RUN),
            "receipt": rows[
                "Run_readonly_20260815T121015Z/texture_runtime_properties_read_only.json"],
            "files": rows,
            "textures": measured,
            "package_hashes_unchanged": True,
            "editor_bootstrap_world": "/Engine/Maps/Entry.Entry",
            "package_saves_authorized": [],
        },
    }


def verify_v005_lane_drift(v005: dict) -> None:
    changed = set()
    for expected in v005["lane"]["files"]:
        if prior.prior.prior.file_row(PROJECT / expected["path"]) != expected:
            changed.add(expected["path"])
    if changed != V006_LANE_CHANGED:
        raise RecoveryError("v005 prepared-lane drift is not exact v006 patch: " + repr(changed))


def v006_lane_snapshot(v005: dict) -> dict:
    paths = {row["path"] for row in v005["lane"]["files"]} | V006_ADDITIONS
    snapshot = prior.prior.prior.inventory([PROJECT / rel for rel in paths])
    if {row["path"] for row in snapshot["files"]} != paths or snapshot["file_count"] != 29:
        raise RecoveryError("v006 prepared-lane path closure drift")
    return snapshot


def result_topology() -> dict:
    prefix = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v006/"
    return {
        "audit_root": prior.prior.prior.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": prior.prior.prior.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "quarantine_receipt": {"filename": "quarantine_receipt_v006.json",
            "$schema": prefix + "quarantine/v6",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_PARTIALS_QUARANTINED"},
        "import": {"receipt_filename": "import_receipt_recovery_v006.json",
            "failure_filename": "import_failure_recovery_v006.json",
            "$schema": prefix + "unreal-import/v6",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_FRESH_IMPORT__4_MESHES__12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE",
            "package_hash_field": "package_sha256"},
        "fresh_validation": {
            "receipt_filename": "fresh_process_validation_receipt_recovery_v006.json",
            "failure_filename": "fresh_process_validation_failure_recovery_v006.json",
            "$schema": prefix + "fresh-process-validation/v6",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED",
            "package_hash_fields": ["package_sha256_before_loads", "package_sha256_after_loads"]},
        "summary": {"filename": "lane_summary_recovery_v006.json",
            "$schema": prefix + "import-lane-summary/v6",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_GUARDED_IMPORT_AND_DISTINCT_READ_ONLY_RELOAD",
            "package_hash_field": "post_exit_package_sha256"},
        "required_incident_binding_fields": ["recovery_contract_sha256",
            "v001_failed_run_id", "v001_import_failure_sha256", "v002_failed_run_id",
            "v002_import_failure_sha256", "v003_failed_run_id",
            "v003_import_failure_sha256", "v004_failed_run_id",
            "v004_import_failure_sha256", "v005_failed_run_id",
            "v005_import_failure_sha256", "incident_chain_sha256", "quarantine_receipt"],
    }


def prior_state() -> tuple[dict, dict, dict, str, str]:
    contract, baseline, _, contract_digest, baseline_digest = prior.prior_state()
    v005 = exact_prior_contract()
    v005_run_rows()
    for key in ("v001_partial_packages", "v002_partial_packages", "v003_partial_packages"):
        prior.prior.prior.verify_snapshot(v005["prior_quarantines"][key], key)
    q4_paths = [PROJECT / row["quarantine_path"] for row in v005["partial_packages"].values()]
    q4 = prior.prior.prior.inventory(q4_paths)
    if q4["file_count"] != 11 or not all(
            prior.prior.prior.inside(path, prior.V004_QUARANTINE) for path in q4_paths):
        raise RecoveryError("v004 eleven-package quarantine closure drift")
    for expected in v005["partial_packages"].values():
        actual = prior.prior.prior.file_row(PROJECT / expected["quarantine_path"])
        if any(actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256")):
            raise RecoveryError("v004 quarantined package drift: " + expected["quarantine_path"])
    verify_v005_lane_drift(v005)
    texture_forensic_rows()
    return contract, baseline, v005, contract_digest, baseline_digest


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v006 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v006 recovery contract or sidecar")
    if RECOVERY_AUDIT_ROOT.exists() or V005_QUARANTINE.exists():
        raise RecoveryError("v006 result/quarantine already exists")
    contract, baseline, v005, _, _ = prior_state()
    run_rows = v005_run_rows()
    partials = partial_contract_rows()
    chain = {
        "v001": v005["incident_chain"]["v001"],
        "v002": v005["incident_chain"]["v002"],
        "v003": v005["incident_chain"]["v003"],
        "v004": v005["incident_chain"]["v004"],
        "v005": {
            "failed_run_id": V005_RUN_ID,
            "run_root": prior.prior.prior.relative(V005_RUN),
            "recovery_contract": prior.prior.prior.file_row(V005_CONTRACT),
            "recovery_contract_sidecar": prior.prior.prior.file_row(V005_CONTRACT_SHA),
            "import_failure": run_rows["import_failure_recovery_v005.json"],
            "lane_summary": run_rows["lane_summary_recovery_v005.json"],
            "quarantine_receipt": run_rows["quarantine_receipt_v005.json"],
            "files": run_rows,
            "primary_failure": "decorated UE Python enum repr falsely failed a suffix comparison",
            "wrapper_result": "strict process/log gate passed then failure receipt stopped lane",
        },
        "old_success_receipts_present": False,
    }
    chain["binding_sha256"] = object_hash(chain)
    q4_paths = [PROJECT / row["quarantine_path"] for row in v005["partial_packages"].values()]
    payload = {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v6",
        "status": STATUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": {"contract": prior.prior.prior.file_row(CONTRACT),
            "contract_sidecar": prior.prior.prior.file_row(CONTRACT_SHA),
            "baseline": prior.prior.prior.file_row(BASELINE),
            "baseline_sidecar": prior.prior.prior.file_row(BASELINE_SHA)},
        "approved_source": {key: baseline["source"][key]
                            for key in ("file_count", "inventory_sha256")},
        "protected_project": {key: baseline["protected"][key]
                              for key in ("file_count", "inventory_sha256")},
        "incident_chain": chain,
        "prior_quarantines": {
            "v001_partial_packages": v005["prior_quarantines"]["v001_partial_packages"],
            "v002_partial_packages": v005["prior_quarantines"]["v002_partial_packages"],
            "v003_partial_packages": v005["prior_quarantines"]["v003_partial_packages"],
            "v004_partial_packages": prior.prior.prior.inventory(q4_paths),
        },
        "partial_packages": partials,
        "slot_normalization": v005["slot_normalization"],
        "runtime_uv_sanitization": v005["runtime_uv_sanitization"],
        "runtime_bounds_coordinate_conversion": v005["runtime_bounds_coordinate_conversion"],
        "exact_ue_enum_validation": enum_validation_authority(),
        "quarantine": {"source_root": prior.prior.prior.relative(DEST),
            "destination_root": prior.prior.prior.relative(V005_QUARANTINE),
            "operation": "MOVE_DIRECTORY_ONLY__NO_DELETE",
            "automatic_delete_authorized": False,
            "rerun_after_any_recovery_result_authorized": False},
        "lane": v006_lane_snapshot(v005),
        "result_topology": result_topology(),
        "policy": {"unreal_launch_authorized_by_freeze": False,
            "source_config_maps_saves_writes_authorized": False,
            "map_load_save_authorized": False,
            "runtime_binding_or_promotion_authorized": False,
            "panel_module_namespace_or_packages_authorized": False,
            "strict_editor_exit_code_zero_required": True,
            "post_receipt_fatal_or_crash_accepted": False,
            "source_uv_authority_must_remain_unmodified": True,
            "runtime_uv_expectation_is_exact_not_relaxed": True,
            "source_fbx_bounds_must_remain_unmodified": True,
            "runtime_bounds_tolerance_must_remain_0_25_cm": True,
            "exact_ue_enum_identity_required": True,
            "enum_string_suffix_comparisons_forbidden": True},
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = prior.prior.prior.sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    _, baseline, v005, contract_digest, baseline_digest = prior_state()
    digest = prior.prior.prior.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise RecoveryError("v006 recovery sidecar drift")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    chain = payload.get("incident_chain", {})
    bound_chain = dict(chain)
    declared_chain_hash = bound_chain.pop("binding_sha256", None)
    if declared_chain_hash != object_hash(bound_chain):
        raise RecoveryError("v006 incident-chain binding hash drift")
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v6"
            or payload.get("status") != STATUS or payload.get("acknowledgement") != RUN_ACK_TOKEN
            or payload.get("original_authorities", {}).get("contract", {}).get("sha256")
            != contract_digest
            or payload.get("original_authorities", {}).get("baseline", {}).get("sha256")
            != baseline_digest
            or chain.get("v001", {}).get("import_failure", {}).get("sha256")
            != prior.prior.prior.V001_IMPORT_FAILURE_SHA256
            or chain.get("v002", {}).get("import_failure", {}).get("sha256")
            != prior.prior.prior.V002_IMPORT_FAILURE_SHA256
            or chain.get("v003", {}).get("import_failure", {}).get("sha256")
            != prior.prior.V003_IMPORT_FAILURE_SHA256
            or chain.get("v004", {}).get("import_failure", {}).get("sha256")
            != prior.V004_IMPORT_FAILURE_SHA256
            or chain.get("v005", {}).get("import_failure", {}).get("sha256")
            != V005_IMPORT_FAILURE_SHA256):
        raise RecoveryError("v006 recovery contract identity drift")
    for key in ("v001_partial_packages", "v002_partial_packages",
                "v003_partial_packages", "v004_partial_packages"):
        prior.prior.prior.verify_snapshot(payload["prior_quarantines"][key], key)
    prior.prior.prior.verify_snapshot(payload["lane"], "v006 prepared lane")
    if payload["slot_normalization"] != v005["slot_normalization"]:
        raise RecoveryError("v006 slot-normalization authority drift")
    if payload["runtime_uv_sanitization"] != v005["runtime_uv_sanitization"]:
        raise RecoveryError("v006 runtime UV sanitation authority drift")
    if (payload["runtime_bounds_coordinate_conversion"]
            != v005["runtime_bounds_coordinate_conversion"]):
        raise RecoveryError("v006 runtime bounds conversion authority drift")
    if payload["exact_ue_enum_validation"] != enum_validation_authority():
        raise RecoveryError("v006 exact UE enum-validation authority drift")
    return payload, baseline


def verify_partial_contract(payload: dict, root: Path, label: str) -> None:
    rows = partial_rows(root, label)
    for rel, actual in rows.items():
        source = prior.prior.prior.relative(DEST / rel)
        expected = payload["partial_packages"][source]
        expected_path = source if root == DEST else expected["quarantine_path"]
        if (actual["path"] != expected_path or any(
                actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256"))):
            raise RecoveryError(label + " does not match contract: " + rel)


def verify_pre_quarantine() -> None:
    payload, _ = load_frozen()
    if V005_QUARANTINE.exists() or RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v006 quarantine/result already exists")
    verify_partial_contract(payload, DEST, "v005 fresh destination")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_PRE_QUARANTINE_REVERIFIED")
    print(prior.prior.prior.sha256(OUTPUT))


def verify_post_quarantine() -> None:
    payload, _ = load_frozen()
    if DEST.exists():
        raise RecoveryError("fresh destination remains after v006 quarantine move")
    verify_partial_contract(payload, V005_QUARANTINE, "v005 package quarantine")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_POST_QUARANTINE_REVERIFIED")
    print(prior.prior.prior.sha256(OUTPUT))


def verify_post_import() -> None:
    payload, baseline = load_frozen()
    verify_partial_contract(payload, V005_QUARANTINE, "v005 package quarantine")
    expected_packages = set(baseline["destination"]["expected_package_paths"])
    expected_disk = {
        spec["disk_path"]
        for collection in (baseline["modules"], baseline["textures"], baseline["materials"])
        for spec in collection.values()
    }
    actual_disk = {
        prior.prior.prior.relative(path)
        for path in DEST.rglob("*") if path.is_file()
    } if DEST.is_dir() else set()
    actual_packages = {
        "/Game/" + (PROJECT / path).relative_to(PROJECT / "Content").with_suffix("").as_posix()
        for path in actual_disk if path.endswith(".uasset")
    }
    if (actual_disk != expected_disk or len(actual_disk) != 11
            or actual_packages != expected_packages or len(actual_packages) != 11):
        raise RecoveryError(
            "post-import destination is not exact all-file eleven-package closure: "
            + repr(sorted(actual_disk)))
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_POST_IMPORT_REVERIFIED")
    print(prior.prior.prior.sha256(OUTPUT))


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
