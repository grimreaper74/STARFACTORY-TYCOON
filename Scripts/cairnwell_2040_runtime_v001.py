"""Shared UE 5.8 guards for the Cairnwell2040Runtime_v001 import lane."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
CONTRACT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.json"
CONTRACT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.sha256"
BASELINE = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_baseline.json"
BASELINE_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_baseline.sha256"
RECOVERY_CONTRACT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v009_contract.json"
RECOVERY_CONTRACT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v009_contract.sha256"
DEST = "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001"
RUN_ROOT_ENV = "LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_RUN_ROOT"
ACK_ENV = "LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_ACK"
ACK_TOKEN = "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE"
INTERCHANGE_FBX_CVAR = "Interchange.FeatureFlags.Import.FBX"
IMPORT_RECEIPT = "import_receipt_recovery_v009.json"
IMPORT_FAILURE = "import_failure_recovery_v009.json"
VALIDATION_RECEIPT = "fresh_process_validation_receipt_recovery_v009.json"
VALIDATION_FAILURE = "fresh_process_validation_failure_recovery_v009.json"
SUMMARY = "lane_summary_recovery_v009.json"
QUARANTINE_RECEIPT = "quarantine_receipt_v009.json"
RESULT_NAMES = {IMPORT_RECEIPT, IMPORT_FAILURE, VALIDATION_RECEIPT, VALIDATION_FAILURE, SUMMARY}
EXPECTED_RECOVERY_STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V009__"
    "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"
)
EXPECTED_V001_FAILED_RUN_ID = "20260815T094919Z-7dfb3c0a"
EXPECTED_V001_IMPORT_FAILURE_SHA256 = (
    "05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D"
)
EXPECTED_V002_FAILED_RUN_ID = "20260815T103132Z-3fc39714"
EXPECTED_V002_IMPORT_FAILURE_SHA256 = (
    "86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1"
)
EXPECTED_V002_RECOVERY_CONTRACT_SHA256 = (
    "0D0E0ADE47D80F487A8E94547133323EF1C7622C9260177A948049BC09AA85E2"
)
EXPECTED_V003_FAILED_RUN_ID = "20260815T105958Z-79a98abc"
EXPECTED_V003_IMPORT_FAILURE_SHA256 = (
    "3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C"
)
EXPECTED_V003_RECOVERY_CONTRACT_SHA256 = (
    "A5ED1D53A35A7D2D58BD533691C4207AF9BF820EBC4D0E0DD0D734254D34FF22"
)
EXPECTED_V004_FAILED_RUN_ID = "20260815T112446Z-4e34bb5c"
EXPECTED_V004_IMPORT_FAILURE_SHA256 = (
    "D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF"
)
EXPECTED_V004_RECOVERY_CONTRACT_SHA256 = (
    "C52DE8F74018D03458A94946A0B1208322881F4C52E765B474B3DE56CF8052DA"
)
EXPECTED_V005_FAILED_RUN_ID = "20260815T115847Z-92ea69dd"
EXPECTED_V005_IMPORT_FAILURE_SHA256 = (
    "435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB"
)
EXPECTED_V005_RECOVERY_CONTRACT_SHA256 = (
    "E5E9F4CF0E003C0B5936E0EED581D6E697E1C20AD0BC1B390E6FA7D3ADD2E239"
)
EXPECTED_V006_FAILED_RUN_ID = "20260815T124823Z-67c989ee"
EXPECTED_V006_IMPORT_FAILURE_SHA256 = (
    "A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06"
)
EXPECTED_V006_RECOVERY_CONTRACT_SHA256 = (
    "7DDEF098FF1C2D0E53756E89CC57B1A00A89C32A4A7E623686454D619F3214AD"
)
EXPECTED_V007_PRELIMINARY_CONTRACT_SHA256 = (
    "7271F549ADF301C078636C408B49C5998CE8882A07FB999EF730CB0B97F7698F"
)
EXPECTED_V007_PRELIMINARY_SIDECAR_SHA256 = (
    "ECC793B9319E935EC29762420421292828B7ADF7C0DBBC93022C3154298F8508"
)
EXPECTED_V008_PRELIMINARY_CONTRACT_SHA256 = (
    "6E8E2D0E6D40A16CFF1AF5BEF31A00498C51DEADADF6CE0901D537285E5E49BD"
)
EXPECTED_V008_PRELIMINARY_SIDECAR_SHA256 = (
    "D082F35B000CEC489991F8F481AACA78580CCB1326356F468612C4C99CBA054F"
)
EXPECTED_V007_PRELIMINARY_RESULT_ROOT = (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v007"
)
EXPECTED_V008_PRELIMINARY_RESULT_ROOT = (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v008"
)
EXPECTED_V006_QUARANTINE_ROOT = (
    "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T124823Z-67c989ee_v006"
)
EXPECTED_PRIOR_INCIDENT_ROOTS = {
    "v001": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/20260815T094919Z-7dfb3c0a"),
    "v002": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v002/20260815T103132Z-3fc39714"),
    "v003": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v003/20260815T105958Z-79a98abc"),
    "v004": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v004/20260815T112446Z-4e34bb5c"),
    "v005": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v005/20260815T115847Z-92ea69dd"),
    "v006": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v006/20260815T124823Z-67c989ee"),
}
EXPECTED_PRIOR_INCIDENT_FILE_COUNTS = {
    "v001": 5, "v002": 6, "v003": 6, "v004": 6, "v005": 6, "v006": 6,
}
EXPECTED_PRIOR_QUARANTINE_ROOTS = {
    "v001": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T094919Z-7dfb3c0a_v001"),
    "v002": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T103132Z-3fc39714_v002"),
    "v003": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T105958Z-79a98abc_v003"),
    "v004": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T112446Z-4e34bb5c_v004"),
    "v005": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T115847Z-92ea69dd_v005"),
}
EXPECTED_PRIOR_QUARANTINE_FILE_COUNTS = {
    "v001": 4, "v002": 7, "v003": 11, "v004": 11, "v005": 11,
}
EXPECTED_BASELINE_STATUS = "FROZEN__CAIRNWELL_2040_RUNTIME_V001_PROJECT_BASELINE"
EXPECTED_CONTRACT_STATUS = "FROZEN__APPROVED_CAIRNWELL_V005_WINNER__READY_FOR_BASELINE"
EXPECTED_V005_ROOT_RELATIVE = (
    "SourceAssets/Candidate/Vehicles/Cairnwell2040/"
    "FinishedVehicleRuntimeDerivative_v001/ProductionCandidate_v005/"
)
EXPECTED_MANIFEST_RELATIVE = EXPECTED_V005_ROOT_RELATIVE + "MANIFEST_v005.json"
EXPECTED_PAINT_MASK_STATUS = (
    "APPROVED__MANUALLY_AUTHORED_V005_BODY_PAINT_MASK__VISUALLY_VALIDATED"
)
EXPECTED_SUPERSESSION_STATUS = (
    "APPROVED__V005_MANUAL_MASK_SUPERSEDES_HISTORICAL_DO_NOT_PROMOTE_WITHOUT_DELETION"
)
EXPECTED_SUPERSESSION_RECORD_RELATIVE = (
    EXPECTED_V005_ROOT_RELATIVE
    + "Audit/Cairnwell2040_v005_FinalApprovalSupersession.json"
)
EXPECTED_FREEZE_AMENDMENT_STATUS = (
    "PASS__V005_ADDITIVE_FREEZE_RECEIPT_V002__CURRENT_CONTRACT_AUTHORITY__"
    "SOLE_SCHEMA_KEY_CORRECTION"
)
EXPECTED_FREEZE_AMENDMENT_SCHEMA = (
    "lineboss.cairnwell2040.v005.additive-freeze-amendment.v2"
)
EXPECTED_FREEZE_AMENDMENT_RECORD_RELATIVE = (
    EXPECTED_V005_ROOT_RELATIVE
    + "Audit/Cairnwell2040_v005_AdditiveFreezeReceipt_v002.json"
)
EXPECTED_FREEZE_AMENDMENT_SHA256 = (
    "7BCE6A5A1DF2C0080011D8EB78D24C5839B44A4755F65FD2939F0E562D75A4A0"
)
EXPECTED_STALE_FREEZE_RECEIPT_RELATIVE = (
    EXPECTED_V005_ROOT_RELATIVE
    + "Audit/Cairnwell2040_v005_AdditiveFreezeReceipt.json"
)
EXPECTED_STALE_FREEZE_RECEIPT_SHA256 = (
    "F7C761D794F44E7EEEBB2958A7947F63D59D0EE828510E1803D7B69EA62642F0"
)
EXPECTED_CURRENT_SUPERSESSION_SHA256 = (
    "738E19C3D1D07028C0F2C107AD023F14DBC94FD44DAE2107411D6C8A317A348C"
)
EXPECTED_STALE_V1_SUPERSESSION_SHA256 = (
    "8E40E4ED420A7F343B8678562D8D38058EAFA72001007F9249AEA97718DE0B98"
)
EXPECTED_SUPERSESSION_EVIDENCE_PATHS = {
    "historical_do_not_promote_marker": (
        EXPECTED_V005_ROOT_RELATIVE + "PENDING_ROOT_VISUAL_APPROVAL_DO_NOT_PROMOTE.md"
    ),
    "approved_manifest": EXPECTED_MANIFEST_RELATIVE,
    "manual_paint_mask_audit": (
        EXPECTED_V005_ROOT_RELATIVE
        + "Audit/Cairnwell2040_v005_ManualPaintMask_Audit.json"
    ),
    "manual_paint_mask_texture": (
        EXPECTED_V005_ROOT_RELATIVE
        + "Textures/T_LB_C2040_Emerald_MR_BodyPaintMaskA_v005.png"
    ),
}
EXPECTED_SUPERSESSION_RENDER_PATHS = {
    name: (
        EXPECTED_V005_ROOT_RELATIVE
        + "Renders/PaintMaskAuthority_v005/"
        + f"Cairnwell2040_v005_ManualPaintMask_{name}.png"
    )
    for name in ("front", "hero", "rear", "side")
}
EXPECTED_MAPLESS_STARTUP_OVERRIDE = (
    "-ini:EditorPerProjectUserSettings:"
    "[/Script/UnrealEd.EditorLoadingSavingSettings]:LoadLevelAtStartup=None"
)
EXPECTED_MESH_NAMES = {
    "BIW_AutomotiveSkeleton": "SM_LB_C2040_BIW_AutomotiveSkeleton_v001",
    "BIW_UnderbodySubset": "SM_LB_C2040_BIW_UnderbodySubset_v001",
    "EmeraldBodyVisualAuthority": "SM_LB_C2040_EmeraldBodyVisualAuthority_v001",
    "EmeraldRollingGearVisualAuthority": "SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001",
}
EXPECTED_MATERIAL_IDENTITIES = {
    "body": ("M_LB_C2040_BodyPaintTintPBR_v001", "textured_tint_pbr"),
    "rolling_gear": ("M_LB_C2040_RollingGearPBR_v001", "textured_pbr"),
    "biw_galvanised": ("M_LB_C2040_BIWGalvanized_v001", "solid_pbr"),
    "ed_coat": ("M_LB_C2040_EDCoat_v001", "solid_pbr"),
}
EXPECTED_ROLE_MATERIAL = {
    "BIW_AutomotiveSkeleton": "biw_galvanised",
    "BIW_UnderbodySubset": "ed_coat",
    "EmeraldBodyVisualAuthority": "body",
    "EmeraldRollingGearVisualAuthority": "rolling_gear",
}
library = unreal.EditorAssetLibrary
TEXTURE_COMPRESSION_BY_NAME = {
    "TC_DEFAULT": unreal.TextureCompressionSettings.TC_DEFAULT,
    "TC_MASKS": unreal.TextureCompressionSettings.TC_MASKS,
    "TC_NORMALMAP": unreal.TextureCompressionSettings.TC_NORMALMAP,
}
MATERIAL_SAMPLER_BY_NAME = {
    "SAMPLERTYPE_COLOR": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    "SAMPLERTYPE_MASKS": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    "SAMPLERTYPE_NORMAL": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
}
CLAMP_MODE_BY_NAME = {
    "CMODE_CLAMP": unreal.ClampMode.CMODE_CLAMP,
}
COLLISION_TRACE_BY_NAME = {
    "CTF_USE_SIMPLE_AS_COMPLEX": unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX,
}
BLEND_MODE_BY_NAME = {
    "BLEND_OPAQUE": unreal.BlendMode.BLEND_OPAQUE,
}
MATERIAL_DOMAIN_BY_NAME = {
    "MD_SURFACE": unreal.MaterialDomain.MD_SURFACE,
}
REFLECTED_MATERIAL_INPUT_NAMES_BY_CLASS = {
    "MaterialExpressionLinearInterpolate": ["A", "B", "Alpha"],
    "MaterialExpressionMultiply": ["A", "B"],
    "MaterialExpressionClamp": ["None", "Min", "Max"],
    "MaterialExpressionDotProduct": ["A", "B"],
}


def fail(message: str) -> None:
    raise RuntimeError("CAIRNWELL_2040_RUNTIME_V001_UNREAL_LANE_FAIL: " + message)


def enum_is_exact(actual, expected) -> bool:
    """Compare UE Python enum type and value without its decorated string repr."""
    return type(actual) is type(expected) and actual == expected


def canonical_enum_name(actual, authorities: dict, label: str) -> str:
    matches = [
        name for name, expected in authorities.items()
        if enum_is_exact(actual, expected)
    ]
    if len(matches) != 1:
        fail(
            "unrecognized or ambiguous UE enum identity: " + label
            + ": expected_names="
            + json.dumps(sorted(authorities), separators=(",", ":"))
            + " actual_repr=" + repr(actual)
            + " actual_type=" + type(actual).__name__
        )
    return matches[0]


def fail_expected_actual(label: str, expected: dict, actual: dict,
                         mismatched_fields: list[str]) -> None:
    fail(
        label
        + ": mismatched_fields="
        + json.dumps(sorted(mismatched_fields), separators=(",", ":"))
        + " expected="
        + json.dumps(expected, sort_keys=True, separators=(",", ":"))
        + " actual="
        + json.dumps(actual, sort_keys=True, separators=(",", ":"))
    )


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT).as_posix()
    except ValueError as exc:
        fail(f"path escapes exact project root: {path}")
        raise exc


def file_row(path: Path) -> dict:
    if not path.is_file():
        fail("required file missing: " + str(path))
    stat = path.stat()
    return {
        "path": relative(path),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def canonical_hash(rows: list[dict]) -> str:
    compact = [
        {key: row[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
        for row in sorted(rows, key=lambda item: item["path"].casefold())
    ]
    return hashlib.sha256(
        json.dumps(compact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def object_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def sidecar_hash(payload: Path, sidecar: Path, label: str) -> str:
    if not payload.is_file() or not sidecar.is_file():
        fail(f"{label} and sidecar are absent")
    digest = sha256(payload)
    if sidecar.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        fail(f"{label} sidecar mismatch")
    return digest


def exact_recovery_row(expected: object, label: str) -> dict:
    if not isinstance(expected, dict) or set(expected) != {
            "path", "bytes", "mtime_ns", "sha256"}:
        fail(label + " row schema drift")
    actual = file_row(PROJECT / str(expected.get("path", "")))
    if actual != expected:
        fail(label + " byte/hash/mtime drift")
    return actual


def source_bounds_to_unreal(source: dict) -> dict:
    minimum = [float(value) for value in source["minimum_cm"]]
    maximum = [float(value) for value in source["maximum_cm"]]
    pivot = [float(value) for value in source["pivot_cm"]]
    converted_minimum = [minimum[0], -maximum[1], minimum[2]]
    converted_maximum = [maximum[0], -minimum[1], maximum[2]]
    return {
        "minimum_cm": converted_minimum,
        "maximum_cm": converted_maximum,
        "dimensions_cm": [
            round(converted_maximum[index] - converted_minimum[index], 6)
            for index in range(3)
        ],
        "pivot_cm": [pivot[0], -pivot[1], pivot[2]],
    }


def load_recovery_contract(baseline: dict, contract_digest: str,
                           baseline_digest: str) -> tuple[dict, str]:
    digest = sidecar_hash(
        RECOVERY_CONTRACT, RECOVERY_CONTRACT_SHA, "incident-chained recovery v009 contract")
    payload = json.loads(RECOVERY_CONTRACT.read_text(encoding="utf-8"))
    original = payload.get("original_authorities", {})
    chain = payload.get("incident_chain", {})
    v001 = chain.get("v001", {})
    v002 = chain.get("v002", {})
    v003 = chain.get("v003", {})
    v004 = chain.get("v004", {})
    v005 = chain.get("v005", {})
    v006 = chain.get("v006", {})
    quarantine = payload.get("quarantine", {})
    bound_chain = dict(chain)
    declared_chain_hash = bound_chain.pop("binding_sha256", None)
    if declared_chain_hash != object_hash(bound_chain):
        fail("incident-chained recovery v009 binding hash drift")
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v9"
            or payload.get("status") != EXPECTED_RECOVERY_STATUS
            or payload.get("acknowledgement") != ACK_TOKEN
            or original.get("contract", {}).get("sha256") != contract_digest
            or original.get("baseline", {}).get("sha256") != baseline_digest
            or payload.get("approved_source", {}).get("file_count")
            != baseline.get("source", {}).get("file_count")
            or payload.get("approved_source", {}).get("inventory_sha256")
            != baseline.get("source", {}).get("inventory_sha256")
            or payload.get("protected_project", {}).get("file_count")
            != baseline.get("protected", {}).get("file_count")
            or payload.get("protected_project", {}).get("inventory_sha256")
            != baseline.get("protected", {}).get("inventory_sha256")
            or v001.get("failed_run_id") != EXPECTED_V001_FAILED_RUN_ID
            or v001.get("import_failure", {}).get("sha256")
            != EXPECTED_V001_IMPORT_FAILURE_SHA256
            or v002.get("failed_run_id") != EXPECTED_V002_FAILED_RUN_ID
            or v002.get("import_failure", {}).get("sha256")
            != EXPECTED_V002_IMPORT_FAILURE_SHA256
            or v002.get("recovery_contract", {}).get("sha256")
            != EXPECTED_V002_RECOVERY_CONTRACT_SHA256
            or v003.get("failed_run_id") != EXPECTED_V003_FAILED_RUN_ID
            or v003.get("import_failure", {}).get("sha256")
            != EXPECTED_V003_IMPORT_FAILURE_SHA256
            or v003.get("recovery_contract", {}).get("sha256")
            != EXPECTED_V003_RECOVERY_CONTRACT_SHA256
            or v004.get("failed_run_id") != EXPECTED_V004_FAILED_RUN_ID
            or v004.get("import_failure", {}).get("sha256")
            != EXPECTED_V004_IMPORT_FAILURE_SHA256
            or v004.get("recovery_contract", {}).get("sha256")
            != EXPECTED_V004_RECOVERY_CONTRACT_SHA256
            or v005.get("failed_run_id") != EXPECTED_V005_FAILED_RUN_ID
            or v005.get("import_failure", {}).get("sha256")
            != EXPECTED_V005_IMPORT_FAILURE_SHA256
            or v005.get("recovery_contract", {}).get("sha256")
            != EXPECTED_V005_RECOVERY_CONTRACT_SHA256
            or v006.get("failed_run_id") != EXPECTED_V006_FAILED_RUN_ID
            or v006.get("import_failure", {}).get("sha256")
            != EXPECTED_V006_IMPORT_FAILURE_SHA256
            or v006.get("recovery_contract", {}).get("sha256")
            != EXPECTED_V006_RECOVERY_CONTRACT_SHA256
            or chain.get("old_success_receipts_present") is not False
            or quarantine.get("operation") != "MOVE_DIRECTORY_ONLY__NO_DELETE"
            or quarantine.get("automatic_delete_authorized") is not False
            or payload.get("policy", {}).get("unreal_launch_authorized_by_freeze") is not False
            or payload.get("policy", {}).get("source_config_maps_saves_writes_authorized")
            is not False
            or payload.get("policy", {}).get(
                "source_uv_authority_must_remain_unmodified") is not True
            or payload.get("policy", {}).get(
                "runtime_uv_expectation_is_exact_not_relaxed") is not True
            or payload.get("policy", {}).get(
                "source_fbx_bounds_must_remain_unmodified") is not True
            or payload.get("policy", {}).get(
                "runtime_bounds_tolerance_must_remain_0_25_cm") is not True
            or payload.get("policy", {}).get("exact_ue_enum_identity_required") is not True
            or payload.get("policy", {}).get(
                "enum_string_suffix_comparisons_forbidden") is not True
            or payload.get("policy", {}).get(
                "unnamed_material_input_canonicalization_required") is not True
            or payload.get("policy", {}).get(
                "raw_none_input_names_forbidden_in_graph_evidence") is not True
            or payload.get("policy", {}).get(
                "exact_prior_all_file_closures_required") is not True
            or payload.get("policy", {}).get(
                "stale_v007_pair_must_remain_byte_exact") is not True
            or payload.get("policy", {}).get(
                "stale_v008_pair_must_remain_byte_exact") is not True
            or payload.get("policy", {}).get(
                "no_write_full_candidate_payload_preflight_required") is not True):
        fail("incident-chained recovery v009 identity/safety drift")
    for version, incident in (
            ("v001", v001), ("v002", v002), ("v003", v003), ("v004", v004),
            ("v005", v005), ("v006", v006)):
        for label, row in incident.get("files", {}).items():
            exact_recovery_row(row, f"preserved {version} incident " + label)
    exact_recovery_row(v002.get("recovery_contract", {}), "frozen v002 recovery contract")
    exact_recovery_row(
        v002.get("recovery_contract_sidecar", {}), "frozen v002 recovery sidecar")
    exact_recovery_row(v003.get("recovery_contract", {}), "frozen v003 recovery contract")
    exact_recovery_row(
        v003.get("recovery_contract_sidecar", {}), "frozen v003 recovery sidecar")
    exact_recovery_row(v004.get("recovery_contract", {}), "frozen v004 recovery contract")
    exact_recovery_row(
        v004.get("recovery_contract_sidecar", {}), "frozen v004 recovery sidecar")
    exact_recovery_row(v005.get("recovery_contract", {}), "frozen v005 recovery contract")
    exact_recovery_row(
        v005.get("recovery_contract_sidecar", {}), "frozen v005 recovery sidecar")
    exact_recovery_row(v006.get("recovery_contract", {}), "frozen v006 recovery contract")
    exact_recovery_row(
        v006.get("recovery_contract_sidecar", {}), "frozen v006 recovery sidecar")
    exact_recovery_row(original.get("contract", {}), "original frozen contract")
    exact_recovery_row(original.get("contract_sidecar", {}), "original contract sidecar")
    exact_recovery_row(original.get("baseline", {}), "original frozen baseline")
    exact_recovery_row(original.get("baseline_sidecar", {}), "original baseline sidecar")
    preliminary = payload.get("stale_preliminary_v007", {})
    preliminary_contract = exact_recovery_row(
        preliminary.get("contract", {}), "stale preliminary v007 contract")
    preliminary_sidecar = exact_recovery_row(
        preliminary.get("sidecar", {}), "stale preliminary v007 sidecar")
    if (preliminary.get("status")
            != "STALE__UNEXECUTED_V007_PRELIMINARY__SUPERSEDED_BY_V008_EXACT_CLOSURE"
            or preliminary_contract.get("path")
            != "Scripts/cairnwell_2040_runtime_v001_recovery_v007_contract.json"
            or preliminary_contract.get("sha256")
            != EXPECTED_V007_PRELIMINARY_CONTRACT_SHA256
            or preliminary_sidecar.get("path")
            != "Scripts/cairnwell_2040_runtime_v001_recovery_v007_contract.sha256"
            or preliminary_sidecar.get("sha256")
            != EXPECTED_V007_PRELIMINARY_SIDECAR_SHA256
            or preliminary.get("recovery_v007_result_root")
            != EXPECTED_V007_PRELIMINARY_RESULT_ROOT
            or preliminary.get("v006_quarantine_root")
            != EXPECTED_V006_QUARANTINE_ROOT
            or preliminary.get("recovery_v007_result_root_absent_at_freeze") is not True
            or preliminary.get("v006_quarantine_absent_at_freeze") is not True
            or preliminary.get("unreal_or_ubt_launched_by_v007_freeze") is not False
            or preliminary.get("content_move_performed_by_v007_freeze") is not False):
        fail("stale preliminary v007 chronology authority drift")
    preliminary_result_root = PROJECT / str(
        preliminary.get("recovery_v007_result_root", ""))
    if preliminary_result_root.exists():
        fail("preliminary v007 result root unexpectedly exists")
    preliminary_v008 = payload.get("stale_preliminary_v008", {})
    preliminary_v008_contract = exact_recovery_row(
        preliminary_v008.get("contract", {}), "stale preliminary v008 contract")
    preliminary_v008_sidecar = exact_recovery_row(
        preliminary_v008.get("sidecar", {}), "stale preliminary v008 sidecar")
    if (preliminary_v008.get("status")
            != "STALE__UNEXECUTED_V008_PRELIMINARY__SUPERSEDED_BY_V009_FULL_NO_WRITE_PAYLOAD_PREFLIGHT"
            or preliminary_v008_contract.get("path")
            != "Scripts/cairnwell_2040_runtime_v001_recovery_v008_contract.json"
            or preliminary_v008_contract.get("sha256")
            != EXPECTED_V008_PRELIMINARY_CONTRACT_SHA256
            or preliminary_v008_sidecar.get("path")
            != "Scripts/cairnwell_2040_runtime_v001_recovery_v008_contract.sha256"
            or preliminary_v008_sidecar.get("sha256")
            != EXPECTED_V008_PRELIMINARY_SIDECAR_SHA256
            or preliminary_v008.get("reason")
            != "POST_FREEZE_PRE_QUARANTINE_CONSTANT_LOOKUP_FAILED_BEFORE_ANY_MOVE_OR_UE"
            or preliminary_v008.get("recovery_v008_result_root")
            != EXPECTED_V008_PRELIMINARY_RESULT_ROOT
            or preliminary_v008.get("v006_quarantine_root")
            != EXPECTED_V006_QUARANTINE_ROOT
            or preliminary_v008.get("recovery_v008_result_root_absent_at_freeze") is not True
            or preliminary_v008.get("v006_quarantine_absent_at_freeze") is not True
            or preliminary_v008.get("unreal_or_ubt_launched_by_v008_freeze") is not False
            or preliminary_v008.get("content_move_performed_by_v008_freeze") is not False):
        fail("stale preliminary v008 chronology authority drift")
    preliminary_v008_result_root = PROJECT / str(
        preliminary_v008.get("recovery_v008_result_root", ""))
    if preliminary_v008_result_root.exists():
        fail("preliminary v008 result root unexpectedly exists")
    closures = payload.get("exact_prior_all_file_closures", {})
    if (set(closures.get("incident_roots", {}))
            != {"v001", "v002", "v003", "v004", "v005", "v006"}
            or set(closures.get("quarantine_roots", {}))
            != {"v001", "v002", "v003", "v004", "v005"}):
        fail("v009 prior all-file closure key drift")
    for version, snapshot in closures["incident_roots"].items():
        if (snapshot.get("root") != EXPECTED_PRIOR_INCIDENT_ROOTS[version]
                or int(snapshot.get("file_count", -1))
                != EXPECTED_PRIOR_INCIDENT_FILE_COUNTS[version]):
            fail("preserved incident exact root/count authority drift: " + version)
        verify_exact_directory_snapshot(snapshot, "preserved incident " + version)
    for version, snapshot in closures["quarantine_roots"].items():
        if (snapshot.get("root") != EXPECTED_PRIOR_QUARANTINE_ROOTS[version]
                or int(snapshot.get("file_count", -1))
                != EXPECTED_PRIOR_QUARANTINE_FILE_COUNTS[version]):
            fail("preserved quarantine exact root/count authority drift: " + version)
        verify_exact_directory_snapshot(snapshot, "preserved quarantine " + version)
    enum_authority = payload.get("exact_ue_enum_validation", {})
    enum_engine = enum_authority.get("engine_source", {})
    diagnostic = enum_authority.get("read_only_diagnostic", {})
    expected_enum_fields = {
        "Texture2D.compression_settings",
        "MaterialExpressionTextureSample.sampler_type",
        "MaterialExpressionClamp.clamp_mode",
        "BodySetup.collision_trace_flag",
        "Material.blend_mode",
        "Material.material_domain",
    }
    if (enum_authority.get("classification")
            != "DETERMINISTIC_VALIDATOR_FALSE_NEGATIVE__UE_ENUM_STRING_REPR_HAS_NUMERIC_SUFFIX__TEXTURE_ASSETS_AND_IMPORTER_SETTINGS_ARE_CORRECT"
            or enum_authority.get("comparison_rule")
            != "exact UE Python enum type and value identity"
            or enum_authority.get("string_suffix_comparison_forbidden") is not True
            or enum_authority.get("semantic_gates_relaxed") is not False
            or set(enum_authority.get("affected_fields", [])) != expected_enum_fields
            or enum_engine.get("sha256")
            != "54488C18B0C2916E89BF416EAC8F008E79AF430AC2F4EA8299A603D5809693AA"
            or enum_engine.get("repr_lines") != "378-385"
            or enum_engine.get("exact_comparison_lines") != "388-410"
            or diagnostic.get("package_hashes_unchanged") is not True
            or diagnostic.get("editor_bootstrap_world") != "/Engine/Maps/Entry.Entry"
            or diagnostic.get("package_saves_authorized") != []
            or len(diagnostic.get("files", {})) != 8):
        fail("recovery v006 exact UE enum-validation authority drift")
    enum_engine_path = Path(str(enum_engine.get("path", "")))
    if (not enum_engine_path.is_file()
            or sha256(enum_engine_path) != enum_engine.get("sha256")):
        fail("recovery v006 installed UE Python enum-wrapper source drift")
    for label, row in diagnostic.get("files", {}).items():
        exact_recovery_row(row, "v005 texture forensic " + label)
    exact_recovery_row(
        diagnostic.get("receipt", {}), "v005 read-only texture diagnostic receipt")
    expected_measured = {
        "base_color": ([2048, 2048], True, "TC_DEFAULT", 0, False),
        "metallic_roughness": ([2048, 2048], False, "TC_MASKS", 2, False),
        "normal": ([2048, 2048], False, "TC_NORMALMAP", 1, True),
    }
    for semantic, (dimensions, srgb, name, value, flip) in expected_measured.items():
        measured = diagnostic.get("textures", {}).get(semantic, {})
        if (measured.get("dimensions") != dimensions
                or measured.get("srgb") is not srgb
                or measured.get("compression_enum_name") != name
                or measured.get("compression_enum_value") != value
                or measured.get("decorated_runtime_repr")
                != f"<TextureCompressionSettings.{name}: {value}>"
                or measured.get("flip_green_channel") is not flip):
            fail("recovery v006 exact measured texture enum authority drift: " + semantic)

    input_authority = payload.get("material_input_name_canonicalization", {})
    input_sources = input_authority.get("engine_sources", {})
    expected_input_sources = {
        "material_editing_library": {
            "bytes": 71759,
            "sha256": "96051980458DAD86719F195072DA4BD34EEBD07A80D647EBB50BBBB0626E5565",
            "connection_lookup_lines": "46-75", "reflection_lines": "1203-1225"},
        "material_graph_node": {
            "bytes": 37860,
            "sha256": "026D9A5C896AF1E590E4BD8E42F1EC4788C8210198007D79C5051F8792716DD9",
            "shortening_lines": "597-613"},
        "python_string_conversion": {
            "bytes": 47655,
            "sha256": "20B3FB6654B4422E7F7327EBC79BA29AC1F4E5366A12A962992E94E516070901",
            "fstring_to_python_lines": "328-331", "array_wrapper_lines": "1191-1195"},
        "unreal_names": {
            "bytes": 186237,
            "sha256": "1A4F7F23564AFEBC8C18D080A4757B16958C15FCAB513C9E3A1F0A67E565F67C",
            "to_string_lines": "3596-3609", "none_spelling_lines": "4206;4214-4224"},
        "expression_input_iterator": {
            "bytes": 27931,
            "sha256": "164DEA3A175E742D2622C8CCA81B6808B07FF7D70F4119D23B389DBFF498D977",
            "iterator_lines": "667-718"},
        "clamp_header": {
            "bytes": 1644,
            "sha256": "B99BD633B8AAB91211162B3EEBF5021BB8C182CEC8FCD9AC051371F8CECB6DEA",
            "input_order_lines": "27-34"},
        "lerp_header": {
            "bytes": 1746,
            "sha256": "0BD39BC602A1F3889793636425A88249C4BA8F3463D91F4BDC64687FAC68A591",
            "input_order_lines": "18-25"},
        "multiply_header": {
            "bytes": 1392,
            "sha256": "B6650CFBBBBD753031277695F633D4271DD5CEEA4C948C73950E3A41168A7CB5",
            "input_order_lines": "19-23"},
        "dot_header": {
            "bytes": 840,
            "sha256": "3179C578A54C54FAA7F6A9D283C321574DAC50DD2C071405AF5F3363EAAA063E",
            "input_order_lines": "19-23"},
        "material_expressions": {
            "bytes": 778212,
            "sha256": "66909943C30BDCEA8F8BC47BD3B719093EEED4D11715B94CB120FB4F4330D815",
            "clamp_input_derivation_lines": "1821-1849"},
    }
    audited_links = input_authority.get("audited_expression_links", {})
    expected_audited_links = {
        "MaterialExpressionLinearInterpolate": {
            "occurrences": 1,
            "raw_input_names": ["A", "B", "Alpha"],
            "canonical_input_names": ["A", "B", "Alpha"],
        },
        "MaterialExpressionMultiply": {
            "occurrences": 2,
            "raw_input_names": ["A", "B"],
            "canonical_input_names": ["A", "B"],
        },
        "MaterialExpressionClamp": {
            "occurrences": 1,
            "raw_input_names": ["None", "Min", "Max"],
            "canonical_input_names": ["", "Min", "Max"],
        },
        "MaterialExpressionDotProduct": {
            "occurrences": 1,
            "raw_input_names": ["A", "B"],
            "canonical_input_names": ["A", "B"],
        },
    }
    if (input_authority.get("classification")
            != "DETERMINISTIC_VALIDATOR_FALSE_NEGATIVE__UE_NAME_NONE_REFLECTS_AS_LITERAL_NONE__MATERIAL_GRAPH_CONNECTION_AND_ASSET_ARE_CORRECT"
            or input_authority.get("import_connection_name") != ""
            or input_authority.get("reflected_raw_name") != "None"
            or input_authority.get("canonical_graph_name") != ""
            or input_authority.get("duplicate_canonical_names_rejected") is not True
            or input_authority.get("raw_none_input_names_in_graph_evidence") is not False
            or input_authority.get("semantic_gates_relaxed") is not False
            or audited_links != expected_audited_links
            or set(input_sources) != set(expected_input_sources)):
        fail("recovery v009 UE5.8 material-input canonicalization authority drift")
    for label, expected_source in expected_input_sources.items():
        row = input_sources[label]
        if any(row.get(key) != value for key, value in expected_source.items()):
            fail("recovery v009 UE source contract drift: " + label)
        source_path = Path(str(row.get("path", "")))
        if (not source_path.is_file() or source_path.stat().st_size != row.get("bytes")
                or sha256(source_path) != row.get("sha256")):
            fail("recovery v009 installed UE source drift: " + label)
    exact_recovery_row(
        input_authority.get("v006_import_failure", {}),
        "v006 reflected material-input failure evidence")
    body_package = input_authority.get("v006_body_material_package", {})
    body_quarantine_path = PROJECT / str(body_package.get("quarantine_path", ""))
    if (not body_quarantine_path.is_file()
            or body_quarantine_path.stat().st_size != body_package.get("bytes")
            or body_quarantine_path.stat().st_mtime_ns != body_package.get("mtime_ns")
            or sha256(body_quarantine_path) != body_package.get("sha256")):
        fail("recovery v009 preserved v006 body-material evidence drift")
    verify_inventory(payload["prior_quarantines"]["v001_partial_packages"],
                     "preserved v001 partial-package quarantine")
    verify_inventory(payload["prior_quarantines"]["v002_partial_packages"],
                     "preserved v002 partial-package quarantine")
    verify_inventory(payload["prior_quarantines"]["v003_partial_packages"],
                     "preserved v003 partial-package quarantine")
    verify_inventory(payload["prior_quarantines"]["v004_partial_packages"],
                     "preserved v004 partial-package quarantine")
    verify_inventory(payload["prior_quarantines"]["v005_partial_packages"],
                     "preserved v005 partial-package quarantine")
    verify_inventory(payload["lane"], "recovery v009 prepared lane")

    rules = payload.get("slot_normalization", {})
    if set(rules) != set(baseline.get("modules", {})):
        fail("recovery v006 exact slot-normalization role closure drift")
    special_role = "BIW_AutomotiveSkeleton"
    for role, spec in baseline["modules"].items():
        rule = rules.get(role, {})
        expected_slots = spec.get("material_slots", [])
        if (len(expected_slots) != 1
                or rule.get("canonical_material_slot_name") != expected_slots[0]
                or rule.get("required_static_material_count") != 1
                or rule.get("source_occurrence_count_by_lod") != [1, 1, 1]):
            fail("recovery v006 slot-normalization semantic/count drift: " + role)
        if role == special_role:
            if (rule.get("source_fbx_material_name")
                    != "MI_LB_C2040_BIW_GalvanisedSteel_v005.001"
                    or rule.get("ue_imported_material_slot_name")
                    != "MI_LB_C2040_BIW_GalvanisedSteel_v005_001"
                    or rule.get("normalize_gameplay_material_slot_name") is not True):
                fail("recovery v006 BIW deterministic dot-to-underscore rule drift")
        elif (rule.get("source_fbx_material_name") != expected_slots[0]
                or rule.get("ue_imported_material_slot_name") != expected_slots[0]
                or rule.get("normalize_gameplay_material_slot_name") is not False):
            fail("recovery v006 unexpected material-slot normalization: " + role)

    uv_authority = payload.get("runtime_uv_sanitization", {})
    uv_roles = uv_authority.get("roles", {})
    engine = uv_authority.get("engine_source", {})
    if (set(uv_roles) != set(baseline.get("modules", {}))
            or engine.get("sha256")
            != "D6E42F80894F87E580DD72FC2EE7F9A46E312DDE1AB006F18F01A068408523C6"
            or engine.get("lines") != "709-718"):
        fail("recovery v006 UE5.8 runtime-UV sanitation authority drift")
    for role, spec in baseline["modules"].items():
        source_uvs = [int(lod["uv_channels"]) for lod in spec["lods"]]
        expected_runtime = [max(1, value) for value in source_uvs]
        forced = [value == 0 for value in source_uvs]
        uv_rule = uv_roles.get(role, {})
        if (uv_rule.get("source_uv_channels_by_lod") != source_uvs
                or uv_rule.get("expected_unreal_uv_channels_by_lod") != expected_runtime
                or uv_rule.get("ue_forced_minimum_one_by_lod") != forced):
            fail("recovery v006 exact source/runtime UV rule drift: " + role)
        if role in {"BIW_AutomotiveSkeleton", "BIW_UnderbodySubset"}:
            if source_uvs != [0, 0, 0] or expected_runtime != [1, 1, 1]:
                fail("recovery v006 zero-source-UV BIW closure drift: " + role)
        elif source_uvs != [1, 1, 1] or expected_runtime != [1, 1, 1]:
            fail("recovery v006 textured runtime-UV closure drift: " + role)
    observed = uv_authority.get("v003_observed_biw_automotive_skeleton_lod0", {})
    if (observed.get("expected_triangles") != 59998
            or observed.get("actual_triangles") != 59998
            or observed.get("source_vertices") != 29092
            or observed.get("actual_render_vertices") != 29109
            or observed.get("expected_source_uv_channels") != 0
            or observed.get("actual_unreal_uv_channels") != 1
            or observed.get("triangle_or_degenerate_removal_drift") is not False):
        fail("recovery v006 inherited observed v003 LOD0 metric proof drift")

    bounds_authority = payload.get("runtime_bounds_coordinate_conversion", {})
    bounds_roles = bounds_authority.get("roles", {})
    engine_sources = bounds_authority.get("engine_sources", {})
    fbx_converter = engine_sources.get("fbx_position_converter", {})
    bounds_serializer = engine_sources.get("bounds_serializer", {})
    if (bounds_authority.get("coordinate_rule")
            != "Unreal = (source X, -source Y, source Z)"
            or bounds_authority.get("bounds_rule")
            != "min=(minX,-maxY,minZ); max=(maxX,-minY,maxZ)"
            or float(bounds_authority.get("comparison_tolerance_cm", -1.0)) != 0.25
            or bounds_authority.get("tolerance_relaxed") is not False
            or bounds_authority.get("source_or_fbx_modified") is not False
            or set(bounds_roles) != set(baseline.get("modules", {}))
            or fbx_converter.get("sha256")
            != "E96AF266A819FD61B94F637253C409B98312B13B24E32B1E873CB4AB45481FB2"
            or fbx_converter.get("lines") != "63-71"
            or bounds_serializer.get("sha256")
            != "690FB6D64A5375CAF53635FC1EFE210FED8C9D2679C5A2F864D08F742085198B"
            or bounds_serializer.get("lines") != "406-410"):
        fail("recovery v006 UE5.8 runtime-bounds conversion authority drift")
    for engine_label, engine_row in (
            ("FBX position converter", fbx_converter),
            ("bounds serializer", bounds_serializer)):
        engine_path = Path(str(engine_row.get("path", "")))
        if not engine_path.is_file() or sha256(engine_path) != engine_row.get("sha256"):
            fail("recovery v006 installed engine-source drift: " + engine_label)
    for role, spec in baseline["modules"].items():
        rows = bounds_roles.get(role, {}).get("lods", [])
        if len(rows) != 3:
            fail("recovery v006 bounds role/LOD closure drift: " + role)
        for index, lod in enumerate(spec["lods"]):
            source = lod["expected_unreal_bounds"]
            converted = source_bounds_to_unreal(source)
            row = rows[index]
            if (row.get("lod") != index
                    or row.get("frozen_source_bounds_cm") != source
                    or row.get("expected_unreal_bounds_cm") != converted
                    or converted["dimensions_cm"] != source["dimensions_cm"]
                    or converted["pivot_cm"] != [0.0, 0.0, 0.0]):
                fail(f"recovery v006 exact source-to-Unreal bounds drift: {role}:LOD{index}")
    forensic = bounds_authority.get("v004_underbody_lod0_failure_forensics", {})
    current_observed = forensic.get("v004_preserved_package", {})
    if (forensic.get("classification")
            != "DETERMINISTIC_UE5_8_FBX_HANDEDNESS_CONVERSION__FROZEN_CONTRACT_WAS_SOURCE_SPACE__NO_TRANSFORM_OR_GEOMETRY_DRIFT"
            or current_observed.get("package", {}).get("sha256")
            != "DEF91E57144420980F5C07089B2A2625ABD31BEE40C7ED8B64DDE04E4FCFF858"
            or current_observed.get("origin_byte_offset") != 15767
            or current_observed.get("box_extent_byte_offset") != 15840
            or current_observed.get("origin_cm")
            != [0.0123748779296875, 0.48571014404296875, 41.680776596069336]
            or current_observed.get("box_extent_cm")
            != [226.0, 79.58294677734375, 33.06645393371582]
            or float(forensic.get("source_space_y_endpoint_mismatch_cm", 0.0)) <= 0.25):
        fail("recovery v006 preserved Underbody bounds forensics drift")

    # Destination topology is process-specific: the importer requires absence before
    # creation, while the distinct validator requires the completed 11-package root.
    # Shared recovery loading therefore verifies only immutable authorities/quarantine.
    quarantine_root = (PROJECT / str(quarantine.get("destination_root", ""))).resolve()
    expected_files = payload.get("partial_packages", {})
    if not quarantine_root.is_dir() or len(expected_files) != 11:
        fail("recovery v009 quarantine root/partial closure drift")
    actual_paths = {
        relative(path) for path in quarantine_root.rglob("*") if path.is_file()
    }
    expected_paths = {
        str(row.get("quarantine_path", "")) for row in expected_files.values()
        if isinstance(row, dict)
    }
    if actual_paths != expected_paths:
        fail("recovery v009 quarantine file closure drift")
    for source_path, row in expected_files.items():
        if not isinstance(row, dict) or row.get("source_path") != source_path:
            fail("recovery v009 partial-package path mapping drift")
        actual = file_row(PROJECT / row["quarantine_path"])
        if any(actual[key] != row.get(key) for key in ("bytes", "mtime_ns", "sha256")):
            fail("recovery v009 quarantined partial-package hash drift: " + source_path)
    return payload, digest


def require_quarantine_receipt(recovery: dict, recovery_digest: str) -> dict:
    path = run_root() / QUARANTINE_RECEIPT
    if not path.is_file():
        fail("recovery v009 quarantine receipt is absent")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (payload.get("$schema")
            != "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v009/quarantine/v9"
            or payload.get("status")
            != "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_PARTIALS_QUARANTINED"
            or payload.get("recovery_contract_sha256") != recovery_digest
            or payload.get("v001_failed_run_id") != EXPECTED_V001_FAILED_RUN_ID
            or payload.get("v001_import_failure_sha256")
            != EXPECTED_V001_IMPORT_FAILURE_SHA256
            or payload.get("v002_failed_run_id") != EXPECTED_V002_FAILED_RUN_ID
            or payload.get("v002_import_failure_sha256")
            != EXPECTED_V002_IMPORT_FAILURE_SHA256
            or payload.get("v003_failed_run_id") != EXPECTED_V003_FAILED_RUN_ID
            or payload.get("v003_import_failure_sha256")
            != EXPECTED_V003_IMPORT_FAILURE_SHA256
            or payload.get("v004_failed_run_id") != EXPECTED_V004_FAILED_RUN_ID
            or payload.get("v004_import_failure_sha256")
            != EXPECTED_V004_IMPORT_FAILURE_SHA256
            or payload.get("v005_failed_run_id") != EXPECTED_V005_FAILED_RUN_ID
            or payload.get("v005_import_failure_sha256")
            != EXPECTED_V005_IMPORT_FAILURE_SHA256
            or payload.get("v006_failed_run_id") != EXPECTED_V006_FAILED_RUN_ID
            or payload.get("v006_import_failure_sha256")
            != EXPECTED_V006_IMPORT_FAILURE_SHA256
            or payload.get("incident_chain_sha256")
            != recovery.get("incident_chain", {}).get("binding_sha256")
            or payload.get("operation") != "MOVE_DIRECTORY_ONLY__NO_DELETE"
            or payload.get("source_destination_absent_after_move") is not True
            or payload.get("quarantined_partial_packages")
            != recovery.get("partial_packages")):
        fail("recovery v009 quarantine receipt identity/hash drift")
    return {
        "path": relative(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "status": payload["status"],
        "incident_chain_sha256": payload["incident_chain_sha256"],
    }


def run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw or os.environ.get(ACK_ENV, "").strip() != ACK_TOKEN:
        fail("guarded runner environment or acknowledgement absent")
    path = Path(raw).resolve()
    if path == AUDIT_ROOT.resolve() or not inside(path, AUDIT_ROOT) or not path.is_dir():
        fail("run root escapes or is absent: " + str(path))
    return path


def require_engine_entry_bootstrap_world() -> str:
    command_line = str(unreal.SystemLibrary.get_command_line())
    if EXPECTED_MAPLESS_STARTUP_OVERRIDE not in command_line:
        fail("exact transient LoadLevelAtStartup=None command-line override is absent")
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_editor_world() if subsystem else None
    path = world.get_path_name() if world else ""
    if path != "/Engine/Maps/Entry.Entry":
        fail(
            "vehicle lane must bootstrap only the immutable Engine Entry world; "
            "actual world: " + path
        )
    return path


def load_contract() -> tuple[dict, str]:
    digest = sidecar_hash(CONTRACT, CONTRACT_SHA, "approved final authority contract")
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    destination = payload.get("destination", {})
    provenance = payload.get("provenance", {})
    provenance_description = str(provenance.get("description", ""))
    selected_candidate = str(provenance.get("selected_candidate", ""))
    selected_version = str(provenance.get("selected_version", ""))
    manifest_relative = str(provenance.get("manifest", {}).get("path", ""))
    paint_mask_raw = payload.get("paint_mask_authority", {})
    paint_mask = paint_mask_raw if isinstance(paint_mask_raw, dict) else {}
    supersession_raw = payload.get("approval_supersession", {})
    supersession = supersession_raw if isinstance(supersession_raw, dict) else {}
    if (payload.get("$schema") != "lineboss/cairnwell-2040-runtime-v001/unreal-import-contract/v1"
            or payload.get("status") != EXPECTED_CONTRACT_STATUS
            or destination.get("namespace") != DEST
            or destination.get("expected_mesh_count") != 4
            or destination.get("expected_texture_count") != 3
            or destination.get("expected_material_count") != 4
            or destination.get("expected_package_count") != 11
            or destination.get("expected_source_fbx_count") != 12
            or "meshy-derived" not in provenance_description.casefold()
            or "native" in provenance_description.casefold()
            or selected_version != "v005"
            or selected_candidate != "ProductionCandidate_v005"
            or manifest_relative != EXPECTED_MANIFEST_RELATIVE
            or payload.get("import_contract", {}).get("editor_bootstrap_world")
            != "/Engine/Maps/Entry.Entry"
            or payload.get("import_contract", {}).get("project_map_load_save_authorized")
            is not False
            or payload.get("import_contract", {}).get("editor_startup_map_override")
            != EXPECTED_MAPLESS_STARTUP_OVERRIDE
            or payload.get("policy", {}).get("overwrite_reimport_delete_authorized") is not False
            or payload.get("policy", {}).get(
                "panel_module_namespace_or_packages_authorized") is not False):
        fail("approved contract identity, provenance, destination, or safety drift")
    audit = paint_mask.get("audit", {})
    audit_path = str(audit.get("path", ""))
    source_files = provenance.get("source_files", [])
    source_by_path = {
        str(row.get("path", "")): row for row in source_files if isinstance(row, dict)
    }
    if (paint_mask.get("status") != EXPECTED_PAINT_MASK_STATUS
            or paint_mask.get("selected_version") != "v005"
            or paint_mask.get("texture_semantic") != "metallic_roughness"
            or paint_mask.get("channel") != "A"
            or paint_mask.get("manual_authored") is not True
            or paint_mask.get("v006_mask_reused") is not False
            or int(paint_mask.get("false_positive_fragment_count", -1)) != 0
            or not audit_path.startswith(EXPECTED_V005_ROOT_RELATIVE)
            or source_by_path.get(audit_path) != audit
            or len(source_by_path) != len(source_files)):
        fail("approved manually authored v005 body-paint-mask authority drift")
    supersession_record = supersession.get("record", {})
    supersession_evidence = supersession.get("evidence", {})
    supersession_renders = supersession.get("manual_paint_mask_renders", {})
    root_visual_approval = supersession.get("root_visual_approval", {})
    amendment_raw = supersession.get("freeze_amendment", {})
    amendment = amendment_raw if isinstance(amendment_raw, dict) else {}
    amendment_record = amendment.get("record", {})
    stale_receipt = amendment.get("stale_v1_receipt", {})
    current_supersession = amendment.get("current_supersession", {})
    amendment_incident = amendment.get("declared_post_v1_incident", {})
    if (supersession.get("status") != EXPECTED_SUPERSESSION_STATUS
            or supersession.get("selected_candidate") != "ProductionCandidate_v005"
            or supersession.get("selected_version") != "v005"
            or supersession.get("historical_marker_preserved_byte_exact") is not True
            or supersession.get("supersedes_historical_marker_without_deletion") is not True
            or supersession.get("unreal_import_or_promotion_performed") is not False
            or not isinstance(root_visual_approval, dict)
            or root_visual_approval.get("status") != "PASS"
            or int(root_visual_approval.get(
                "visible_isolated_false_positive_regions", -1)) != 0
            or root_visual_approval.get("painted_roof_and_body_included") is not True
            or root_visual_approval.get(
                "glazing_lamps_trim_diffuser_and_wheels_excluded") is not True
            or not isinstance(supersession_record, dict)
            or supersession_record.get("path") != EXPECTED_SUPERSESSION_RECORD_RELATIVE
            or source_by_path.get(EXPECTED_SUPERSESSION_RECORD_RELATIVE)
            != supersession_record
            or not isinstance(supersession_evidence, dict)
            or set(supersession_evidence) != set(EXPECTED_SUPERSESSION_EVIDENCE_PATHS)
            or any(not isinstance(row, dict) for row in supersession_evidence.values())
            or any(supersession_evidence[key].get("path") != path
                   for key, path in EXPECTED_SUPERSESSION_EVIDENCE_PATHS.items())
            or any(source_by_path.get(row.get("path", "")) != row
                   for row in supersession_evidence.values())
            or not isinstance(supersession_renders, dict)
            or set(supersession_renders) != set(EXPECTED_SUPERSESSION_RENDER_PATHS)
            or any(not isinstance(row, dict) for row in supersession_renders.values())
            or any(supersession_renders[key].get("path") != path
                   for key, path in EXPECTED_SUPERSESSION_RENDER_PATHS.items())
            or any(source_by_path.get(row.get("path", "")) != row
                   for row in supersession_renders.values())
            or amendment.get("schema") != EXPECTED_FREEZE_AMENDMENT_SCHEMA
            or amendment.get("status") != EXPECTED_FREEZE_AMENDMENT_STATUS
            or amendment.get("selected_candidate") != "ProductionCandidate_v005"
            or amendment.get("selected_version") != "v005"
            or amendment.get("current_contract_authority") is not True
            or amendment.get("supersedes_stale_v1_receipt_without_modifying_it") is not True
            or amendment.get("unreal_import_or_promotion_performed") is not False
            or amendment.get("preexisting_file_count") != 36
            or amendment.get("final_authority_and_additive_inventory_count") != 44
            or amendment.get("no_missing_files") is not True
            or amendment.get("no_unexpected_additions") is not True
            or amendment.get("no_other_changed_files") is not True
            or not isinstance(amendment_record, dict)
            or amendment_record.get("path") != EXPECTED_FREEZE_AMENDMENT_RECORD_RELATIVE
            or amendment_record.get("sha256") != EXPECTED_FREEZE_AMENDMENT_SHA256
            or amendment_record.get("bytes") != 24420
            or source_by_path.get(EXPECTED_FREEZE_AMENDMENT_RECORD_RELATIVE)
            != amendment_record
            or not isinstance(stale_receipt, dict)
            or stale_receipt.get("path") != EXPECTED_STALE_FREEZE_RECEIPT_RELATIVE
            or stale_receipt.get("sha256") != EXPECTED_STALE_FREEZE_RECEIPT_SHA256
            or stale_receipt.get("bytes") != 24570
            or source_by_path.get(EXPECTED_STALE_FREEZE_RECEIPT_RELATIVE) != stale_receipt
            or not isinstance(current_supersession, dict)
            or current_supersession != supersession_record
            or current_supersession.get("sha256") != EXPECTED_CURRENT_SUPERSESSION_SHA256
            or current_supersession.get("bytes") != 3319
            or not isinstance(amendment_incident, dict)
            or amendment_incident.get("current_expected_sha256")
            != EXPECTED_CURRENT_SUPERSESSION_SHA256
            or amendment_incident.get("v1_pinned_state", {}).get("sha256")
            != EXPECTED_STALE_V1_SUPERSESSION_SHA256
            or amendment_incident.get("sole_change") != (
                "JSON key `schema` corrected to `$schema`; value and every other "
                "semantic/evidence field retained."
            )):
        fail("historical v005 marker/final approval supersession closure drift")
    if not DEST.startswith("/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"):
        fail("destination escaped the OneFactory vehicle namespace")
    modules = payload.get("modules", {})
    materials = payload.get("materials", {})
    textures = payload.get("textures", {})
    if ({role: spec.get("asset_name") for role, spec in modules.items()}
            != EXPECTED_MESH_NAMES):
        fail("frozen runtime mesh asset-name seam drift")
    if ({key: (spec.get("asset_name"), spec.get("recipe"))
            for key, spec in materials.items()} != EXPECTED_MATERIAL_IDENTITIES):
        fail("frozen runtime material asset-name/recipe seam drift")
    material_paths_by_key = {key: spec["object_path"] for key, spec in materials.items()}
    for role, expected_key in EXPECTED_ROLE_MATERIAL.items():
        if set(modules[role]["material_bindings"].values()) != {
                material_paths_by_key[expected_key]}:
            fail("frozen module/material authority binding drift: " + role)
    body = materials["body"]
    if (body.get("parameter_name") != "VehiclePaintColour"
            or body.get("parameter_output") != "RGB"
            or body.get("detail_luminance_weights") != [0.2126, 0.7152, 0.0722]
            or body.get("detail_normalization") != 1.35
            or body.get("detail_clamp_min") != 0.35
            or body.get("detail_clamp_max") != 1.15
            or body.get("paint_mask_texture_semantic") != "metallic_roughness"
            or body.get("paint_mask_channel") != "A"
            or body.get("paint_mask_target_input") != "Alpha"):
        fail("frozen player-selectable paint parameter/mask seam drift")
    if (modules["EmeraldBodyVisualAuthority"].get("closed_body_shell") is not True
            or modules["EmeraldRollingGearVisualAuthority"].get(
                "semantic_object_count_before_combined_import") != 8):
        fail("frozen closed-body/eight-part rolling-gear source topology drift")
    imported_source_paths = [
        str(lod.get("source", {}).get("path", ""))
        for spec in modules.values() for lod in spec.get("lods", [])
    ] + [
        str(spec.get("source", {}).get("path", "")) for spec in textures.values()
    ]
    if (len(imported_source_paths) != 15
            or len(set(imported_source_paths)) != 15
            or any(not path.startswith(EXPECTED_V005_ROOT_RELATIVE)
                   for path in imported_source_paths)
            or any("ProductionCandidate_v006" in path for path in imported_source_paths)):
        fail("exact distinct v005-only imported source closure drift")
    if (supersession_evidence["approved_manifest"] != provenance.get("manifest")
            or supersession_evidence["manual_paint_mask_audit"] != paint_mask["audit"]
            or supersession_evidence["manual_paint_mask_texture"]
            != textures["metallic_roughness"]["source"]):
        fail("v005 supersession does not bind the runtime manifest/manual-mask closure")
    return payload, digest


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("running project identity drift")
    contract, contract_digest = load_contract()
    baseline_digest = sidecar_hash(BASELINE, BASELINE_SHA, "project baseline")
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    if (payload.get("$schema") != "lineboss/cairnwell-2040-runtime-v001/unreal-import-baseline/v1"
            or payload.get("status") != EXPECTED_BASELINE_STATUS
            or payload.get("contract", {}).get("sha256") != contract_digest
            or payload.get("destination") != contract.get("destination")
            or payload.get("shared_datum") != contract.get("shared_datum")
            or payload.get("import_contract") != contract.get("import_contract")
            or payload.get("modules") != contract.get("modules")
            or payload.get("textures") != contract.get("textures")
            or payload.get("materials") != contract.get("materials")
            or payload.get("paint_mask_authority") != contract.get("paint_mask_authority")
            or payload.get("approval_supersession") != contract.get("approval_supersession")
            or payload.get("policy") != contract.get("policy")):
        fail("frozen baseline identity or approved contract drift")
    payload["_baseline_sha256"] = baseline_digest
    payload["_contract_sha256"] = contract_digest
    recovery, recovery_digest = load_recovery_contract(
        payload, contract_digest, baseline_digest)
    payload["_recovery"] = recovery
    payload["_recovery_contract_sha256"] = recovery_digest
    return payload


def verify_inventory(snapshot: dict, label: str) -> dict:
    rows = []
    for expected in snapshot["files"]:
        actual = file_row(PROJECT / expected["path"])
        if any(actual[key] != expected[key] for key in ("path", "bytes", "mtime_ns", "sha256")):
            fail(f"{label} file drift: {expected['path']}")
        rows.append(actual)
    digest = canonical_hash(rows)
    if len(rows) != int(snapshot["file_count"]) or digest != snapshot["inventory_sha256"]:
        fail(label + " inventory drift")
    return {"file_count": len(rows), "inventory_sha256": digest}


def verify_exact_directory_snapshot(snapshot: dict, label: str) -> dict:
    root = (PROJECT / str(snapshot.get("root", ""))).resolve()
    if not root.is_dir() or not inside(root, PROJECT):
        fail(label + " exact root absent or escapes project")
    actual_paths = {
        relative(path) for path in root.rglob("*") if path.is_file()
    }
    expected_paths = {
        str(row.get("path", "")) for row in snapshot.get("files", [])
    }
    if (actual_paths != expected_paths
            or len(actual_paths) != int(snapshot.get("file_count", -1))):
        fail_expected_actual(
            label + " exact all-file closure drift",
            {"file_count": len(expected_paths), "paths": sorted(expected_paths)},
            {"file_count": len(actual_paths), "paths": sorted(actual_paths)},
            ["file_count_or_paths"],
        )
    return verify_inventory(snapshot, label)


def verify_source(baseline: dict) -> dict:
    return verify_inventory(baseline["source"], "approved selected-authority source")


def verify_protected(baseline: dict) -> dict:
    protected = baseline["protected"]
    actual_union = set()
    for group in protected["groups"]:
        selected = {PROJECT / rel for rel in group.get("files", [])}
        for rel in group.get("roots", []):
            root = PROJECT / rel
            if not root.is_dir():
                if group.get("allow_empty"):
                    continue
                fail("protected root missing: " + rel)
            selected.update(path for path in root.rglob("*") if path.is_file())
        exclusions = [PROJECT / rel for rel in group.get("excludes", [])]
        selected = {
            path for path in selected
            if not any(path.resolve() == excluded.resolve() or inside(path, excluded)
                       for excluded in exclusions)
        }
        paths = {relative(path) for path in selected}
        if paths != set(group["paths"]):
            fail("protected group path inventory drift: " + group["name"])
        actual_union.update(paths)
    if actual_union != {row["path"] for row in protected["files"]}:
        fail("protected group union drift")
    return verify_inventory(protected, "protected project")


def verify_lane(baseline: dict) -> dict:
    recovery = baseline.get("_recovery", {})
    if not isinstance(recovery, dict) or "lane" not in recovery:
        fail("incident-chained recovery v006 lane snapshot is absent")
    return verify_inventory(recovery["lane"], "prepared recovery v006 vehicle lane")


def namespace_inventory() -> dict:
    if not DEST_DISK.is_dir():
        return {}
    return {
        row["path"]: {"bytes": row["bytes"], "mtime_ns": row["mtime_ns"], "sha256": row["sha256"]}
        for row in (
            file_row(path) for path in sorted(DEST_DISK.rglob("*"), key=lambda p: str(p).casefold())
            if path.is_file()
        )
    }


def package_hashes(baseline: dict) -> dict[str, str]:
    output = {}
    expected = baseline["destination"]["expected_package_paths"]
    for package in expected:
        path = PROJECT / ("Content/" + package.removeprefix("/Game/") + ".uasset")
        if not path.is_file():
            fail("expected runtime package missing: " + package)
        output[package] = sha256(path)
    actual_uassets = sorted(DEST_DISK.rglob("*.uasset"), key=lambda path: str(path).casefold())
    if len(actual_uassets) != len(expected):
        fail("destination package count is not exact")
    actual_packages = {
        "/Game/" + path.relative_to(PROJECT / "Content").with_suffix("").as_posix()
        for path in actual_uassets
    }
    if actual_packages != set(expected):
        fail("destination package path closure is not exact")
    return output


def prior_results() -> list[str]:
    current = run_root()
    return sorted(
        relative(path) for path in current.rglob("*")
        if path.is_file() and path.name in RESULT_NAMES
    )


def vector(value) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def lod_bounds(mesh, lod_index: int) -> dict:
    dynamic = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    request = unreal.GeometryScriptMeshReadLOD()
    request.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": lod_index,
    })
    dynamic, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic, options, request, False
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail(f"source LOD bounds extraction failed: {mesh.get_name()}:LOD{lod_index}")
    box = dynamic.get_mesh_bounding_box()
    minimum, maximum = vector(box.min), vector(box.max)
    return {
        "minimum_cm": minimum,
        "maximum_cm": maximum,
        "dimensions_cm": [maximum[index] - minimum[index] for index in range(3)],
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def assert_bounds(actual: dict, expected: dict, tolerance: float, label: str) -> None:
    for field in ("minimum_cm", "maximum_cm", "dimensions_cm", "pivot_cm"):
        deltas = [
            abs(float(actual[field][index]) - float(expected[field][index]))
            for index in range(3)
        ]
        if max(deltas) > tolerance:
            fail_expected_actual(
                f"{label} bounds/shared-pivot drift",
                {"field": field, "value_cm": expected[field], "tolerance_cm": tolerance},
                {"field": field, "value_cm": actual[field], "absolute_delta_cm": deltas},
                [field],
            )


def slot_names(mesh) -> list[str]:
    return [
        str(row.get_editor_property("material_slot_name"))
        for row in mesh.get_editor_property("static_materials")
    ]


def imported_slot_names(mesh) -> list[str]:
    return [
        str(row.get_editor_property("imported_material_slot_name"))
        for row in mesh.get_editor_property("static_materials")
    ]


def section_slots(mesh, subsystem, lod_index: int, slots: list[str]) -> list[str]:
    output = []
    for section in range(int(mesh.get_num_sections(lod_index))):
        index = int(subsystem.get_lod_material_slot(mesh, lod_index, section))
        if index < 0 or index >= len(slots):
            fail(f"section/material index invalid: {mesh.get_name()}:LOD{lod_index}")
        output.append(slots[index])
    return output


def legacy_import_data(mesh) -> dict:
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
        fail("legacy FBX import-setting drift: " + mesh.get_name() + repr(output))
    return output


def validate_mesh(role: str, spec: dict, baseline: dict, subsystem,
                  require_persisted_dependencies: bool) -> dict:
    mesh = library.load_asset(spec["package_path"])
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
        fail("StaticMesh/object identity drift: " + role)
    if int(mesh.get_num_lods()) != 3:
        fail("authored LOD count drift: " + role)
    screens = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
    if screens != baseline["import_contract"]["lod_screen_sizes"] or mesh.is_lod_screen_size_auto_computed():
        fail("manual LOD screen-size drift: " + role)
    slots = slot_names(mesh)
    if slots != spec["material_slots"]:
        fail("global semantic material-slot drift: " + role + repr(slots))
    imported_slots = imported_slot_names(mesh)
    slot_rule = baseline["_recovery"]["slot_normalization"][role]
    if imported_slots != [slot_rule["ue_imported_material_slot_name"]]:
        fail("imported source material-slot identity drift: " + role + repr(imported_slots))
    bound_materials = {
        slot: (mesh.get_material(index).get_path_name() if mesh.get_material(index) else None)
        for index, slot in enumerate(slots)
    }
    if bound_materials != spec["material_bindings"]:
        fail("exact material binding drift: " + role + repr(bound_materials))
    lods = []
    for index, expected in enumerate(spec["lods"]):
        triangles = int(mesh.get_num_triangles(index))
        vertices = int(mesh.get_num_vertices(index))
        uv_channels = int(mesh.get_num_tex_coords(index))
        runtime_uv_rule = baseline["_recovery"]["runtime_uv_sanitization"]["roles"][role]
        expected_unreal_uv_channels = int(
            runtime_uv_rule["expected_unreal_uv_channels_by_lod"][index])
        if int(runtime_uv_rule["source_uv_channels_by_lod"][index]) != int(
                expected["uv_channels"]):
            fail(f"source UV authority drift: {role}:LOD{index}")
        bounds = lod_bounds(mesh, index)
        geometry_expected = {
            "triangles": int(expected["triangles"]),
            "source_vertices_positive": True,
            "render_vertices_positive": True,
            "unreal_uv_channels": expected_unreal_uv_channels,
        }
        geometry_actual = {
            "triangles": triangles,
            "source_vertices": int(expected["source_vertices"]),
            "source_vertices_positive": int(expected["source_vertices"]) > 0,
            "render_vertices": vertices,
            "render_vertices_positive": vertices > 0,
            "unreal_uv_channels": uv_channels,
        }
        geometry_mismatches = [
            field for field, matches in {
                "triangles": triangles == geometry_expected["triangles"],
                "source_vertices_positive": geometry_actual["source_vertices_positive"],
                "render_vertices_positive": geometry_actual["render_vertices_positive"],
                "unreal_uv_channels": uv_channels == expected_unreal_uv_channels,
            }.items() if not matches
        ]
        if geometry_mismatches:
            fail_expected_actual(
                f"triangle/positive-vertex/UV drift: {role}:LOD{index}",
                geometry_expected, geometry_actual, geometry_mismatches)
        runtime_bounds_rule = baseline["_recovery"][
            "runtime_bounds_coordinate_conversion"]["roles"][role]["lods"][index]
        if (runtime_bounds_rule["lod"] != index
                or runtime_bounds_rule["frozen_source_bounds_cm"]
                != expected["expected_unreal_bounds"]):
            fail(f"runtime bounds authority binding drift: {role}:LOD{index}")
        assert_bounds(
            bounds,
            runtime_bounds_rule["expected_unreal_bounds_cm"],
            float(baseline["import_contract"]["bounds_tolerance_cm"]),
            f"{role}:LOD{index}",
        )
        sections = section_slots(mesh, subsystem, index, slots)
        if sections != expected["material_slots"]:
            fail(f"section/material semantic drift: {role}:LOD{index}:{sections}")
        lods.append({
            "lod": index,
            "triangles": triangles,
            "vertices": vertices,
            "source_vertices": int(expected["source_vertices"]),
            "source_uv_channels": int(expected["uv_channels"]),
            "uv_channels": uv_channels,
            "bounds": bounds,
            "section_material_slots": sections,
        })
    chain = [row["triangles"] for row in lods]
    if chain != spec["triangle_chain"] or not chain[0] > chain[1] > chain[2] > 0:
        fail("strict authored LOD chain drift: " + role)
    simple = int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh))
    convex = int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh))
    body = mesh.get_editor_property("body_setup")
    trace_value = body.get_editor_property("collision_trace_flag") if body else None
    trace = (
        canonical_enum_name(trace_value, COLLISION_TRACE_BY_NAME, role + ":collision_trace_flag")
        if trace_value is not None else "NONE"
    )
    nanite = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    has_navigation_data = bool(mesh.get_editor_property("has_navigation_data"))
    collision_expected = {
        "simple_collision_count": 0,
        "convex_collision_count": 0,
        "collision_trace_flag": "CTF_USE_SIMPLE_AS_COMPLEX",
        "nanite_enabled": False,
        "has_navigation_data": False,
    }
    collision_actual = {
        "simple_collision_count": simple,
        "convex_collision_count": convex,
        "collision_trace_flag": trace,
        "nanite_enabled": nanite,
        "has_navigation_data": has_navigation_data,
    }
    collision_mismatches = [
        field for field in collision_expected
        if collision_actual[field] != collision_expected[field]
    ]
    if collision_mismatches:
        fail_expected_actual(
            f"collision/navigation/Nanite drift: {role}",
            collision_expected, collision_actual, collision_mismatches)
    expected_dependencies = {
        path.split(".", 1)[0] for path in spec["material_bindings"].values()
    }
    actual_dependencies = {
        path for path in project_dependencies(spec["package_path"])
        if path.startswith(DEST + "/")
    }
    if require_persisted_dependencies and actual_dependencies != expected_dependencies:
        fail(f"persisted mesh/material dependency closure drift: {role}:{actual_dependencies}")
    return {
        "role": role,
        "object_path": mesh.get_path_name(),
        "lod_count": 3,
        "lod_screen_sizes": screens,
        "lod_screen_size_auto_computed": False,
        "lods": lods,
        "triangle_chain": chain,
        "strict_monotonic_triangles": True,
        "material_slots": slots,
        "imported_material_slots": imported_slots,
        "slot_normalization_rule": slot_rule,
        "bound_materials": bound_materials,
        "simple_collision_count": simple,
        "convex_collision_count": convex,
        "collision_trace_flag": trace,
        "nanite_enabled": nanite,
        "has_navigation_data": has_navigation_data,
        "legacy_import_data": legacy_import_data(mesh),
        "expected_runtime_dependencies": sorted(expected_dependencies, key=str.casefold),
        "persisted_runtime_dependencies": sorted(actual_dependencies, key=str.casefold),
        "persisted_dependency_check_required": require_persisted_dependencies,
    }


def validate_texture(semantic: str, spec: dict,
                     require_persisted_dependencies: bool) -> dict:
    texture = library.load_asset(spec["package_path"])
    if not isinstance(texture, unreal.Texture2D) or texture.get_path_name() != spec["object_path"]:
        fail("Texture2D/object identity drift: " + semantic)
    width, height = int(texture.blueprint_get_size_x()), int(texture.blueprint_get_size_y())
    srgb = bool(texture.get_editor_property("srgb"))
    compression_value = texture.get_editor_property("compression_settings")
    compression = canonical_enum_name(
        compression_value, TEXTURE_COMPRESSION_BY_NAME,
        semantic + ":compression_settings")
    flip_green = bool(texture.get_editor_property("flip_green_channel"))
    expected = {
        "dimensions": [int(spec["width"]), int(spec["height"])],
        "srgb": bool(spec["srgb"]),
        "compression": str(spec["compression"]),
        "flip_green_channel": bool(spec["flip_green_channel"]),
    }
    actual = {
        "dimensions": [width, height],
        "srgb": srgb,
        "compression": compression,
        "compression_runtime_repr": repr(compression_value),
        "flip_green_channel": flip_green,
    }
    texture_mismatches = [
        field for field in expected
        if actual[field] != expected[field]
    ]
    if texture_mismatches:
        fail_expected_actual(
            f"texture dimensions/colour/compression drift: {semantic}",
            expected, actual, texture_mismatches)
    actual_dependencies = {
        path for path in project_dependencies(spec["package_path"])
        if path.startswith(DEST + "/")
    }
    if require_persisted_dependencies and actual_dependencies:
        fail(f"runtime texture unexpectedly depends on another lane package: {semantic}")
    return {
        "semantic": semantic,
        "object_path": texture.get_path_name(),
        "dimensions": [width, height],
        "source_channels": int(spec["channels"]),
        "source_colorspace": spec["source_colorspace"],
        "srgb": srgb,
        "compression": compression,
        "compression_runtime_repr": repr(compression_value),
        "flip_green_channel": flip_green,
        "channel_mapping": spec["channel_mapping"],
        "normal_convention": spec.get("normal_convention"),
        "persisted_runtime_dependencies": sorted(actual_dependencies, key=str.casefold),
        "persisted_dependency_check_required": require_persisted_dependencies,
    }


def project_dependencies(package: str) -> set[str]:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False,
    )
    return {
        str(value) for value in (registry.get_dependencies(package, options) or [])
        if str(value).startswith("/Game/")
    }


def material_input(material, prop) -> dict:
    node = unreal.MaterialEditingLibrary.get_material_property_input_node(material, prop)
    output_name = str(
        unreal.MaterialEditingLibrary.get_material_property_input_node_output_name(material, prop)
    )
    result = {"class": node.get_class().get_name() if node else None,
              "output": output_name}
    if node:
        for name in ("constant", "r", "texture", "sampler_type"):
            try:
                value = node.get_editor_property(name)
                if hasattr(value, "get_path_name"):
                    value = value.get_path_name()
                elif hasattr(value, "to_tuple"):
                    value = list(value.to_tuple())
                elif name == "sampler_type":
                    value = canonical_enum_name(
                        value, MATERIAL_SAMPLER_BY_NAME,
                        node.get_name() + ":sampler_type")
                else:
                    value = float(value)
                result[name] = value
            except RuntimeError:
                raise
            except Exception:
                pass
    return result


def node_record(node) -> dict:
    result = {"class": node.get_class().get_name() if node else None}
    if node:
        for name in (
                "texture", "sampler_type", "parameter_name", "default_value",
                "constant", "r", "min_default", "max_default", "clamp_mode"):
            try:
                value = node.get_editor_property(name)
                if hasattr(value, "get_path_name"):
                    value = value.get_path_name()
                elif hasattr(value, "to_tuple"):
                    value = list(value.to_tuple())
                elif name in {"r", "min_default", "max_default"}:
                    value = float(value)
                elif name == "sampler_type":
                    value = canonical_enum_name(
                        value, MATERIAL_SAMPLER_BY_NAME,
                        node.get_name() + ":sampler_type")
                elif name == "clamp_mode":
                    value = canonical_enum_name(
                        value, CLAMP_MODE_BY_NAME,
                        node.get_name() + ":clamp_mode")
                else:
                    value = str(value)
                result[name] = value
            except RuntimeError:
                raise
            except Exception:
                pass
    return result


def canonical_material_input_name(value) -> str:
    """Map UE's reflected NAME_None spelling to the logical empty first-input key."""
    if type(value) is not str:
        fail(
            "material expression input-name reflection type drift: expected exact str; "
            + "actual_type=" + type(value).__name__ + " actual_repr=" + repr(value)
        )
    if value == "":
        fail("UE5.8 reflected material input unexpectedly returned a raw empty string")
    return "" if value == "None" else value


