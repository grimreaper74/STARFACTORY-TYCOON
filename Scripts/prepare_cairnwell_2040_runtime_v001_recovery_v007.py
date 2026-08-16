"""Freeze or verify incident-bound Cairnwell runtime recovery v007 offline."""

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
import prepare_cairnwell_2040_runtime_v001_recovery_v006 as prior


BASE = prior.prior.prior.prior
PROJECT = prior.PROJECT
CONTRACT = prior.CONTRACT
CONTRACT_SHA = prior.CONTRACT_SHA
BASELINE = prior.BASELINE
BASELINE_SHA = prior.BASELINE_SHA
V006_CONTRACT = prior.OUTPUT
V006_CONTRACT_SHA = prior.OUTPUT_SHA
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v007_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v007_contract.sha256"
DEST = prior.DEST
AUDIT_ROOT = prior.AUDIT_ROOT
V006_RUN_ID = "20260815T124823Z-67c989ee"
V006_RUN = AUDIT_ROOT / "Recovery_v006" / V006_RUN_ID
V006_IMPORT_FAILURE_SHA256 = (
    "A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06"
)
V006_CONTRACT_SHA256 = (
    "7DDEF098FF1C2D0E53756E89CC57B1A00A89C32A4A7E623686454D619F3214AD"
)
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v007"
V005_QUARANTINE = prior.V005_QUARANTINE
V006_QUARANTINE = (
    PROJECT / "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T124823Z-67c989ee_v006"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_ONCE"
RUN_ACK_TOKEN = "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V007_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V007__"
    "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"
)
V006_FILES = {
    "import_failure_recovery_v006.json": (
        8473, "A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06"),
    "lane_summary_recovery_v006.json": (
        4605, "A301E0F229D172C66351017D5281778A3916232D12F4455C328F45F6C5FE1502"),
    "quarantine_receipt_v006.json": (
        20008, "ADA88E957267A48B548E1524B3EED9890AB99DD1839D5A35952F05B55078511A"),
    "unreal_import_recovery_v006.log": (
        385619, "78E4377EEDF8F963BE0ED6C400F8CBA167569A39C5F8A8D4314D60BDE9956B17"),
    "unreal_import_recovery_v006.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "unreal_import_recovery_v006.stdout.log": (
        385634, "E7AE363F34997A551ECACEDAC33B2D4BAF9B5650E5B10BDFA9028A815E56502C"),
}
V006_PARTIAL_HASHES = {
    "Materials/M_LB_C2040_BIWGalvanized_v001.uasset": (
        6002, "8EC43533B301D2E9F6CB118882E7AD4BE456E22125BBD3FDABCF1432DA269F69"),
    "Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset": (
        11566, "35A9439C1C978A0D2F4A69D0FABCC1BD69AA5A01DD849709CB6147B36E17BB66"),
    "Materials/M_LB_C2040_EDCoat_v001.uasset": (
        5960, "FB28DBAD698214DA050789FB3EF3127907477F2660B49B4CB7CCFE908E65C48B"),
    "Materials/M_LB_C2040_RollingGearPBR_v001.uasset": (
        7119, "8FCC9B40772B821D460191B57383797B45D291C9C5B064C3EE993D96962AEA89"),
    "Meshes/SM_LB_C2040_BIW_AutomotiveSkeleton_v001.uasset": (
        2293043, "77FF117DC3BA40225F69EA516B55038345502A9A59D73BE5ACA8203B945EDFCD"),
    "Meshes/SM_LB_C2040_BIW_UnderbodySubset_v001.uasset": (
        1329365, "5F59EAB9CEC34B3EBAA5D15D771BA2FA3A266C41FA36EFB8A45C4D2EFAF0B198"),
    "Meshes/SM_LB_C2040_EmeraldBodyVisualAuthority_v001.uasset": (
        7355548, "DFE3889C8AF4B381D1BF24A510C7078969DCC468A8662F7D816A4489C66CA904"),
    "Meshes/SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001.uasset": (
        3756424, "39D9D8DA550A1E6A460974F42DAE7435F22125CC5152E27FADEAE9447AD520FC"),
    "Textures/T_LB_C2040_Emerald_BaseColor_v001.uasset": (
        3818680, "61705EDE0091E2B582C0C303671A55E5E8E4E52D52F5DAAD884E93007A6D83DE"),
    "Textures/T_LB_C2040_Emerald_MRBodyMask_v001.uasset": (
        5818244, "EC370758B430EE1E20049279D8BE7EB82E6D96691E2827CE6C272F42942E40AA"),
    "Textures/T_LB_C2040_Emerald_Normal_v001.uasset": (
        3973188, "FFA03A94898EDC9EBBE180053A94B18D512009A30E88A1F8183C70EC582F28CA"),
}
V007_LANE_CHANGED = {
    "Scripts/cairnwell_2040_runtime_v001.py",
    "Scripts/import_cairnwell_2040_runtime_v001.py",
    "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
    "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
}
V007_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v007.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v006_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v006_contract.sha256",
}
ENGINE_SOURCES = {
    "material_editing_library": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Editor\MaterialEditor\Private\MaterialEditingLibrary.cpp"),
        "bytes": 71759,
        "sha256": "96051980458DAD86719F195072DA4BD34EEBD07A80D647EBB50BBBB0626E5565",
        "connection_lookup_lines": "46-75",
        "reflection_lines": "1203-1225",
    },
    "material_graph_node": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Editor\UnrealEd\Private\MaterialGraphNode.cpp"),
        "bytes": 37860,
        "sha256": "026D9A5C896AF1E590E4BD8E42F1EC4788C8210198007D79C5051F8792716DD9",
        "shortening_lines": "597-613",
    },
    "python_string_conversion": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Source\PythonScriptPlugin\Private\PyConversion.cpp"),
        "bytes": 47655,
        "sha256": "20B3FB6654B4422E7F7327EBC79BA29AC1F4E5366A12A962992E94E516070901",
        "fstring_to_python_lines": "328-331",
        "array_wrapper_lines": "1191-1195",
    },
    "unreal_names": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\Core\Private\UObject\UnrealNames.cpp"),
        "bytes": 186237,
        "sha256": "1A4F7F23564AFEBC8C18D080A4757B16958C15FCAB513C9E3A1F0A67E565F67C",
        "to_string_lines": "3596-3609",
        "none_spelling_lines": "4206;4214-4224",
    },
    "expression_input_iterator": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\Engine\Public\Materials\MaterialExpression.h"),
        "bytes": 27931,
        "sha256": "164DEA3A175E742D2622C8CCA81B6808B07FF7D70F4119D23B389DBFF498D977",
        "iterator_lines": "667-718",
    },
    "clamp_header": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\Engine\Public\Materials\MaterialExpressionClamp.h"),
        "bytes": 1644,
        "sha256": "B99BD633B8AAB91211162B3EEBF5021BB8C182CEC8FCD9AC051371F8CECB6DEA",
        "input_order_lines": "27-34",
    },
    "lerp_header": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\Engine\Public\Materials\MaterialExpressionLinearInterpolate.h"),
        "bytes": 1746,
        "sha256": "0BD39BC602A1F3889793636425A88249C4BA8F3463D91F4BDC64687FAC68A591",
        "input_order_lines": "18-25",
    },
    "multiply_header": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\Engine\Public\Materials\MaterialExpressionMultiply.h"),
        "bytes": 1392,
        "sha256": "B6650CFBBBBD753031277695F633D4271DD5CEEA4C948C73950E3A41168A7CB5",
        "input_order_lines": "19-23",
    },
    "dot_header": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\Engine\Public\Materials\MaterialExpressionDotProduct.h"),
        "bytes": 840,
        "sha256": "3179C578A54C54FAA7F6A9D283C321574DAC50DD2C071405AF5F3363EAAA063E",
        "input_order_lines": "19-23",
    },
    "material_expressions": {
        "path": Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\Engine\Private\Materials\MaterialExpressions.cpp"),
        "bytes": 778212,
        "sha256": "66909943C30BDCEA8F8BC47BD3B719093EEED4D11715B94CB120FB4F4330D815",
        "clamp_input_derivation_lines": "1821-1849",
    },
}


