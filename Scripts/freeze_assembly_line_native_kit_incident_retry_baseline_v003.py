"""Freeze the one-use v003 retry after v002 command-line path escaping failure."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUTPUT = PROJECT / "Scripts/assembly_line_native_kit_incident_retry_baseline_v003_final.json"
SUPERSEDED_BASELINE_RELATIVE = "Scripts/assembly_line_native_kit_incident_retry_baseline_v003.json"
EXPECTED_SUPERSEDED_BASELINE_SHA256 = "B465F68B5DC540B7C68EBCB6BD4C682271A2826A8841A902EC98FBAE3DCAA9B5"
SETTLED_CAPTURE_BRIDGE_HASHES = {
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h":
        "2C5442B15B94504CEA085A3F46F4740BCC4FD0A83CDE70DB37E3C7D0FC04673B",
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp":
        "849C7E1ACD6A02B27126831202E774E8C922E422050904EC3DF5349C6D01CA30",
}
V002_BASELINE = PROJECT / "Scripts/assembly_line_native_kit_incident_recovery_baseline_v002.json"
EXPECTED_V002_BASELINE_SHA256 = "CDD41027FCBB556ED3A3EF472B804275677F023CDCCA8D394DC454BBF94C1520"
FAILED_RUN_RELATIVE = "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v002/20260815T030646Z-e8c9a5eb"
FAILED_RUN = PROJECT / FAILED_RUN_RELATIVE
V003_AUDIT_RELATIVE = "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v003"
V002_FILES = (
    "Scripts/assembly_line_native_kit_incident_recovery_baseline_v002.json",
    "Scripts/freeze_assembly_line_native_kit_incident_recovery_baseline_v002.py",
    "Scripts/assembly_line_native_kit_incident_recovery_runtime_v002.py",
    "Scripts/revalidate_assembly_line_native_kit_incident_v002.py",
    "Scripts/run_assembly_line_native_kit_incident_recovery_v002.ps1",
    "Scripts/tests/test_assembly_line_native_kit_incident_recovery_v002.py",
    "Docs/AssemblyShop/ASSEMBLY_LINE_NATIVE_KIT_INCIDENT_RECOVERY_v002.md",
    "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/StaticPreparation_v002/incident_recovery_static_freeze_v002.json",
)
EXPECTED_V002_HASHES = {
    V002_FILES[0]: EXPECTED_V002_BASELINE_SHA256,
    V002_FILES[1]: "FDB7A841FED8F6CCC6240CF3DC2F9CC017DC60DE272CE32AC562C4AAB7325E5C",
    V002_FILES[2]: "405244C7CF359085A42AD05B3CC0A17385E7BB6B6BE3463C2F0612298739454F",
    V002_FILES[3]: "7263BF87CBA3049555EE36BC378EFE284C9279565A501BDDE81F33700F9455C9",
    V002_FILES[4]: "7390D3091652B91015844AF2F8AF1A697D9B22F4B5F9C689296ECD30CFDC8A99",
    V002_FILES[5]: "354012EC832880CA0767B3A73AA271456335280B73223B29E5B5F654B89885AD",
    V002_FILES[6]: "FDE2326EECAE1D1BBB153B9A19735D9D44B53EA204C86E65B254961FC8A00DB3",
    V002_FILES[7]: "4C725C9A41BFDDFC3AC299289450F166B1C7F0325DE0C250653DF43FC397ACD3",
}
FAILED_RUN_HASHES = {
    "fresh_load_recovery_validation.log": "9BC7F87884532B794F4FB49D9B13082A6ED4C48D0C46325730E2DBB4E78E9B72",
    "fresh_load_recovery_validation.stderr.log": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    "fresh_load_recovery_validation.stdout.log": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    "incident_recovery_summary_v002.json": "CEBFD5239081C66FFCEEE84FCDB593DE5D588D01C06B4B6B5F89CEE7FD3362EC",
}
BASE_GROUPS = (
    {"name": "project_descriptor", "files": ("LineBossCarFactory.uproject",)},
    {"name": "complete_source_tree_278", "roots": ("Source",)},
    {"name": "complete_config_tree", "roots": ("Config",)},
    {"name": "campaign_save_games", "roots": ("Saved/SaveGames",), "allow_empty": True},
    {"name": "all_existing_content_including_eight_imported_packages", "roots": ("Content",)},
    {"name": "frozen_assembly_source_authority", "roots": ("SourceAssets/Candidate/AssemblyShop/AssemblyLineNativeKit_v001",)},
    {"name": "v002_recovery_static_authority", "files": V002_FILES},
    {"name": "failed_v002_recovery_run_exact_evidence", "roots": (FAILED_RUN_RELATIVE,)},
    {"name": "superseded_v003_pre_ui_v005_baseline", "files": (SUPERSEDED_BASELINE_RELATIVE,)},
)


def fail(message: str) -> None:
    raise RuntimeError("ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_BASELINE_V003_FAIL: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT.resolve()).as_posix()


def row(path: Path) -> dict:
    if not path.is_file():
        fail("required file missing: " + str(path))
    stat = path.stat()
    return {"path": relative(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}


def canonical_hash(rows: list[dict]) -> str:
    compact = [{key: item[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
               for item in sorted(rows, key=lambda item: item["path"].casefold())]
    return hashlib.sha256(json.dumps(compact, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()


def groups_from_v002(v002: dict) -> tuple[dict, ...]:
    maps = tuple({"name": f"exact_{name}_map", "files": (item["path"],)}
                 for name, item in v002["protected"]["maps"].items())
    original_groups = tuple(
        {"name": item["name"], "files": tuple(item.get("files", ())), "roots": tuple(item.get("roots", ())),
         "allow_empty": bool(item.get("allow_empty", False))}
        for item in v002["protected"]["groups"]
        if item["name"] in {"original_lane_static_authority", "incident_original_run_receipts_and_logs"}
    )
    return BASE_GROUPS + original_groups + maps


def protected_inventory(specs: tuple[dict, ...]) -> tuple[list[dict], list[dict]]:
    paths, membership, groups = {}, defaultdict(set), []
    for spec in specs:
        selected = {PROJECT / item for item in spec.get("files", ())}
        for item in spec.get("roots", ()):
            root = PROJECT / item
            if not root.is_dir():
                if spec.get("allow_empty"):
                    continue
                fail("protected root missing: " + str(root))
            selected.update(path for path in root.rglob("*") if path.is_file())
        if not selected and not spec.get("allow_empty"):
            fail("protected group empty: " + spec["name"])
        group_paths = []
        for path in sorted(selected, key=lambda item: str(item).casefold()):
            rel = relative(path)
            paths[rel] = path
            membership[rel].add(spec["name"])
            group_paths.append(rel)
        groups.append({"name": spec["name"], "files": list(spec.get("files", ())),
                       "roots": list(spec.get("roots", ())), "allow_empty": bool(spec.get("allow_empty", False)),
                       "paths": group_paths, "file_count": len(group_paths)})
    rows = []
    for rel in sorted(paths, key=str.casefold):
        item = row(paths[rel])
        item["groups"] = sorted(membership[rel])
        rows.append(item)
    return groups, rows


def incident() -> dict:
    if sha256(PROJECT / SUPERSEDED_BASELINE_RELATIVE) != EXPECTED_SUPERSEDED_BASELINE_SHA256:
        fail("superseded pre-UI-v005 v003 baseline changed")
    for rel, expected in SETTLED_CAPTURE_BRIDGE_HASHES.items():
        if sha256(PROJECT / rel) != expected:
            fail("settled CaptureBridge source changed: " + rel)
    if sha256(V002_BASELINE) != EXPECTED_V002_BASELINE_SHA256:
        fail("v002 successor baseline changed")
    for rel, expected in EXPECTED_V002_HASHES.items():
        if sha256(PROJECT / rel) != expected:
            fail("v002 static authority changed: " + rel)
    actual_files = {path.name: path for path in FAILED_RUN.iterdir() if path.is_file()}
    if set(actual_files) != set(FAILED_RUN_HASHES):
        fail("failed v002 recovery run file inventory drift")
    evidence = []
    for name, expected in FAILED_RUN_HASHES.items():
        item = row(actual_files[name])
        if item["sha256"] != expected:
            fail("failed v002 recovery evidence drift: " + name)
        evidence.append(item)
    summary = json.loads((FAILED_RUN / "incident_recovery_summary_v002.json").read_text(encoding="utf-8-sig"))
    if (summary.get("status") != "FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002" or
            summary.get("error") != "Recovery PASS receipt missing" or summary.get("importer_process") is not None or
            int(summary.get("validator_process", {}).get("exit_code", -1)) != 0):
        fail("failed v002 summary identity drift")
    log_bytes = (FAILED_RUN / "fresh_load_recovery_validation.log").read_bytes()
    control_fragment = b"Scripts" + bytes([13]) + b"evalidate_assembly_line_native_kit_incident_v002.py"
    if (b"Could not load Python file" not in log_bytes or control_fragment not in log_bytes or
            b"LINE_BOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002_PASS" in log_bytes):
        fail("failed v002 command-line carriage-return incident proof drift")
    if ((FAILED_RUN / "fresh_load_recovery_validation_receipt_v002.json").exists() or
            (FAILED_RUN / "fresh_load_recovery_validation_failure_v002.json").exists()):
        fail("Python unexpectedly executed during v002 failed command-line attempt")
    return {"classification": "EXECUTE_PYTHON_PATH_BACKSLASH_R_BECAME_CARRIAGE_RETURN",
            "failed_run": FAILED_RUN_RELATIVE, "evidence": evidence,
            "evidence_inventory_sha256": canonical_hash(evidence),
            "python_executed": False, "asset_validation_executed": False,
            "content_writes": [], "original_v002_baseline": row(V002_BASELINE)}


def build() -> dict:
    if Path.cwd().resolve() != PROJECT.resolve():
        fail("run from exact project root")
    if OUTPUT.exists():
        fail("refusing to overwrite v003 retry baseline")
    if (PROJECT / V003_AUDIT_RELATIVE).exists():
        fail("v003 recovery result namespace already exists")
    v002 = json.loads(V002_BASELINE.read_text(encoding="utf-8-sig"))
    retry_incident = incident()
    specs = groups_from_v002(v002)
    groups, rows = protected_inventory(specs)
    return {"$schema": "lineboss/assembly-native-kit-v001/incident-retry-baseline/v3",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FROZEN__ASSEMBLY_NATIVE_KIT_V001_INCIDENT_RETRY_BASELINE_V003__FORWARD_SLASH_EXECUTE_PATH",
            "project": v002["project"], "incident": v002["incident"], "retry_incident": retry_incident,
            "settled_concurrent_source": {
                "authority": "OneFactory v005 SOURCE FROZEN",
                "files": [{"path": rel, "sha256": digest}
                          for rel, digest in sorted(SETTLED_CAPTURE_BRIDGE_HASHES.items())],
                "superseded_pre_v005_baseline": row(PROJECT / SUPERSEDED_BASELINE_RELATIVE),
            },
            "source": v002["source"], "assets": v002["assets"], "import_contract": v002["import_contract"],
            "destination": v002["destination"],
            "protected": {"groups": groups, "files": rows, "file_count": len(rows),
                          "inventory_sha256": canonical_hash(rows), "maps": v002["protected"]["maps"]},
            "command_line_contract": {"execute_python_path_separator": "/",
                                      "backslash_or_control_character_authorized": False,
                                      "absolute_existing_python_file_required": True},
            "policy": {**v002["policy"], "exactly_one_recovery_attempt": True,
                       "v002_retry_authorized": False, "v003_retry_authorized": True,
                       "failed_v002_recovery_evidence_mutation_authorized": False}}


def verify() -> dict:
    if not OUTPUT.is_file():
        fail("verify-only requires v003 retry baseline")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8-sig"))
    incident()
    specs = groups_from_v002(json.loads(V002_BASELINE.read_text(encoding="utf-8-sig")))
    groups, rows = protected_inventory(specs)
    wanted_groups = {item["name"]: item for item in payload["protected"]["groups"]}
    if {item["name"] for item in groups} != set(wanted_groups):
        fail("v003 protected group inventory drift")
    for group in groups:
        if group["paths"] != wanted_groups[group["name"]]["paths"]:
            fail("v003 protected group path drift: " + group["name"])
    wanted = {item["path"]: item for item in payload["protected"]["files"]}
    if {item["path"] for item in rows} != set(wanted):
        fail("v003 protected union drift")
    for item in rows:
        expected = wanted[item["path"]]
        if any(item[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256")):
            fail("v003 protected file drift: " + item["path"])
    digest = canonical_hash(rows)
    if digest != payload["protected"]["inventory_sha256"]:
        fail("v003 protected inventory hash drift")
    return {"status": "PASS__V003_INCIDENT_BOUND_RETRY_BASELINE_FULL_REVERIFY",
            "baseline_sha256": sha256(OUTPUT), "source_files": 278, "target_packages": 8,
            "protected_files": len(rows), "protected_inventory_sha256": digest,
            "failed_v002_evidence_files": 4}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(), indent=2))
    else:
        payload = build()
        OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "path": str(OUTPUT), "sha256": sha256(OUTPUT),
                          "protected_files": payload["protected"]["file_count"],
                          "failed_v002_evidence_files": 4}, indent=2))


if __name__ == "__main__":
    main()
