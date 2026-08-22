"""Fresh read-only validation for the preserved VehicleWIPNativeKit packages."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
SCRIPTS = PROJECT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import vehicle_wip_native_kit_unreal_runtime_v001 as lane

CONTRACT = SCRIPTS / "vehicle_wip_native_kit_coordinate_recovery_v002_contract.json"
SIDECAR = CONTRACT.with_suffix(".sha256")
ROOT = PROJECT / "Saved/Audits/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/CoordinateRecovery_v002"
PASS = "PASS__VEHICLE_WIP_NATIVE_KIT_V001_COORDINATE_RECOVERY_V002__READ_ONLY_16_ASSET_48_LOD_VALIDATION"
FAIL = "FAIL_CLOSED__VEHICLE_WIP_NATIVE_KIT_V001_COORDINATE_RECOVERY_V002"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def strict_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise RuntimeError(f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_pairs)


def files(expected: dict) -> dict:
    actual = {}
    for relative, row in expected.items():
        path = PROJECT / relative
        current = {"bytes": path.stat().st_size, "sha256": sha(path)}
        if current != row:
            raise RuntimeError(f"native package drift: {relative}")
        actual[relative] = current
    return actual


def corrected_baseline(contract: dict) -> dict:
    baseline = copy.deepcopy(read(SCRIPTS / "vehicle_wip_native_kit_unreal_import_baseline_v001.json"))
    expected = contract["corrected_expected_unreal_bounds"]
    if set(baseline["assets"]) != set(expected) or len(expected) != 16:
        raise RuntimeError("native vehicle closure drift")
    for key, bounds in expected.items():
        for lod, replacement in zip(baseline["assets"][key]["lods"], bounds):
            lod["expected_unreal_bounds"] = replacement
    return baseline


def main() -> None:
    root = ROOT / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    root.mkdir(parents=True, exist_ok=False)
    receipt, failure = root / "fresh_read_only_validation_receipt_v002.json", root / "fresh_read_only_validation_failure_v002.json"
    record = {"$schema": "lineboss/audit/vehicle-wip-native-kit-v001/coordinate-recovery-v002/fresh-read-only-validation/v2",
              "generated_utc": datetime.now(timezone.utc).isoformat(), "status": None,
              "writes_authorized": [str(receipt), str(failure)], "asset_mutation_count": 0,
              "reimport_overwrite_delete_authorized": False}
    before = after = None
    try:
        if sha(CONTRACT) != SIDECAR.read_text(encoding="ascii").split()[0].upper():
            raise RuntimeError("coordinate recovery sidecar drift")
        contract = read(CONTRACT)
        if contract.get("status") != "FROZEN__READ_ONLY_NATIVE_VEHICLE_BOUNDS_VALIDATION__NO_REIMPORT_OR_PROMOTION":
            raise RuntimeError("coordinate recovery status drift")
        if "-noassetregistrycachewrite" not in unreal.SystemLibrary.get_command_line().casefold():
            raise RuntimeError("read-only cache-write suppression missing")
        before = files(contract["destination_package_files"])
        baseline = corrected_baseline(contract)
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        assets = {key: lane.validate_mesh(key, baseline["assets"][key], baseline, subsystem)
                  for key in sorted(baseline["assets"])}
        after = files(contract["destination_package_files"])
        if after != before:
            raise RuntimeError("read-only validation changed a native vehicle package")
        record.update({"status": PASS, "coordinate_contract_sha256": sha(CONTRACT),
                       "v001_import_failure": contract["v001_import_failure"], "proof": contract["proof"],
                       "package_files_before": before, "package_files_after": after, "assets": assets,
                       "asset_count": 16, "authored_lod_count": 48, "failures": []})
        receipt.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        unreal.log("LINE_BOSS_VEHICLE_WIP_NATIVE_KIT_COORDINATE_RECOVERY_V002_PASS")
    except Exception as error:
        record.update({"status": FAIL, "error": str(error), "traceback": traceback.format_exc(),
                       "package_files_before": before, "package_files_after": after})
        failure.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        raise


if __name__ == "__main__":
    main()