class RecoveryError(RuntimeError):
    pass


def object_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def external_source_rows() -> dict[str, dict]:
    rows = {}
    for name, expected in ENGINE_SOURCES.items():
        path = expected["path"]
        if (not path.is_file() or path.stat().st_size != expected["bytes"]
                or BASE.sha256(path) != expected["sha256"]):
            raise RecoveryError("installed UE5.8 material-input source drift: " + name)
        row = {key: value for key, value in expected.items() if key != "path"}
        row["path"] = str(path).replace("\\", "/")
        rows[name] = row
    return rows


def exact_prior_contract() -> dict:
    BASE.exact_sidecar(
        V006_CONTRACT, V006_CONTRACT_SHA, V006_CONTRACT_SHA256, "v006 contract")
    payload = json.loads(V006_CONTRACT.read_text(encoding="utf-8"))
    chain = dict(payload.get("incident_chain", {}))
    declared = chain.pop("binding_sha256", None)
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v6"
            or payload.get("status") != prior.STATUS
            or declared != object_hash(chain)
            or payload.get("incident_chain", {}).get("v005", {}).get(
                "import_failure", {}).get("sha256") != prior.V005_IMPORT_FAILURE_SHA256):
        raise RecoveryError("frozen v006 recovery authority drift")
    for version in ("v001", "v002", "v003", "v004", "v005"):
        for label, row in payload["incident_chain"][version]["files"].items():
            if BASE.file_row(PROJECT / row["path"]) != row:
                raise RecoveryError(f"preserved {version} incident drift: {label}")
    for version in ("v002", "v003", "v004", "v005"):
        incident = payload["incident_chain"][version]
        for label in ("recovery_contract", "recovery_contract_sidecar"):
            row = incident[label]
            if BASE.file_row(PROJECT / row["path"]) != row:
                raise RecoveryError(f"preserved {version} {label} drift")
    for label, row in payload["original_authorities"].items():
        if BASE.file_row(PROJECT / row["path"]) != row:
            raise RecoveryError("preserved original authority drift: " + label)
    for row in payload["exact_ue_enum_validation"]["read_only_diagnostic"]["files"].values():
        if BASE.file_row(PROJECT / row["path"]) != row:
            raise RecoveryError("v005 texture-forensic evidence drift")
    receipt = payload["exact_ue_enum_validation"]["read_only_diagnostic"]["receipt"]
    if BASE.file_row(PROJECT / receipt["path"]) != receipt:
        raise RecoveryError("v005 texture-forensic receipt drift")
    return payload


