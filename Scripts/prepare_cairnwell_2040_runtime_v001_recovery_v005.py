"""Freeze or verify the incident-bound Cairnwell runtime recovery v005 offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v004 as prior


PROJECT = prior.PROJECT
CONTRACT = prior.CONTRACT
CONTRACT_SHA = prior.CONTRACT_SHA
BASELINE = prior.BASELINE
BASELINE_SHA = prior.BASELINE_SHA
V004_CONTRACT = prior.OUTPUT
V004_CONTRACT_SHA = prior.OUTPUT_SHA
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v005_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v005_contract.sha256"
DEST = prior.DEST
AUDIT_ROOT = prior.AUDIT_ROOT
V004_RUN_ID = "20260815T112446Z-4e34bb5c"
V004_RUN = AUDIT_ROOT / "Recovery_v004" / V004_RUN_ID
V004_IMPORT_FAILURE_SHA256 = (
    "D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF"
)
V004_CONTRACT_SHA256 = (
    "C52DE8F74018D03458A94946A0B1208322881F4C52E765B474B3DE56CF8052DA"
)
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v005"
V004_QUARANTINE = (
    PROJECT / "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T112446Z-4e34bb5c_v004"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_ONCE"
RUN_ACK_TOKEN = "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V005_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V005__"
    "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"
)
V004_FILES = {
    "import_failure_recovery_v004.json": (
        7378, "D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF"),
    "lane_summary_recovery_v004.json": (
        3525, "C05669FFD06EA3570B8192E4A4ADE4F1596B4AAED402E5202E481E527E349961"),
    "quarantine_receipt_v004.json": (
        7938, "D5E09C0EEE23CF6FBCC914A00DD44F5CE3EA9EF33C9461E9E6B38EE98C1CF144"),
    "unreal_import_recovery_v004.log": (
        380700, "9EC1257D9C2CB441040820F18D27C374D91F25101B090E353823D1C86C303F49"),
    "unreal_import_recovery_v004.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "unreal_import_recovery_v004.stdout.log": (
        380711, "9EBE0189E19B51FE6D240F3FC9F037B2976345D374CD909D27C0A132F38008DF"),
}
V004_PARTIALS = {
    "Materials/M_LB_C2040_BIWGalvanized_v001.uasset": (
        6002, 1786793199484938000,
        "7CB2E1A6290373CB105EDC2A64EA8F9984CD8DF9E39A3E09D6B4B53DB8F977B0"),
    "Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset": (
        11566, 1786793199546939800,
        "B6A69E70FA534BEC747AC5CB70DA63E997AB1B3B6FC6B3CA0A0973BE736314F4"),
    "Materials/M_LB_C2040_EDCoat_v001.uasset": (
        5960, 1786793199603937900,
        "53DA47DECFFB17A7B1403AF548B0562EBF94F7CAEEDFE229AA2DF87D4E334446"),
    "Materials/M_LB_C2040_RollingGearPBR_v001.uasset": (
        7119, 1786793199662938000,
        "98A863E52C804BC04F9E4DD4180A3B6A3852AD01A74DF28712BD9E5BE57F0C82"),
    "Meshes/SM_LB_C2040_BIW_AutomotiveSkeleton_v001.uasset": (
        2293043, 1786793205386473800,
        "7D35D47B0ECDE59EAB51FBDB475EF20F4F4BB481BBA453927724B9B521445DD0"),
    "Meshes/SM_LB_C2040_BIW_UnderbodySubset_v001.uasset": (
        1329365, 1786793205406473900,
        "DEF91E57144420980F5C07089B2A2625ABD31BEE40C7ED8B64DDE04E4FCFF858"),
    "Meshes/SM_LB_C2040_EmeraldBodyVisualAuthority_v001.uasset": (
        7355548, 1786793205447491200,
        "4CAAA5B6465D4D967F3BE2FAE5406271D9D5F225270BB64FAEFCD6F04E9EA386"),
    "Meshes/SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001.uasset": (
        3756424, 1786793205528540500,
        "20D2E8EE7D7B197C5E88A4E1CCA0A308511673A602053C15AFA185BC20AD811F"),
    "Textures/T_LB_C2040_Emerald_BaseColor_v001.uasset": (
        3818680, 1786793199233939900,
        "DD48E3BD3A2EE49E2D6F2C351857A884C2834636134E533BDB5F95BCC8C27586"),
    "Textures/T_LB_C2040_Emerald_MRBodyMask_v001.uasset": (
        5818244, 1786793199283940800,
        "A98F8229F7BB6583F3857AAF976CA82F0519E8BBAD6C360A225B522B2DFAF450"),
    "Textures/T_LB_C2040_Emerald_Normal_v001.uasset": (
        3973188, 1786793199323948900,
        "94CC4413F9EEC414F32D42108D3381DC6BCD63658D7F969DD208483A12DCFC72"),
}
V005_LANE_CHANGED = {
    "Scripts/cairnwell_2040_runtime_v001.py",
    "Scripts/import_cairnwell_2040_runtime_v001.py",
    "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
    "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
}
V005_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v005.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v004_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v004_contract.sha256",
}
FBX_CONVERTER_SOURCE = Path(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Editor\UnrealEd\Private\Fbx\FbxUtilsImport.cpp"
)
FBX_CONVERTER_SOURCE_SHA256 = (
    "E96AF266A819FD61B94F637253C409B98312B13B24E32B1E873CB4AB45481FB2"
)
BOUNDS_SERIALIZER_SOURCE = Path(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\Core\Public\Math\BoxSphereBounds.h"
)
BOUNDS_SERIALIZER_SOURCE_SHA256 = (
    "690FB6D64A5375CAF53635FC1EFE210FED8C9D2679C5A2F864D08F742085198B"
)
OBSERVED_UNDERBODY_ORIGIN = (
    0.0123748779296875, 0.48571014404296875, 41.680776596069336)
OBSERVED_UNDERBODY_EXTENT = (
    226.0, 79.58294677734375, 33.06645393371582)
OBSERVED_ORIGIN_OFFSET = 15767
OBSERVED_EXTENT_OFFSET = 15840


class RecoveryError(RuntimeError):
    pass


def object_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest().upper()


def exact_prior_contract() -> dict:
    prior.prior.exact_sidecar(
        V004_CONTRACT, V004_CONTRACT_SHA, V004_CONTRACT_SHA256, "v004 contract")
    payload = json.loads(V004_CONTRACT.read_text(encoding="utf-8"))
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v4"
            or payload.get("status") != prior.STATUS
            or payload.get("incident_chain", {}).get("v003", {}).get(
                "import_failure", {}).get("sha256") != prior.V003_IMPORT_FAILURE_SHA256):
        raise RecoveryError("frozen v004 recovery authority drift")
    return payload


def v004_run_rows() -> dict[str, dict]:
    if not V004_RUN.is_dir():
        raise RecoveryError("exact v004 failed-run root is absent")
    actual_names = {path.name for path in V004_RUN.iterdir() if path.is_file()}
    if actual_names != set(V004_FILES):
        raise RecoveryError("v004 failed-run file closure drift: " + repr(sorted(actual_names)))
    rows = {}
    for name, (size, digest) in V004_FILES.items():
        row = prior.prior.file_row(V004_RUN / name)
        if row["bytes"] != size or row["sha256"] != digest:
            raise RecoveryError("v004 failed-run hash drift: " + name)
        rows[name] = row
    failure = json.loads((V004_RUN / "import_failure_recovery_v004.json").read_text())
    summary = json.loads((V004_RUN / "lane_summary_recovery_v004.json").read_text())
    quarantine = json.loads((V004_RUN / "quarantine_receipt_v004.json").read_text())
    process = summary.get("import_process", {})
    expected_error = (
        "CAIRNWELL_2040_RUNTIME_V001_UNREAL_LANE_FAIL: "
        "BIW_UnderbodySubset:LOD0 bounds/shared-pivot drift: minimum_cm"
    )
    if (failure.get("$schema")
            != "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v004/unreal-import/v4"
            or failure.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_UNREAL_IMPORT"
            or failure.get("error") != expected_error
            or summary.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_UNREAL_IMPORT_LANE"
            or summary.get("error")
            != "Recovery importer emitted a failure receipt despite strict process exit gate"
            or int(process.get("exit_code", -1)) != 0
            or int(process.get("redirected_log_read_open_retry", {}).get(
                "stdout_attempts", -1)) != 22
            or process.get("fatal_log_patterns") != []
            or quarantine.get("status")
            != "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004_PARTIALS_QUARANTINED"):
        raise RecoveryError("v004 primary/wrapper/quarantine incident identity drift")
    return rows


def partial_rows(root: Path, label: str) -> dict[str, dict]:
    if not root.is_dir():
        raise RecoveryError(label + " root absent")
    actual = {path.relative_to(root).as_posix(): path
              for path in root.rglob("*") if path.is_file()}
    if set(actual) != set(V004_PARTIALS):
        raise RecoveryError(label + " eleven-package closure drift")
    rows = {}
    for rel, (size, mtime, digest) in V004_PARTIALS.items():
        row = prior.prior.file_row(actual[rel])
        if (row["bytes"] != size or row["mtime_ns"] != mtime
                or row["sha256"] != digest):
            raise RecoveryError(label + " package hash/mtime drift: " + rel)
        rows[rel] = row
    return rows


def partial_contract_rows() -> dict[str, dict]:
    current = partial_rows(DEST, "v004 fresh destination")
    failure = json.loads((V004_RUN / "import_failure_recovery_v004.json").read_text())
    preserved = failure.get("namespace_files_preserved_for_recovery", {})
    output = {}
    for rel, row in current.items():
        source_path = prior.prior.relative(DEST / rel)
        if preserved.get(source_path) != {
                key: row[key] for key in ("bytes", "mtime_ns", "sha256")}:
            raise RecoveryError("v004 failure receipt does not pin package: " + source_path)
        output[source_path] = {
            "source_path": source_path,
            "quarantine_path": prior.prior.relative(V004_QUARANTINE / rel),
            "bytes": row["bytes"], "mtime_ns": row["mtime_ns"],
            "sha256": row["sha256"],
        }
    return output


def convert_source_bounds_to_unreal(source: dict) -> dict:
    minimum = [float(value) for value in source["minimum_cm"]]
    maximum = [float(value) for value in source["maximum_cm"]]
    pivot = [float(value) for value in source["pivot_cm"]]
    if (len(minimum) != 3 or len(maximum) != 3 or len(pivot) != 3
            or not all(math.isfinite(value) for value in minimum + maximum + pivot)):
        raise RecoveryError("non-finite or malformed source bounds")
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


def unpack_unique(data: bytes, values: tuple[float, float, float], label: str) -> int:
    pattern = struct.pack("<3d", *values)
    offsets = []
    start = 0
    while True:
        offset = data.find(pattern, start)
        if offset < 0:
            break
        offsets.append(offset)
        start = offset + 1
    if len(offsets) != 1:
        raise RecoveryError(label + " serialized proof is not unique: " + repr(offsets))
    return offsets[0]


def observed_underbody_bounds(path: Path, expected_sha256: str) -> dict:
    if prior.prior.sha256(path) != expected_sha256:
        raise RecoveryError("observed Underbody package hash drift: " + str(path))
    data = path.read_bytes()
    origin_offset = unpack_unique(data, OBSERVED_UNDERBODY_ORIGIN, "Underbody origin")
    extent_offset = unpack_unique(data, OBSERVED_UNDERBODY_EXTENT, "Underbody extent")
    if origin_offset != OBSERVED_ORIGIN_OFFSET or extent_offset != OBSERVED_EXTENT_OFFSET:
        raise RecoveryError("Underbody serialized bounds offsets drift")
    minimum = [OBSERVED_UNDERBODY_ORIGIN[index] - OBSERVED_UNDERBODY_EXTENT[index]
               for index in range(3)]
    maximum = [OBSERVED_UNDERBODY_ORIGIN[index] + OBSERVED_UNDERBODY_EXTENT[index]
               for index in range(3)]
    return {
        "package": prior.prior.file_row(path),
        "serialization": "FBoxSphereBounds3d Origin then BoxExtent property values",
        "origin_byte_offset": origin_offset,
        "box_extent_byte_offset": extent_offset,
        "origin_cm": list(OBSERVED_UNDERBODY_ORIGIN),
        "box_extent_cm": list(OBSERVED_UNDERBODY_EXTENT),
        "minimum_cm": minimum,
        "maximum_cm": maximum,
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def runtime_bounds_conversion(contract: dict) -> dict:
    if prior.prior.sha256(FBX_CONVERTER_SOURCE) != FBX_CONVERTER_SOURCE_SHA256:
        raise RecoveryError("installed UE5.8 FBX position converter source drift")
    if prior.prior.sha256(BOUNDS_SERIALIZER_SOURCE) != BOUNDS_SERIALIZER_SOURCE_SHA256:
        raise RecoveryError("installed UE5.8 bounds serializer source drift")
    roles = {}
    for role, spec in sorted(contract["modules"].items()):
        lods = []
        for lod in spec["lods"]:
            source = lod["expected_unreal_bounds"]
            converted = convert_source_bounds_to_unreal(source)
            if converted["dimensions_cm"] != source["dimensions_cm"]:
                raise RecoveryError("Y flip changed dimensions unexpectedly: " + role)
            if converted["pivot_cm"] != [0.0, 0.0, 0.0]:
                raise RecoveryError("shared zero datum changed during Y flip: " + role)
            lods.append({
                "lod": int(lod["lod"]),
                "frozen_source_bounds_cm": source,
                "expected_unreal_bounds_cm": converted,
            })
        roles[role] = {"lods": lods}
    underbody_relative = Path("Meshes/SM_LB_C2040_BIW_UnderbodySubset_v001.uasset")
    current_source = V004_QUARANTINE / underbody_relative
    if not current_source.is_file():
        current_source = DEST / underbody_relative
    current = observed_underbody_bounds(
        current_source,
        V004_PARTIALS["Meshes/SM_LB_C2040_BIW_UnderbodySubset_v001.uasset"][2],
    )
    # The frozen forensic row names the package at the instant of the v004
    # failure.  After the one permitted whole-directory move, verify the same
    # bytes from quarantine while retaining that chronological source path.
    current["package"]["path"] = prior.prior.relative(DEST / underbody_relative)
    v003 = observed_underbody_bounds(
        prior.V003_QUARANTINE / "Meshes/SM_LB_C2040_BIW_UnderbodySubset_v001.uasset",
        prior.V003_PARTIALS["Meshes/SM_LB_C2040_BIW_UnderbodySubset_v001.uasset"][2],
    )
    expected = roles["BIW_UnderbodySubset"]["lods"][0]["expected_unreal_bounds_cm"]
    if max(abs(current[field][index] - expected[field][index])
           for field in ("minimum_cm", "maximum_cm") for index in range(3)) > 0.00003:
        raise RecoveryError("converted Underbody bounds do not match preserved UE package")
    if any(current[key] != v003[key]
           for key in ("origin_cm", "box_extent_cm", "minimum_cm", "maximum_cm")):
        raise RecoveryError("v003/v004 deterministic Underbody bounds proof drift")
    source = roles["BIW_UnderbodySubset"]["lods"][0]["frozen_source_bounds_cm"]
    return {
        "coordinate_rule": "Unreal = (source X, -source Y, source Z)",
        "bounds_rule": "min=(minX,-maxY,minZ); max=(maxX,-minY,maxZ)",
        "comparison_tolerance_cm": 0.25,
        "tolerance_relaxed": False,
        "source_or_fbx_modified": False,
        "engine_sources": {
            "fbx_position_converter": {
                "path": str(FBX_CONVERTER_SOURCE).replace("\\", "/"),
                "sha256": FBX_CONVERTER_SOURCE_SHA256,
                "lines": "63-71",
                "proof": "FFbxDataConverter::ConvertPos maps X,-Y,Z",
            },
            "bounds_serializer": {
                "path": str(BOUNDS_SERIALIZER_SOURCE).replace("\\", "/"),
                "sha256": BOUNDS_SERIALIZER_SOURCE_SHA256,
                "lines": "406-410",
                "proof": "FBoxSphereBounds3d serializes Origin then BoxExtent",
            },
        },
        "roles": roles,
        "v004_underbody_lod0_failure_forensics": {
            "frozen_expected_source_space": source,
            "expected_after_ue_y_flip": expected,
            "v003_preserved_package": v003,
            "v004_preserved_package": current,
            "maximum_expected_vs_observed_delta_cm": max(
                abs(current[field][index] - expected[field][index])
                for field in ("minimum_cm", "maximum_cm") for index in range(3)),
            "source_space_y_endpoint_mismatch_cm": max(
                abs(current[field][1] - source[field][1])
                for field in ("minimum_cm", "maximum_cm")),
            "classification": (
                "DETERMINISTIC_UE5_8_FBX_HANDEDNESS_CONVERSION__"
                "FROZEN_CONTRACT_WAS_SOURCE_SPACE__NO_TRANSFORM_OR_GEOMETRY_DRIFT"),
        },
    }


def verify_v004_lane_drift(v004: dict) -> None:
    changed = set()
    for expected in v004["lane"]["files"]:
        if prior.prior.file_row(PROJECT / expected["path"]) != expected:
            changed.add(expected["path"])
    if changed != V005_LANE_CHANGED:
        raise RecoveryError("v004 prepared-lane drift is not exact v005 patch: " + repr(changed))


def v005_lane_snapshot(v004: dict) -> dict:
    paths = {row["path"] for row in v004["lane"]["files"]} | V005_ADDITIONS
    snapshot = prior.prior.inventory([PROJECT / rel for rel in paths])
    if {row["path"] for row in snapshot["files"]} != paths:
        raise RecoveryError("v005 prepared-lane path closure drift")
    return snapshot


def result_topology() -> dict:
    prefix = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v005/"
    return {
        "audit_root": prior.prior.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": prior.prior.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "quarantine_receipt": {"filename": "quarantine_receipt_v005.json",
            "$schema": prefix + "quarantine/v5",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_PARTIALS_QUARANTINED"},
        "import": {"receipt_filename": "import_receipt_recovery_v005.json",
            "failure_filename": "import_failure_recovery_v005.json",
            "$schema": prefix + "unreal-import/v5",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_FRESH_IMPORT__4_MESHES__12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE",
            "package_hash_field": "package_sha256"},
        "fresh_validation": {
            "receipt_filename": "fresh_process_validation_receipt_recovery_v005.json",
            "failure_filename": "fresh_process_validation_failure_recovery_v005.json",
            "$schema": prefix + "fresh-process-validation/v5",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED",
            "package_hash_fields": ["package_sha256_before_loads", "package_sha256_after_loads"]},
        "summary": {"filename": "lane_summary_recovery_v005.json",
            "$schema": prefix + "import-lane-summary/v5",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_GUARDED_IMPORT_AND_DISTINCT_READ_ONLY_RELOAD",
            "package_hash_field": "post_exit_package_sha256"},
        "required_incident_binding_fields": ["recovery_contract_sha256",
            "v001_failed_run_id", "v001_import_failure_sha256", "v002_failed_run_id",
            "v002_import_failure_sha256", "v003_failed_run_id",
            "v003_import_failure_sha256", "v004_failed_run_id",
            "v004_import_failure_sha256", "incident_chain_sha256", "quarantine_receipt"],
    }


def prior_state() -> tuple[dict, dict, dict, str, str]:
    contract, baseline, contract_digest, baseline_digest = prior.prior.load_original()
    v004 = exact_prior_contract()
    v004_run_rows()
    prior.prior.verify_snapshot(v004["prior_quarantines"]["v001_partial_packages"],
                                "v001 package quarantine")
    prior.prior.verify_snapshot(v004["prior_quarantines"]["v002_partial_packages"],
                                "v002 package quarantine")
    q3_paths = [PROJECT / row["quarantine_path"]
                for row in v004["partial_packages"].values()]
    q3 = prior.prior.inventory(q3_paths)
    if q3["file_count"] != 11 or not all(
            prior.prior.inside(path, prior.V003_QUARANTINE) for path in q3_paths):
        raise RecoveryError("v003 eleven-package quarantine closure drift")
    for expected in v004["partial_packages"].values():
        actual = prior.prior.file_row(PROJECT / expected["quarantine_path"])
        if any(actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256")):
            raise RecoveryError("v003 quarantined package drift: " + expected["quarantine_path"])
    verify_v004_lane_drift(v004)
    return contract, baseline, v004, contract_digest, baseline_digest


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v005 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v005 recovery contract or sidecar")
    if RECOVERY_AUDIT_ROOT.exists() or V004_QUARANTINE.exists():
        raise RecoveryError("v005 result/quarantine already exists")
    contract, baseline, v004, _, _ = prior_state()
    run_rows = v004_run_rows()
    partials = partial_contract_rows()
    chain = {
        "v001": v004["incident_chain"]["v001"],
        "v002": v004["incident_chain"]["v002"],
        "v003": v004["incident_chain"]["v003"],
        "v004": {
            "failed_run_id": V004_RUN_ID,
            "run_root": prior.prior.relative(V004_RUN),
            "recovery_contract": prior.prior.file_row(V004_CONTRACT),
            "recovery_contract_sidecar": prior.prior.file_row(V004_CONTRACT_SHA),
            "import_failure": run_rows["import_failure_recovery_v004.json"],
            "lane_summary": run_rows["lane_summary_recovery_v004.json"],
            "quarantine_receipt": run_rows["quarantine_receipt_v004.json"],
            "files": run_rows,
            "primary_failure": "frozen source-space Y bounds compared against UE left-handed import",
            "wrapper_result": "strict process/log gate passed then failure receipt stopped lane",
        },
        "old_success_receipts_present": False,
    }
    chain["binding_sha256"] = object_hash(chain)
    q3_paths = [PROJECT / row["quarantine_path"]
                for row in v004["partial_packages"].values()]
    payload = {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v5",
        "status": STATUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": {"contract": prior.prior.file_row(CONTRACT),
            "contract_sidecar": prior.prior.file_row(CONTRACT_SHA),
            "baseline": prior.prior.file_row(BASELINE),
            "baseline_sidecar": prior.prior.file_row(BASELINE_SHA)},
        "approved_source": {key: baseline["source"][key]
                            for key in ("file_count", "inventory_sha256")},
        "protected_project": {key: baseline["protected"][key]
                              for key in ("file_count", "inventory_sha256")},
        "incident_chain": chain,
        "prior_quarantines": {
            "v001_partial_packages": v004["prior_quarantines"]["v001_partial_packages"],
            "v002_partial_packages": v004["prior_quarantines"]["v002_partial_packages"],
            "v003_partial_packages": prior.prior.inventory(q3_paths),
        },
        "partial_packages": partials,
        "slot_normalization": v004["slot_normalization"],
        "runtime_uv_sanitization": v004["runtime_uv_sanitization"],
        "runtime_bounds_coordinate_conversion": runtime_bounds_conversion(contract),
        "quarantine": {"source_root": prior.prior.relative(DEST),
            "destination_root": prior.prior.relative(V004_QUARANTINE),
            "operation": "MOVE_DIRECTORY_ONLY__NO_DELETE",
            "automatic_delete_authorized": False,
            "rerun_after_any_recovery_result_authorized": False},
        "lane": v005_lane_snapshot(v004),
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
            "runtime_bounds_tolerance_must_remain_0_25_cm": True},
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = prior.prior.sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    contract, baseline, v004, contract_digest, baseline_digest = prior_state()
    digest = prior.prior.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise RecoveryError("v005 recovery sidecar drift")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    chain = payload.get("incident_chain", {})
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v5"
            or payload.get("status") != STATUS or payload.get("acknowledgement") != RUN_ACK_TOKEN
            or payload.get("original_authorities", {}).get("contract", {}).get("sha256")
            != contract_digest
            or payload.get("original_authorities", {}).get("baseline", {}).get("sha256")
            != baseline_digest
            or chain.get("v001", {}).get("import_failure", {}).get("sha256")
            != prior.prior.V001_IMPORT_FAILURE_SHA256
            or chain.get("v002", {}).get("import_failure", {}).get("sha256")
            != prior.prior.V002_IMPORT_FAILURE_SHA256
            or chain.get("v003", {}).get("import_failure", {}).get("sha256")
            != prior.V003_IMPORT_FAILURE_SHA256
            or chain.get("v004", {}).get("import_failure", {}).get("sha256")
            != V004_IMPORT_FAILURE_SHA256):
        raise RecoveryError("v005 recovery contract identity drift")
    for key in ("v001_partial_packages", "v002_partial_packages", "v003_partial_packages"):
        prior.prior.verify_snapshot(payload["prior_quarantines"][key], key)
    prior.prior.verify_snapshot(payload["lane"], "v005 prepared lane")
    if payload["slot_normalization"] != v004["slot_normalization"]:
        raise RecoveryError("v005 slot-normalization authority drift")
    if payload["runtime_uv_sanitization"] != v004["runtime_uv_sanitization"]:
        raise RecoveryError("v005 runtime UV sanitation authority drift")
    if payload["runtime_bounds_coordinate_conversion"] != runtime_bounds_conversion(contract):
        raise RecoveryError("v005 runtime bounds conversion authority drift")
    return payload, baseline


def verify_partial_contract(payload: dict, root: Path, label: str) -> None:
    rows = partial_rows(root, label)
    for rel, actual in rows.items():
        source = prior.prior.relative(DEST / rel)
        expected = payload["partial_packages"][source]
        expected_path = source if root == DEST else expected["quarantine_path"]
        if (actual["path"] != expected_path or any(
                actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256"))):
            raise RecoveryError(label + " does not match contract: " + rel)


def verify_pre_quarantine() -> None:
    payload, _ = load_frozen()
    if V004_QUARANTINE.exists() or RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v005 quarantine/result already exists")
    verify_partial_contract(payload, DEST, "v004 fresh destination")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_PRE_QUARANTINE_REVERIFIED")
    print(prior.prior.sha256(OUTPUT))


def verify_post_quarantine() -> None:
    payload, _ = load_frozen()
    if DEST.exists():
        raise RecoveryError("fresh destination remains after v005 quarantine move")
    verify_partial_contract(payload, V004_QUARANTINE, "v004 package quarantine")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_POST_QUARANTINE_REVERIFIED")
    print(prior.prior.sha256(OUTPUT))


def verify_post_import() -> None:
    payload, baseline = load_frozen()
    verify_partial_contract(payload, V004_QUARANTINE, "v004 package quarantine")
    expected = set(baseline["destination"]["expected_package_paths"])
    actual = {"/Game/" + path.relative_to(PROJECT / "Content").with_suffix("").as_posix()
              for path in DEST.rglob("*.uasset")} if DEST.is_dir() else set()
    if actual != expected or len(actual) != 11:
        raise RecoveryError("post-import destination is not exact eleven-package closure")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_POST_IMPORT_REVERIFIED")
    print(prior.prior.sha256(OUTPUT))


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
