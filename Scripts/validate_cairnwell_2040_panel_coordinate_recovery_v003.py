"""One fresh, read-only validation of the frozen panel-coordinate correction."""

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

import cairnwell_2040_panel_modules_v001 as lane
import cairnwell_2040_panel_modules_recovery_v002 as v002


CONTRACT = SCRIPTS / "cairnwell_2040_panel_coordinate_recovery_v003_contract.json"
SIDECAR = CONTRACT.with_suffix(".sha256")
RECOVERY_ROOT = PROJECT / ("Saved/Audits/OneFactory/Vehicles/"
    "Cairnwell2040PanelModules_v001/UnrealImportLane_v001/Recovery_v003")
PASS = "PASS__CAIRNWELL_2040_PANEL_COORDINATE_RECOVERY_V003__READ_ONLY_11_PANEL_33_LOD_VALIDATION"
FAIL = "FAIL_CLOSED__CAIRNWELL_2040_PANEL_COORDINATE_RECOVERY_V003"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_pairs)


def file_rows(expected: dict) -> dict:
    rows = {}
    for relative, expected_row in expected.items():
        path = PROJECT / relative
        actual = {"bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns,
                  "sha256": sha(path)}
        if actual != expected_row:
            raise RuntimeError(f"panel package drift: {relative}")
        rows[relative] = actual
    return rows


def corrected_baseline(contract: dict) -> dict:
    baseline = copy.deepcopy(read(lane.BASELINE))
    expected = contract["corrected_expected_unreal_bounds"]
    if set(baseline["modules"]) != set(expected) or len(expected) != 11:
        raise RuntimeError("panel module closure drift")
    for panel_id, bounds in expected.items():
        lods = baseline["modules"][panel_id]["lods"]
        if len(lods) != 3 or len(bounds) != 3:
            raise RuntimeError(f"LOD closure drift: {panel_id}")
        for lod, corrected in zip(lods, bounds):
            lod["expected_unreal_bounds"] = corrected
    return baseline


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = RECOVERY_ROOT / f"{stamp}-{uuid.uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=False)
    receipt = root / "fresh_process_validation_receipt_coordinate_recovery_v003.json"
    failure = root / "fresh_process_validation_failure_coordinate_recovery_v003.json"
    record = {
        "$schema": "lineboss/audit/cairnwell-2040-panel-modules-v001/coordinate-recovery-v003/fresh-read-only-validation/v3",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": None,
        "writes_authorized": [str(receipt), str(failure)],
        "asset_mutation_count": 0,
        "reimport_overwrite_delete_authorized": False,
    }
    before = after = None
    try:
        if sha(CONTRACT) != SIDECAR.read_text(encoding="ascii").split()[0].upper():
            raise RuntimeError("coordinate contract sidecar drift")
        contract = read(CONTRACT)
        if contract.get("status") != "FROZEN__READ_ONLY_PANEL_BOUNDS_VALIDATION__NO_REIMPORT_OR_PROMOTION":
            raise RuntimeError("coordinate contract state drift")
        command_line = unreal.SystemLibrary.get_command_line()
        if "-noassetregistrycachewrite" not in command_line.casefold():
            raise RuntimeError("read-only cache-write suppression missing")
        before = file_rows(contract["destination_package_files"])
        baseline = corrected_baseline(contract)
        v002.install_persisted_dependency_query(lane, unreal)
        measured = lane.validate_all_assets(baseline, require_persisted_dependencies=True)
        after = file_rows(contract["destination_package_files"])
        if after != before:
            raise RuntimeError("read-only validation changed a panel package")
        record.update({
            "status": PASS,
            "coordinate_contract_sha256": sha(CONTRACT),
            "source_import_contract": contract["source_import_contract"],
            "recovery_v002_failure": contract["recovery_v002_failure"],
            "proof": contract["proof"],
            "panel_package_files_before": before,
            "panel_package_files_after": after,
            "assets": measured,
            "mesh_count": 11,
            "authored_lod_count": 33,
            "failures": [],
        })
        receipt.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_CAIRNWELL_PANEL_COORDINATE_RECOVERY_V003_PASS")
    except Exception as error:
        record.update({"status": FAIL, "error": str(error), "traceback": traceback.format_exc(),
                       "panel_package_files_before": before, "panel_package_files_after": after})
        failure.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