def v006_run_rows() -> dict[str, dict]:
    if not V006_RUN.is_dir():
        raise RecoveryError("exact v006 failed-run root is absent")
    actual_names = {path.name for path in V006_RUN.iterdir() if path.is_file()}
    if actual_names != set(V006_FILES):
        raise RecoveryError("v006 failed-run file closure drift: " + repr(sorted(actual_names)))
    rows = {}
    for name, (size, digest) in V006_FILES.items():
        row = BASE.file_row(V006_RUN / name)
        if row["bytes"] != size or row["sha256"] != digest:
            raise RecoveryError("v006 failed-run hash drift: " + name)
        rows[name] = row
    failure = json.loads((V006_RUN / "import_failure_recovery_v006.json").read_text())
    summary = json.loads((V006_RUN / "lane_summary_recovery_v006.json").read_text())
    quarantine = json.loads((V006_RUN / "quarantine_receipt_v006.json").read_text())
    process = summary.get("import_process", {})
    retry = process.get("redirected_log_read_open_retry", {})
    expected_error = (
        "CAIRNWELL_2040_RUNTIME_V001_UNREAL_LANE_FAIL: body luminance detail "
        "clamp/default/mode drift: mismatched_fields=[\"input_names_or_defaults_or_clamp_mode\"] "
        "expected={\"clamp_mode\":\"CMODE_CLAMP\",\"input_names\":[\"\",\"Max\",\"Min\"],"
        "\"max_default\":1.15,\"min_default\":0.35} actual={\"clamp_mode\":\"CMODE_CLAMP\","
        "\"class\":\"MaterialExpressionClamp\",\"input_names\":[\"Max\",\"Min\",\"None\"],"
        "\"max_default\":1.149999976158142,\"min_default\":0.3499999940395355}"
    )
    if (failure.get("$schema")
            != "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v006/unreal-import/v6"
            or failure.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_UNREAL_IMPORT"
            or failure.get("error") != expected_error
            or summary.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_UNREAL_IMPORT_LANE"
            or summary.get("error")
            != "Recovery importer emitted a failure receipt despite strict process exit gate"
            or int(process.get("exit_code", -1)) != 0
            or int(process.get("process_id", -1)) != 37812
            or process.get("fatal_log_patterns") != []
            or int(retry.get("log_attempts", -1)) != 1
            or int(retry.get("stdout_attempts", -1)) != 8
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
            != "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_PARTIALS_QUARANTINED"
            or quarantine.get("incident_chain_sha256")
            != "7FD754B3BFC8FC3BF7CF42059EB16268A766C75290A76B92AFC107C24AA5E661"):
        raise RecoveryError("v006 primary/wrapper/quarantine incident identity drift")
    return rows