def expression_links(material, expression) -> tuple[dict, dict]:
    reflected_names = list(
        unreal.MaterialEditingLibrary.get_material_expression_input_names(expression))
    expression_class = expression.get_class().get_name()
    expected_reflected_names = REFLECTED_MATERIAL_INPUT_NAMES_BY_CLASS.get(expression_class)
    if expected_reflected_names is None or reflected_names != expected_reflected_names:
        fail_expected_actual(
            "material expression exact reflected input-name order drift",
            {"class": expression_class,
             "reflected_input_names": expected_reflected_names},
            {"class": expression_class,
             "reflected_input_names": reflected_names},
            ["reflected_input_names"],
        )
    names = [canonical_material_input_name(value) for value in reflected_names]
    sources = list(
        unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, expression))
    if len(names) != len(sources):
        fail("material expression input/name cardinality drift: " + expression.get_name())
    if len(set(names)) != len(names):
        fail(
            "material expression duplicate canonical input-name drift: "
            + expression.get_name()
            + " raw=" + repr(reflected_names) + " canonical=" + repr(names)
        )
    raw = dict(zip(names, sources))
    records = {}
    for name, source in raw.items():
        record = node_record(source)
        record["output"] = str(
            unreal.MaterialEditingLibrary.get_input_node_output_name_for_material_expression(
                expression, source)
        ) if source else ""
        records[name] = record
    return raw, records


