"""Freeze the read-only incident recovery baseline for Assembly kit import v001.

Offline only. It preserves and pins the original lane and successful import,
accepting exactly the two settled OneFactory capture-bridge Source additions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUTPUT = PROJECT / "Scripts/assembly_line_native_kit_incident_recovery_baseline_v002.json"
SOURCE_ROOT = PROJECT / "SourceAssets/Candidate/AssemblyShop/AssemblyLineNativeKit_v001"
TARGET_RELATIVE = "Content/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001"
TARGET_NAMESPACE = "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001"
ORIGINAL_RUN_RELATIVE = "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/UnrealImportLane_v001/20260815T025138Z-2b421583"
RECOVERY_AUDIT_RELATIVE = "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v002"
ORIGINAL_BASELINE = PROJECT / "Scripts/assembly_line_native_kit_unreal_import_baseline_v001.json"
IMPORT_RECEIPT = PROJECT / ORIGINAL_RUN_RELATIVE / "import_receipt_v001.json"
FAILURE_RECEIPT = PROJECT / ORIGINAL_RUN_RELATIVE / "fresh_load_validation_failure_v001.json"
EXPECTED_ORIGINAL_BASELINE_SHA256 = "041C802023D14ADE7EC418EF7488679D7F4A03550471AE38E2DC80B310E731BA"
EXPECTED_IMPORT_RECEIPT_SHA256 = "C0E1F8D3E7B6EEBB2780067671AF408C53368DEA9370B3AA56B9F7F3AAFD49F7"
EXPECTED_FAILURE_RECEIPT_SHA256 = "269F732E2433EEC7948EB17F6FFE453D18F6CEEA3CF70239A99B67517799D57B"
SOURCE_ADDITIONS = {
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h": "5D24296B0FF7239276793DCA0232DBFB239E6C393B0ED7EA2D767F15BFF7F8C8",
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp": "447C04E64A2F322754C6F78523A34A59D9E133B3D949B766064D9FD112F15ECD",
}
ORIGINAL_LANE_FILES = (
    "Scripts/assembly_line_native_kit_unreal_import_baseline_v001.json",
    "Scripts/freeze_assembly_line_native_kit_unreal_import_baseline_v001.py",
    "Scripts/assembly_line_native_kit_unreal_runtime_v001.py",
    "Scripts/import_assembly_line_native_kit_v001.py",
    "Scripts/validate_assembly_line_native_kit_v001.py",
    "Scripts/run_assembly_line_native_kit_unreal_import_lane_v001.ps1",
    "Scripts/tests/test_assembly_line_native_kit_unreal_import_lane_v001.py",
    "Docs/AssemblyShop/ASSEMBLY_LINE_NATIVE_KIT_UNREAL_IMPORT_LANE_v001.md",
    "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/StaticPreparation_v001/static_freeze_v001.json",
)
EXPECTED_ORIGINAL_LANE_HASHES = {
    ORIGINAL_LANE_FILES[0]: EXPECTED_ORIGINAL_BASELINE_SHA256,
    ORIGINAL_LANE_FILES[1]: "A7CFD24D4A3804EFA0B0003749B1D85D48905533F0A59770BC8AA0256C9397DC",
    ORIGINAL_LANE_FILES[2]: "597638FE1A11AD67B3F54090B57529C07757C48A8378EAF84F90157DCA2D73F0",
    ORIGINAL_LANE_FILES[3]: "15DCBE67A54D0A8E78E4C7D30C9520AD173B02F72003ECFC166DFAF23C8A9B76",
    ORIGINAL_LANE_FILES[4]: "D19420B06776BBDF2FFC2B19ADB3B66458171FB37DD2775BE99906317F82C6BB",
    ORIGINAL_LANE_FILES[5]: "4D0B3FD9E0DCDAFA72081F110BF019573D762AE19AB4B7F97A7377CF82832079",
    ORIGINAL_LANE_FILES[6]: "EEDD54700543B9AEDE2894EDC20CE8D0CDFD05C3D9428D012878834D1F96742B",
    ORIGINAL_LANE_FILES[7]: "C6D8358D957511FCEACFBA7A9DC3EA0DD25A7614EE8710238C721350D9403BB4",
    ORIGINAL_LANE_FILES[8]: "6B677A80442112AB675E01B8733E1842940769579895938BC254315AE5B86E7D",
}
MAPS = {
    "press_v913": "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap",
    "restored_press": "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap",
    "body": "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap",
    "paint": "Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap",
    "one_factory": "Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap",
}
EXPECTED_MAP_HASHES = {
    "press_v913": "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
    "restored_press": "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
    "body": "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F",
    "paint": "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069",
    "one_factory": "750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682",
}
PROTECTED_GROUPS = (
    {"name": "project_descriptor", "files": ("LineBossCarFactory.uproject",)},
    {"name": "complete_source_tree_278", "roots": ("Source",)},
    {"name": "complete_config_tree", "roots": ("Config",)},
    {"name": "campaign_save_games", "roots": ("Saved/SaveGames",), "allow_empty": True},
    {"name": "all_existing_content_including_eight_imported_packages", "roots": ("Content",)},
    {"name": "frozen_assembly_source_authority", "roots": ("SourceAssets/Candidate/AssemblyShop/AssemblyLineNativeKit_v001",)},
    {"name": "original_lane_static_authority", "files": ORIGINAL_LANE_FILES},
    {"name": "incident_original_run_receipts_and_logs", "roots": (ORIGINAL_RUN_RELATIVE,)},
    *({"name": f"exact_{name}_map", "files": (path,)} for name, path in MAPS.items()),
)


def fail(message: str) -> None:
    raise RuntimeError("ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_BASELINE_V002_FAIL: " + message)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT.resolve()).as_posix()


def row(path: Path) -> dict:
    if not path.is_file():
        fail("required file missing: " + str(path))
    stat = path.stat()
    return {"path": relative(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}


def canonical_hash(rows: list[dict]) -> str:
    data = [{key: item[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
            for item in sorted(rows, key=lambda item: item["path"].casefold())]
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()


def protected_inventory() -> tuple[list[dict], list[dict]]:
    paths, memberships = {}, defaultdict(set)
    groups = []
    for spec in PROTECTED_GROUPS:
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
            memberships[rel].add(spec["name"])
            group_paths.append(rel)
        groups.append({"name": spec["name"], "files": list(spec.get("files", ())),
                       "roots": list(spec.get("roots", ())), "allow_empty": bool(spec.get("allow_empty", False)),
                       "paths": group_paths, "file_count": len(group_paths)})
    rows = []
    for rel in sorted(paths, key=str.casefold):
        item = row(paths[rel])
        item["groups"] = sorted(memberships[rel])
        rows.append(item)
    return groups, rows


def validate_incident_inputs(original: dict, imported: dict, failure: dict) -> dict:
    if sha256(ORIGINAL_BASELINE) != EXPECTED_ORIGINAL_BASELINE_SHA256:
        fail("original baseline changed")
    if sha256(IMPORT_RECEIPT) != EXPECTED_IMPORT_RECEIPT_SHA256:
        fail("PASS import receipt changed")
    if sha256(FAILURE_RECEIPT) != EXPECTED_FAILURE_RECEIPT_SHA256:
        fail("original validation failure receipt changed")
    for rel, expected in EXPECTED_ORIGINAL_LANE_HASHES.items():
        if sha256(PROJECT / rel) != expected:
            fail("original lane authority changed: " + rel)
    old_source = next(group for group in original["protected"]["groups"] if group["name"] == "complete_source_tree")
    current = {relative(path) for path in (PROJECT / "Source").rglob("*") if path.is_file()}
    added = current - set(old_source["paths"])
    removed = set(old_source["paths"]) - current
    if len(current) != 278 or added != set(SOURCE_ADDITIONS) or removed:
        fail("incident is not exactly the two pinned Source additions")
    additions = {}
    for rel, expected in SOURCE_ADDITIONS.items():
        actual = row(PROJECT / rel)
        if actual["sha256"] != expected:
            fail("settled Source addition hash drift: " + rel)
        additions[rel] = actual
    if (imported.get("status") != "PASS__HASH_GUARDED_FRESH_IMPORT__8_ASSETS__24_AUTHORED_LODS__ASSEMBLY_NATIVE_KIT_V001" or
            imported.get("baseline_sha256") != EXPECTED_ORIGINAL_BASELINE_SHA256 or imported.get("asset_count") != 8 or
            imported.get("lod_count_per_asset") != 3 or imported.get("source_fbx_count") != 24 or
            imported.get("custom_lods_appended") != 16):
        fail("successful import receipt identity drift")
    if (failure.get("status") != "FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_V001_FRESH_LOAD_VALIDATION" or
            "protected group inventory drift: complete_source_tree" not in failure.get("error", "") or
            failure.get("asset_or_level_saves") != [] or failure.get("imports_reimports_deletes") != []):
        fail("original validator failure is not the exact read-only Source-inventory incident")
    target_files = [row(path) for path in (PROJECT / TARGET_RELATIVE).rglob("*") if path.is_file()]
    receipt_files = imported["namespace_disk_files"]
    if len(target_files) != 8 or {item["path"] for item in target_files} != set(receipt_files):
        fail("current target inventory is not the exact successful import")
    for item in target_files:
        wanted = receipt_files[item["path"]]
        if any(item[key] != wanted[key] for key in ("bytes", "mtime_ns", "sha256")):
            fail("current imported package drift: " + item["path"])
    return {"old_source_count": len(old_source["paths"]), "settled_source_count": len(current),
            "exact_added_files": additions, "removed_files": [], "target_packages": target_files,
            "target_inventory_sha256": canonical_hash(target_files)}


def build() -> dict:
    if Path.cwd().resolve() != PROJECT.resolve():
        fail("run from exact project root")
    if OUTPUT.exists():
        fail("refusing to overwrite successor baseline")
    if (PROJECT / RECOVERY_AUDIT_RELATIVE).exists():
        fail("successor recovery result namespace already exists")
    original = json.loads(ORIGINAL_BASELINE.read_text(encoding="utf-8-sig"))
    imported = json.loads(IMPORT_RECEIPT.read_text(encoding="utf-8-sig"))
    failure = json.loads(FAILURE_RECEIPT.read_text(encoding="utf-8-sig"))
    incident = validate_incident_inputs(original, imported, failure)
    groups, protected_rows = protected_inventory()
    protected = {item["path"]: item for item in protected_rows}
    for name, path in MAPS.items():
        if protected[path]["sha256"] != EXPECTED_MAP_HASHES[name]:
            fail("exact protected map drift: " + name)
    return {
        "$schema": "lineboss/assembly-native-kit-v001/incident-recovery-baseline/v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FROZEN__ASSEMBLY_NATIVE_KIT_V001_INCIDENT_RECOVERY_BASELINE_V002__READ_ONLY_REVALIDATION_ONLY",
        "project": {"root": str(PROJECT), "uproject": "LineBossCarFactory.uproject", "game_name": "LineBossCarFactory"},
        "incident": {"classification": "INTENTIONAL_CONCURRENT_SOURCE_ADDITIONS_ONLY",
                     "original_baseline": row(ORIGINAL_BASELINE), "successful_import_receipt": row(IMPORT_RECEIPT),
                     "original_validation_failure_receipt": row(FAILURE_RECEIPT), **incident},
        "source": original["source"],
        "assets": original["assets"],
        "import_contract": original["import_contract"],
        "destination": {**original["destination"], "state": "EXISTING_EXACT_PASS_IMPORT__READ_ONLY"},
        "protected": {"groups": groups, "files": protected_rows, "file_count": len(protected_rows),
                      "inventory_sha256": canonical_hash(protected_rows),
                      "maps": {name: protected[path] for name, path in MAPS.items()}},
        "policy": {"importer_authorized": False, "content_writes_authorized": False,
                   "asset_or_level_saves_authorized": False, "reimport_delete_overwrite_authorized": False,
                   "original_baseline_run_receipts_logs_mutation_authorized": False,
                   "independent_fresh_process_required": True, "exactly_one_recovery_attempt": True,
                   "partial_or_failed_recovery_evidence_must_be_preserved": True},
    }


def verify() -> dict:
    if not OUTPUT.is_file():
        fail("verify-only requires frozen successor baseline")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8-sig"))
    original = json.loads(ORIGINAL_BASELINE.read_text(encoding="utf-8-sig"))
    imported = json.loads(IMPORT_RECEIPT.read_text(encoding="utf-8-sig"))
    failure = json.loads(FAILURE_RECEIPT.read_text(encoding="utf-8-sig"))
    validate_incident_inputs(original, imported, failure)
    groups, rows = protected_inventory()
    expected_groups = {item["name"]: item for item in payload["protected"]["groups"]}
    if {item["name"] for item in groups} != set(expected_groups):
        fail("successor protected group inventory drift")
    for group in groups:
        if group["paths"] != expected_groups[group["name"]]["paths"]:
            fail("successor protected group path drift: " + group["name"])
    expected = {item["path"]: item for item in payload["protected"]["files"]}
    if {item["path"] for item in rows} != set(expected):
        fail("successor protected union drift")
    for item in rows:
        wanted = expected[item["path"]]
        if any(item[key] != wanted[key] for key in ("bytes", "mtime_ns", "sha256")):
            fail("successor protected file drift: " + item["path"])
    digest = canonical_hash(rows)
    if digest != payload["protected"]["inventory_sha256"]:
        fail("successor protected canonical hash drift")
    return {"status": "PASS__INCIDENT_BOUND_SUCCESSOR_BASELINE_FULL_REVERIFY",
            "baseline_sha256": sha256(OUTPUT), "source_files": 278,
            "protected_files": len(rows), "protected_inventory_sha256": digest,
            "target_packages": 8, "original_import_receipt_sha256": EXPECTED_IMPORT_RECEIPT_SHA256}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(), indent=2))
        return
    payload = build()
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "path": str(OUTPUT), "sha256": sha256(OUTPUT),
                      "protected_files": payload["protected"]["file_count"], "source_files": 278,
                      "target_packages": 8}, indent=2))


if __name__ == "__main__":
    main()