def v006_failure_preserved_rows() -> dict[str, dict]:
    failure = json.loads((V006_RUN / "import_failure_recovery_v006.json").read_text())
    rows = failure.get("namespace_files_preserved_for_recovery", {})
    expected_paths = {BASE.relative(DEST / rel) for rel in V006_PARTIAL_HASHES}
    if set(rows) != expected_paths:
        raise RecoveryError("v006 failure receipt eleven-package closure drift")
    return rows


def partial_rows(root: Path, label: str) -> dict[str, dict]:
    if not root.is_dir():
        raise RecoveryError(label + " root absent")
    actual = {path.relative_to(root).as_posix(): path
              for path in root.rglob("*") if path.is_file()}
    if set(actual) != set(V006_PARTIAL_HASHES):
        raise RecoveryError(label + " eleven-package closure drift")
    failure_rows = v006_failure_preserved_rows()
    output = {}
    for rel, (size, digest) in V006_PARTIAL_HASHES.items():
        row = BASE.file_row(actual[rel])
        if row["bytes"] != size or row["sha256"] != digest:
            raise RecoveryError(label + " package byte/hash drift: " + rel)
        if root == DEST:
            source_path = BASE.relative(DEST / rel)
            if failure_rows.get(source_path) != {
                    key: row[key] for key in ("bytes", "mtime_ns", "sha256")}:
                raise RecoveryError("v006 failure receipt package drift: " + source_path)
        output[rel] = row
    return output


def partial_contract_rows() -> dict[str, dict]:
    current = partial_rows(DEST, "v006 fresh destination")
    output = {}
    for rel, row in current.items():
        source_path = BASE.relative(DEST / rel)
        output[source_path] = {
            "source_path": source_path,
            "quarantine_path": BASE.relative(V006_QUARANTINE / rel),
            "bytes": row["bytes"],
            "mtime_ns": row["mtime_ns"],
            "sha256": row["sha256"],
        }
    return output