def assert_texture_record(record: dict, texture_path: str, output: str,
                          sampler: str, label: str) -> None:
    if (record.get("class") != "MaterialExpressionTextureSample"
            or record.get("texture") != texture_path
            or record.get("output") != output
            or record.get("sampler_type") != sampler):
        fail_expected_actual(
            f"exact texture/socket/sampler drift: {label}",
            {"class": "MaterialExpressionTextureSample", "texture": texture_path,
             "output": output, "sampler_type": sampler},
            record,
            [field for field, expected in {
                "class": "MaterialExpressionTextureSample", "texture": texture_path,
                "output": output, "sampler_type": sampler,
            }.items() if record.get(field) != expected],
        )


def validate_material(key: str, spec: dict,
                      require_persisted_dependencies: bool) -> dict:
    material = library.load_asset(spec["package_path"])
    if not isinstance(material, unreal.Material) or material.get_path_name() != spec["object_path"]:
        fail("Material/object identity drift: " + key)
    blend_mode = canonical_enum_name(
        material.get_editor_property("blend_mode"), BLEND_MODE_BY_NAME,
        key + ":blend_mode")
    material_domain = canonical_enum_name(
        material.get_editor_property("material_domain"), MATERIAL_DOMAIN_BY_NAME,
        key + ":material_domain")
    material_state_expected = {
        "blend_mode": "BLEND_OPAQUE",
        "material_domain": "MD_SURFACE",
        "two_sided": False,
    }
    material_state_actual = {
        "blend_mode": blend_mode,
        "material_domain": material_domain,
        "two_sided": bool(material.get_editor_property("two_sided")),
    }
    material_state_mismatches = [
        field for field in material_state_expected
        if material_state_actual[field] != material_state_expected[field]
    ]
    if material_state_mismatches:
        fail_expected_actual(
            "opaque surface material-state drift: " + key,
            material_state_expected, material_state_actual, material_state_mismatches)
    expected_dependencies = {
        path.split(".", 1)[0] for path in spec["texture_object_paths"].values()
    }
    actual_dependencies = {
        path for path in project_dependencies(spec["package_path"])
        if path.startswith(DEST + "/")
    }
    if require_persisted_dependencies and actual_dependencies != expected_dependencies:
        fail(f"persisted material/texture dependency closure drift: {key}:{actual_dependencies}")
    inputs = {
        "base_color": material_input(material, unreal.MaterialProperty.MP_BASE_COLOR),
        "metallic": material_input(material, unreal.MaterialProperty.MP_METALLIC),
        "roughness": material_input(material, unreal.MaterialProperty.MP_ROUGHNESS),
        "normal": material_input(material, unreal.MaterialProperty.MP_NORMAL),
    }
    unused_inputs = {
        "specular": material_input(material, unreal.MaterialProperty.MP_SPECULAR),
        "emissive": material_input(material, unreal.MaterialProperty.MP_EMISSIVE_COLOR),
        "opacity": material_input(material, unreal.MaterialProperty.MP_OPACITY),
        "opacity_mask": material_input(material, unreal.MaterialProperty.MP_OPACITY_MASK),
        "ambient_occlusion": material_input(
            material, unreal.MaterialProperty.MP_AMBIENT_OCCLUSION),
    }
    if any(record["class"] is not None for record in unused_inputs.values()):
        fail("material has an undeclared output connection: " + key + repr(unused_inputs))
    expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(material))
    expression_classes = sorted(node.get_class().get_name() for node in expressions)
    graph = {"expression_classes": expression_classes}
    if spec["recipe"] == "textured_pbr":
        if expression_classes != ["MaterialExpressionTextureSample"] * 3:
            fail("textured PBR expression inventory drift: " + key + repr(expression_classes))
        if not all(inputs[name]["class"] == "MaterialExpressionTextureSample"
                   for name in ("base_color", "metallic", "roughness", "normal")):
            fail("textured PBR graph input class drift: " + key)
        expected_inputs = {
            "base_color": {
                "texture": spec["texture_object_paths"]["base_color"],
                "output": "RGB",
                "sampler": "SAMPLERTYPE_COLOR",
            },
            "metallic": {
                "texture": spec["texture_object_paths"]["metallic_roughness"],
                "output": spec["metallic_channel"],
                "sampler": "SAMPLERTYPE_MASKS",
            },
            "roughness": {
                "texture": spec["texture_object_paths"]["metallic_roughness"],
                "output": spec["roughness_channel"],
                "sampler": "SAMPLERTYPE_MASKS",
            },
            "normal": {
                "texture": spec["texture_object_paths"]["normal"],
                "output": "RGB",
                "sampler": "SAMPLERTYPE_NORMAL",
            },
        }
        for input_name, expected in expected_inputs.items():
            actual = inputs[input_name]
            if (actual.get("texture") != expected["texture"]
                    or actual.get("output") != expected["output"]
                    or actual.get("sampler_type") != expected["sampler"]):
                fail_expected_actual(
                    f"textured PBR texture/socket/sampler drift: {key}:{input_name}",
                    {"texture": expected["texture"], "output": expected["output"],
                     "sampler_type": expected["sampler"]},
                    actual,
                    [field for field, value in {
                        "texture": expected["texture"], "output": expected["output"],
                        "sampler_type": expected["sampler"],
                    }.items() if actual.get(field) != value],
                )
    elif spec["recipe"] == "textured_tint_pbr":
        expected_classes = sorted([
            "MaterialExpressionTextureSample",
            "MaterialExpressionTextureSample",
            "MaterialExpressionTextureSample",
            "MaterialExpressionVectorParameter",
            "MaterialExpressionMultiply",
            "MaterialExpressionMultiply",
            "MaterialExpressionConstant3Vector",
            "MaterialExpressionConstant",
            "MaterialExpressionDotProduct",
            "MaterialExpressionClamp",
            "MaterialExpressionLinearInterpolate",
        ])
        if expression_classes != expected_classes:
            fail("body masked-tint expression inventory drift: " + repr(expression_classes))
        if (inputs["base_color"]["class"] != "MaterialExpressionLinearInterpolate"
                or inputs["base_color"]["output"] != ""):
            fail("body BaseColor is not driven only by the exact masked-tint Lerp")
        for input_name, texture_semantic, output, sampler in (
                ("metallic", "metallic_roughness", spec["metallic_channel"],
                 "SAMPLERTYPE_MASKS"),
                ("roughness", "metallic_roughness", spec["roughness_channel"],
                 "SAMPLERTYPE_MASKS"),
                ("normal", "normal", "RGB", "SAMPLERTYPE_NORMAL")):
            assert_texture_record(
                inputs[input_name], spec["texture_object_paths"][texture_semantic],
                output, sampler, key + ":" + input_name)
        lerp = unreal.MaterialEditingLibrary.get_material_property_input_node(
            material, unreal.MaterialProperty.MP_BASE_COLOR)
        lerp_raw, lerp_links = expression_links(material, lerp)
        if list(lerp_raw) != ["A", "B", "Alpha"]:
            fail("body masked-tint Lerp input-name drift: " + repr(lerp_links))
        assert_texture_record(
            lerp_links["A"], spec["texture_object_paths"]["base_color"],
            "RGB", "SAMPLERTYPE_COLOR", key + ":lerp_A_unmodified_base")
        if lerp_links["B"].get("class") != "MaterialExpressionMultiply":
            fail("body masked-tint Lerp B is not the absolute-hue detail multiply")
        assert_texture_record(
            lerp_links["Alpha"],
            spec["texture_object_paths"][spec["paint_mask_texture_semantic"]],
            spec["paint_mask_channel"], "SAMPLERTYPE_MASKS", key + ":lerp_Alpha_mask")
        tint_multiply = lerp_raw["B"]
        tint_raw, tint_links = expression_links(material, tint_multiply)
        if list(tint_raw) != ["A", "B"]:
            fail("body absolute-hue multiply input-name drift: " + repr(tint_links))
        parameter = tint_raw["A"]
        parameter_record = tint_links["A"]
        expected_colour = [float(value) for value in spec["default_paint_colour_linear"]]
        actual_colour = [float(value) for value in parameter_record.get("default_value", [])[:3]]
        if (parameter_record.get("class") != "MaterialExpressionVectorParameter"
                or parameter_record.get("parameter_name") != "VehiclePaintColour"
                or parameter_record.get("output") != spec["parameter_output"]
                or len(actual_colour) != 3
                or max(abs(actual_colour[index] - expected_colour[index])
                       for index in range(3)) > 1e-5
                or parameter not in expressions):
            fail("body VehiclePaintColour parameter/default/topology drift")
        detail_clamp = tint_raw["B"]
        if tint_links["B"].get("class") != "MaterialExpressionClamp":
            fail("body absolute-hue multiplier lacks clamped luminance detail")
        clamp_raw, clamp_links = expression_links(material, detail_clamp)
        clamp_record = node_record(detail_clamp)
        # UE 5.8 reflects the shortened NAME_None pin as literal `None`;
        # expression_links canonicalizes that exact spelling to the logical
        # empty first-input selector used by the connection API.
        if (list(clamp_raw) != ["", "Min", "Max"]
                or clamp_raw["Min"] is not None
                or clamp_raw["Max"] is not None
                or abs(float(clamp_record.get("min_default", -1.0))
                       - float(spec["detail_clamp_min"])) > 1e-6
                or abs(float(clamp_record.get("max_default", -1.0))
                       - float(spec["detail_clamp_max"])) > 1e-6
                or clamp_record.get("clamp_mode") != "CMODE_CLAMP"):
            fail_expected_actual(
                "body luminance detail clamp/default/mode drift",
                {"input_names": ["", "Min", "Max"],
                 "min_default": float(spec["detail_clamp_min"]),
                 "max_default": float(spec["detail_clamp_max"]),
                 "clamp_mode": "CMODE_CLAMP"},
                {"input_names": list(clamp_raw), **clamp_record},
                ["input_names_or_defaults_or_clamp_mode"],
            )
        normalized_luminance = clamp_raw[""]
        if clamp_links[""].get("class") != "MaterialExpressionMultiply":
            fail("body detail clamp input is not normalized luminance")
        normalized_raw, normalized_links = expression_links(material, normalized_luminance)
        if list(normalized_raw) != ["A", "B"]:
            fail("body luminance normalization multiply input drift")
        luminance = normalized_raw["A"]
        normalization = normalized_raw["B"]
        normalization_record = normalized_links["B"]
        if (normalized_links["A"].get("class") != "MaterialExpressionDotProduct"
                or normalization_record.get("class") != "MaterialExpressionConstant"
                or abs(float(normalization_record.get("r", -1.0))
                       - float(spec["detail_normalization"])) > 1e-6):
            fail("body luminance normalization graph/value drift")
        luminance_raw, luminance_links = expression_links(material, luminance)
        if list(luminance_raw) != ["A", "B"]:
            fail("body luminance dot-product input drift")
        assert_texture_record(
            luminance_links["A"], spec["texture_object_paths"]["base_color"],
            "RGB", "SAMPLERTYPE_COLOR", key + ":luminance_A_base")
        weights = luminance_links["B"]
        actual_weights = [float(value) for value in weights.get("constant", [])[:3]]
        expected_weights = [float(value) for value in spec["detail_luminance_weights"]]
        if (weights.get("class") != "MaterialExpressionConstant3Vector"
                or len(actual_weights) != 3
                or max(abs(actual_weights[index] - expected_weights[index])
                       for index in range(3)) > 1e-6
                or lerp_raw["A"] is not luminance_raw["A"]):
            fail("body linear-luminance weights/shared base-sample topology drift")
        graph.update({
            "base_color_lerp": lerp_links,
            "absolute_hue_multiply": tint_links,
            "luminance_dot_product": luminance_links,
            "normalized_luminance": normalized_links,
            "detail_clamp": {"properties": clamp_record, "inputs": clamp_links},
            "parameter_name": "VehiclePaintColour",
            "paint_mask_texture_semantic": spec["paint_mask_texture_semantic"],
            "paint_mask_channel": spec["paint_mask_channel"],
            "paint_mask_target_input": spec["paint_mask_target_input"],
            "tint_graph_topology": spec["tint_graph_topology"],
            "absolute_hue_tonal_detail_reaches_base_color_only_through_masked_lerp": True,
        })
    else:
        expected_classes = sorted([
            "MaterialExpressionConstant3Vector",
            "MaterialExpressionConstant",
            "MaterialExpressionConstant",
        ])
        if expression_classes != expected_classes:
            fail("solid PBR expression inventory drift: " + key + repr(expression_classes))
        if (inputs["base_color"]["class"] != "MaterialExpressionConstant3Vector"
                or inputs["metallic"]["class"] != "MaterialExpressionConstant"
                or inputs["roughness"]["class"] != "MaterialExpressionConstant"
                or inputs["normal"]["class"] is not None):
            fail("solid PBR graph input class drift: " + key)
        expected_colour = [float(value) for value in spec["base_color_linear"]]
        actual_colour = [float(value) for value in inputs["base_color"].get("constant", [])[:3]]
        if (len(actual_colour) != 3
                or max(abs(actual_colour[i] - expected_colour[i]) for i in range(3)) > 1e-5
                or abs(float(inputs["metallic"].get("r", -1.0)) - float(spec["metallic"])) > 1e-5
                or abs(float(inputs["roughness"].get("r", -1.0)) - float(spec["roughness"])) > 1e-5):
            fail("solid PBR value drift: " + key)
    return {
        "material_key": key,
        "object_path": material.get_path_name(),
        "recipe": spec["recipe"],
        "material_state": material_state_actual,
        "texture_dependencies": sorted(actual_dependencies, key=str.casefold),
        "expected_texture_dependencies": sorted(expected_dependencies, key=str.casefold),
        "persisted_dependency_check_required": require_persisted_dependencies,
        "inputs": inputs,
        "unused_inputs_proven_unconnected": unused_inputs,
        "graph": graph,
    }