def verify_v005_quarantine(v006: dict) -> dict:
    paths = [PROJECT / row["quarantine_path"] for row in v006["partial_packages"].values()]
    snapshot = BASE.inventory(paths)
    if snapshot["file_count"] != 11 or not all(
            BASE.inside(path, V005_QUARANTINE) for path in paths):
        raise RecoveryError("v005 eleven-package quarantine closure drift")
    for expected in v006["partial_packages"].values():
        actual = BASE.file_row(PROJECT / expected["quarantine_path"])
        if any(actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256")):
            raise RecoveryError("v005 quarantined package drift: " + expected["quarantine_path"])
    return snapshot


def verify_v006_lane_drift(v006: dict) -> None:
    changed = set()
    for expected in v006["lane"]["files"]:
        if BASE.file_row(PROJECT / expected["path"]) != expected:
            changed.add(expected["path"])
    if changed != V007_LANE_CHANGED:
        raise RecoveryError("v006 prepared-lane drift is not exact v007 patch: " + repr(changed))


def v007_lane_snapshot(v006: dict) -> dict:
    paths = {row["path"] for row in v006["lane"]["files"]} | V007_ADDITIONS
    snapshot = BASE.inventory([PROJECT / rel for rel in paths])
    if {row["path"] for row in snapshot["files"]} != paths or snapshot["file_count"] != 33:
        raise RecoveryError("v007 prepared-lane path closure drift")
    return snapshot


def material_input_authority() -> dict:
    rows = v006_run_rows()
    failure_rows = v006_failure_preserved_rows()
    body_source = BASE.relative(
        DEST / "Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset")
    body = failure_rows[body_source]
    return {
        "classification": (
            "DETERMINISTIC_VALIDATOR_FALSE_NEGATIVE__UE_NAME_NONE_REFLECTS_AS_LITERAL_NONE__"
            "MATERIAL_GRAPH_CONNECTION_AND_ASSET_ARE_CORRECT"),
        "import_connection_name": "",
        "reflected_raw_name": "None",
        "canonical_graph_name": "",
        "canonicalization_rule": (
            "require exact Python str and exact class-specific reflected order; map only literal "
            "None to logical empty before zipping sources"),
        "duplicate_canonical_names_rejected": True,
        "raw_none_input_names_in_graph_evidence": False,
        "semantic_gates_relaxed": False,
        "audited_expression_links": {
            "MaterialExpressionLinearInterpolate": {
                "occurrences": 1, "raw_input_names": ["A", "B", "Alpha"],
                "canonical_input_names": ["A", "B", "Alpha"]},
            "MaterialExpressionMultiply": {
                "occurrences": 2, "raw_input_names": ["A", "B"],
                "canonical_input_names": ["A", "B"]},
            "MaterialExpressionClamp": {
                "occurrences": 1, "raw_input_names": ["None", "Min", "Max"],
                "canonical_input_names": ["", "Min", "Max"]},
            "MaterialExpressionDotProduct": {
                "occurrences": 1, "raw_input_names": ["A", "B"],
                "canonical_input_names": ["A", "B"]},
        },
        "engine_sources": external_source_rows(),
        "v006_import_failure": rows["import_failure_recovery_v006.json"],
        "v006_body_material_package": {
            "source_path": body_source,
            "quarantine_path": BASE.relative(
                V006_QUARANTINE / "Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset"),
            **body,
        },
        "observed_v006": {
            "reflected_raw_input_names_sorted": ["Max", "Min", "None"],
            "expected_logical_input_names_in_failed_validator": ["", "Max", "Min"],
            "clamp_mode": "CMODE_CLAMP",
            "min_default": 0.3499999940395355,
            "max_default": 1.149999976158142,
            "defaults_within_existing_tolerance": True,
            "asset_or_connection_drift": False,
        },
    }


def result_topology() -> dict:
    prefix = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v007/"
    return {
        "audit_root": BASE.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": BASE.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "quarantine_receipt": {
            "filename": "quarantine_receipt_v007.json", "$schema": prefix + "quarantine/v7",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_PARTIALS_QUARANTINED"},
        "import": {
            "receipt_filename": "import_receipt_recovery_v007.json",
            "failure_filename": "import_failure_recovery_v007.json",
            "$schema": prefix + "unreal-import/v7",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_FRESH_IMPORT__4_MESHES__12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE",
            "package_hash_field": "package_sha256"},
        "fresh_validation": {
            "receipt_filename": "fresh_process_validation_receipt_recovery_v007.json",
            "failure_filename": "fresh_process_validation_failure_recovery_v007.json",
            "$schema": prefix + "fresh-process-validation/v7",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED",
            "package_hash_fields": ["package_sha256_before_loads", "package_sha256_after_loads"]},
        "summary": {
            "filename": "lane_summary_recovery_v007.json",
            "$schema": prefix + "import-lane-summary/v7",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_GUARDED_IMPORT_AND_DISTINCT_READ_ONLY_RELOAD",
            "package_hash_field": "post_exit_package_sha256"},
        "required_incident_binding_fields": [
            "recovery_contract_sha256", "v001_failed_run_id", "v001_import_failure_sha256",
            "v002_failed_run_id", "v002_import_failure_sha256", "v003_failed_run_id",
            "v003_import_failure_sha256", "v004_failed_run_id", "v004_import_failure_sha256",
            "v005_failed_run_id", "v005_import_failure_sha256", "v006_failed_run_id",
            "v006_import_failure_sha256", "incident_chain_sha256", "quarantine_receipt"],
    }


def prior_state() -> tuple[dict, dict, dict, str, str]:
    contract, baseline, contract_digest, baseline_digest = BASE.load_original()
    v006 = exact_prior_contract()
    v006_run_rows()
    for key in ("v001_partial_packages", "v002_partial_packages",
                "v003_partial_packages", "v004_partial_packages"):
        BASE.verify_snapshot(v006["prior_quarantines"][key], key)
    verify_v005_quarantine(v006)
    verify_v006_lane_drift(v006)
    external_source_rows()
    return contract, baseline, v006, contract_digest, baseline_digest


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v007 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v007 recovery contract or sidecar")
    if RECOVERY_AUDIT_ROOT.exists() or V006_QUARANTINE.exists():
        raise RecoveryError("v007 result/quarantine already exists")
    contract, baseline, v006, _, _ = prior_state()
    run_rows = v006_run_rows()
    partials = partial_contract_rows()
    chain = {
        "v001": v006["incident_chain"]["v001"],
        "v002": v006["incident_chain"]["v002"],
        "v003": v006["incident_chain"]["v003"],
        "v004": v006["incident_chain"]["v004"],
        "v005": v006["incident_chain"]["v005"],
        "v006": {
            "failed_run_id": V006_RUN_ID,
            "run_root": BASE.relative(V006_RUN),
            "recovery_contract": BASE.file_row(V006_CONTRACT),
            "recovery_contract_sidecar": BASE.file_row(V006_CONTRACT_SHA),
            "import_failure": run_rows["import_failure_recovery_v006.json"],
            "lane_summary": run_rows["lane_summary_recovery_v006.json"],
            "quarantine_receipt": run_rows["quarantine_receipt_v006.json"],
            "files": run_rows,
            "primary_failure": (
                "UE5.8 reflected NAME_None as literal None while validator expected empty"),
            "wrapper_result": "strict process/log gate passed then failure receipt stopped lane",
        },
        "old_success_receipts_present": False,
    }
    chain["binding_sha256"] = object_hash(chain)
    payload = {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v7",
        "status": STATUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": {
            "contract": BASE.file_row(CONTRACT), "contract_sidecar": BASE.file_row(CONTRACT_SHA),
            "baseline": BASE.file_row(BASELINE), "baseline_sidecar": BASE.file_row(BASELINE_SHA)},
        "approved_source": {key: baseline["source"][key]
                            for key in ("file_count", "inventory_sha256")},
        "protected_project": {key: baseline["protected"][key]
                              for key in ("file_count", "inventory_sha256")},
        "incident_chain": chain,
        "prior_quarantines": {
            "v001_partial_packages": v006["prior_quarantines"]["v001_partial_packages"],
            "v002_partial_packages": v006["prior_quarantines"]["v002_partial_packages"],
            "v003_partial_packages": v006["prior_quarantines"]["v003_partial_packages"],
            "v004_partial_packages": v006["prior_quarantines"]["v004_partial_packages"],
            "v005_partial_packages": verify_v005_quarantine(v006),
        },
        "partial_packages": partials,
        "slot_normalization": v006["slot_normalization"],
        "runtime_uv_sanitization": v006["runtime_uv_sanitization"],
        "runtime_bounds_coordinate_conversion": v006["runtime_bounds_coordinate_conversion"],
        "exact_ue_enum_validation": v006["exact_ue_enum_validation"],
        "material_input_name_canonicalization": material_input_authority(),
        "quarantine": {
            "source_root": BASE.relative(DEST),
            "destination_root": BASE.relative(V006_QUARANTINE),
            "operation": "MOVE_DIRECTORY_ONLY__NO_DELETE",
            "automatic_delete_authorized": False,
            "rerun_after_any_recovery_result_authorized": False},
        "lane": v007_lane_snapshot(v006),
        "result_topology": result_topology(),
        "policy": {
            "unreal_launch_authorized_by_freeze": False,
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
            "enum_string_suffix_comparisons_forbidden": True,
            "unnamed_material_input_canonicalization_required": True,
            "raw_none_input_names_forbidden_in_graph_evidence": True,
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = BASE.sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    _, baseline, v006, contract_digest, baseline_digest = prior_state()
    digest = BASE.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise RecoveryError("v007 recovery sidecar drift")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    chain = payload.get("incident_chain", {})
    bound = dict(chain)
    declared = bound.pop("binding_sha256", None)
    if declared != object_hash(bound):
        raise RecoveryError("v007 incident-chain binding hash drift")
    expected_failures = {
        "v001": BASE.V001_IMPORT_FAILURE_SHA256,
        "v002": BASE.V002_IMPORT_FAILURE_SHA256,
        "v003": BASE.V003_IMPORT_FAILURE_SHA256,
        "v004": prior.prior.V004_IMPORT_FAILURE_SHA256,
        "v005": prior.V005_IMPORT_FAILURE_SHA256,
        "v006": V006_IMPORT_FAILURE_SHA256,
    }
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v7"
            or payload.get("status") != STATUS
            or payload.get("acknowledgement") != RUN_ACK_TOKEN
            or payload.get("original_authorities", {}).get("contract", {}).get("sha256")
            != contract_digest
            or payload.get("original_authorities", {}).get("baseline", {}).get("sha256")
            != baseline_digest
            or any(chain.get(version, {}).get("import_failure", {}).get("sha256") != digest
                   for version, digest in expected_failures.items())):
        raise RecoveryError("v007 recovery contract identity drift")
    for key in ("v001_partial_packages", "v002_partial_packages", "v003_partial_packages",
                "v004_partial_packages", "v005_partial_packages"):
        BASE.verify_snapshot(payload["prior_quarantines"][key], key)
    BASE.verify_snapshot(payload["lane"], "v007 prepared lane")
    for inherited in ("slot_normalization", "runtime_uv_sanitization",
                      "runtime_bounds_coordinate_conversion", "exact_ue_enum_validation"):
        if payload[inherited] != v006[inherited]:
            raise RecoveryError("v007 inherited authority drift: " + inherited)
    if payload["material_input_name_canonicalization"] != material_input_authority():
        raise RecoveryError("v007 material-input canonicalization authority drift")
    return payload, baseline


def verify_partial_contract(payload: dict, root: Path, label: str) -> None:
    rows = partial_rows(root, label) if root == DEST else {
        rel: BASE.file_row(path) for rel, path in {
            path.relative_to(root).as_posix(): path
            for path in root.rglob("*") if path.is_file()
        }.items()
    }
    if set(rows) != set(V006_PARTIAL_HASHES):
        raise RecoveryError(label + " eleven-package closure drift")
    for rel, actual in rows.items():
        source = BASE.relative(DEST / rel)
        expected = payload["partial_packages"][source]
        expected_path = source if root == DEST else expected["quarantine_path"]
        if (actual["path"] != expected_path or any(
                actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256"))):
            raise RecoveryError(label + " does not match contract: " + rel)


def verify_pre_quarantine() -> None:
    payload, _ = load_frozen()
    if V006_QUARANTINE.exists() or RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v007 quarantine/result already exists")
    verify_partial_contract(payload, DEST, "v006 fresh destination")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_PRE_QUARANTINE_REVERIFIED")
    print(BASE.sha256(OUTPUT))


def verify_post_quarantine() -> None:
    payload, _ = load_frozen()
    if DEST.exists():
        raise RecoveryError("fresh destination remains after v007 quarantine move")
    verify_partial_contract(payload, V006_QUARANTINE, "v006 package quarantine")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_POST_QUARANTINE_REVERIFIED")
    print(BASE.sha256(OUTPUT))


def verify_post_import() -> None:
    payload, baseline = load_frozen()
    verify_partial_contract(payload, V006_QUARANTINE, "v006 package quarantine")
    expected_packages = set(baseline["destination"]["expected_package_paths"])
    expected_disk = {
        spec["disk_path"]
        for collection in (baseline["modules"], baseline["textures"], baseline["materials"])
        for spec in collection.values()
    }
    actual_disk = {
        BASE.relative(path) for path in DEST.rglob("*") if path.is_file()
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
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_POST_IMPORT_REVERIFIED")
    print(BASE.sha256(OUTPUT))


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