def validate_all_assets(baseline: dict,
                        require_persisted_dependencies: bool = False) -> dict:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if subsystem is None or not hasattr(subsystem, "import_lod"):
        fail("UE5.8 StaticMeshEditorSubsystem is unavailable")
    modules = {
        role: validate_mesh(
            role, spec, baseline, subsystem, require_persisted_dependencies)
        for role, spec in baseline["modules"].items()
    }
    textures = {
        semantic: validate_texture(semantic, spec, require_persisted_dependencies)
        for semantic, spec in baseline["textures"].items()
    }
    materials = {
        key: validate_material(key, spec, require_persisted_dependencies)
        for key, spec in baseline["materials"].items()
    }
    package_paths = set(baseline["destination"]["expected_package_paths"])
    closure = set()
    for role, spec in baseline["modules"].items():
        closure.add(spec["package_path"])
        closure.update(path.split(".", 1)[0] for path in spec["material_bindings"].values())
    for spec in baseline["materials"].values():
        closure.add(spec["package_path"])
        closure.update(path.split(".", 1)[0] for path in spec["texture_object_paths"].values())
    if closure != package_paths:
        fail("runtime mesh/material/texture dependency closure is not exact")
    body_material = baseline["materials"]["body"]["object_path"]
    rolling_material = baseline["materials"]["rolling_gear"]["object_path"]
    body_bindings = set(
        modules["EmeraldBodyVisualAuthority"]["bound_materials"].values())
    rolling_bindings = set(
        modules["EmeraldRollingGearVisualAuthority"]["bound_materials"].values())
    if (body_material == rolling_material
            or body_bindings != {body_material}
            or rolling_bindings != {rolling_material}
            or materials["body"]["recipe"] != "textured_tint_pbr"
            or materials["rolling_gear"]["recipe"] != "textured_pbr"):
        fail("body masked-paint and untinted rolling-gear material binding separation drift")
    return {
        "modules": modules,
        "textures": textures,
        "materials": materials,
        "exact_dependency_closure": sorted(closure, key=str.casefold),
        "body_rolling_material_binding_separation": {
            "body": body_material,
            "rolling_gear": rolling_material,
            "distinct": True,
            "body_player_tint_enabled": True,
            "rolling_gear_player_tint_enabled": False,
        },
        "persisted_asset_registry_dependency_closure_verified": (
            require_persisted_dependencies),
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
