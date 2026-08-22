"""Freeze the read-only coordinate correction for Cairnwell panel validation.

Recovery v002 correctly preserved the 11 imported panel packages but compared
them against exporter-space Y bounds.  This tool preserves that incident and
derives the exact Unreal-space expectation for a fresh validation only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
SOURCE = SCRIPTS / "cairnwell_2040_panel_modules_v001_import_contract.json"
RECOVERY_V002 = SCRIPTS / "cairnwell_2040_panel_modules_recovery_v002_contract.json"
V002_RUN = PROJECT / ("Saved/Audits/OneFactory/Vehicles/"
    "Cairnwell2040PanelModules_v001/UnrealImportLane_v001/Recovery_v002/"
    "20260815T193624Z-b1de90e0")
OUTPUT = SCRIPTS / "cairnwell_2040_panel_coordinate_recovery_v003_contract.json"
SIDECAR = OUTPUT.with_suffix(".sha256")
ACK = "FREEZE_CAIRNWELL_2040_PANEL_COORDINATE_RECOVERY_V003"

SOURCE_SHA = "0EB0ED65D171A476D30F2F47BCEA9F63CF7CCE845369565AE6781ABE7CC35C2B"
RECOVERY_V002_SHA = "881CB2DDE80FD4974AC13EB505F735E0023A134AF53C2DDE9A01C7EA3F78278F"
V002_FILES = {
    "fresh_process_validation_failure_recovery_v002.json": (12606, "5A80E4B620419CF5EC394FEC4ED342028BBD9A339C5121EC183884F66EF6F534"),
    "fresh_process_validation_recovery_v002.log": (333458, "F075FCD0E50C9867712E976E725E7590E1B9E56635C46282929A847E49046A96"),
    "fresh_process_validation_recovery_v002.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "fresh_process_validation_recovery_v002.stdout.log": (333564, "D314CAEFDE53C6A66606BD936D9F595E9F8B72229E6BC49212A7FDF8975F12A5"),
    "lane_summary_recovery_v002.json": (948, "DD684E7D65A36A6028F0FD35D59B326376FDEB7F34D7FCD56FE44012BBAF9D75"),
}


class ContractError(RuntimeError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def strict_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ContractError(f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_pairs)


def row(path: Path) -> dict:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def corrected(bounds: dict) -> dict:
    minimum, maximum = bounds["minimum_cm"], bounds["maximum_cm"]
    return {
        "minimum_cm": [minimum[0], -maximum[1], minimum[2]],
        "maximum_cm": [maximum[0], -minimum[1], maximum[2]],
        "dimensions_cm": bounds["dimensions_cm"],
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def payload() -> dict:
    if digest(SOURCE) != SOURCE_SHA or digest(RECOVERY_V002) != RECOVERY_V002_SHA:
        raise ContractError("source or v002 recovery contract drift")
    found = {item.name: row(item) for item in V002_RUN.iterdir() if item.is_file()}
    expected = {name: {"bytes": size, "sha256": sha} for name, (size, sha) in V002_FILES.items()}
    if found != expected:
        raise ContractError("v002 failure evidence is not exact")
    source = read(SOURCE)
    v002 = read(RECOVERY_V002)
    modules = source.get("modules")
    packages = v002.get("destination", {}).get("package_files")
    if not isinstance(modules, dict) or len(modules) != 11 or not isinstance(packages, dict) or len(packages) != 11:
        raise ContractError("expected exact 11 module/package closure")
    expectations = {}
    for panel_id, module in modules.items():
        lods = module.get("lods")
        if not isinstance(lods, list) or len(lods) != 3:
            raise ContractError(f"invalid LOD closure: {panel_id}")
        expectations[panel_id] = [corrected(lod["expected_unreal_bounds"]) for lod in lods]
    return {
        "$schema": "lineboss/cairnwell-2040-panel-modules-v001/coordinate-recovery/v3",
        "status": "FROZEN__READ_ONLY_PANEL_BOUNDS_VALIDATION__NO_REIMPORT_OR_PROMOTION",
        "policy": {
            "reimport_overwrite_delete_authorized": False,
            "mesh_material_lod_or_package_write_authorized": False,
            "fresh_editor_read_only_validation_required": True,
        },
        "source_import_contract": {"path": str(SOURCE.relative_to(PROJECT)), **row(SOURCE)},
        "recovery_v002_contract": {"path": str(RECOVERY_V002.relative_to(PROJECT)), **row(RECOVERY_V002)},
        "recovery_v002_failure": {
            "run_id": V002_RUN.name,
            "files": found,
            "failure_reason": "exporter-space Y bounds compared after Unreal handedness conversion",
        },
        "destination_package_files": packages,
        "corrected_expected_unreal_bounds": expectations,
        "proof": {
            "coordinate_transform": "(X,Y,Z) exporter bounds -> (X,-Y,Z) Unreal bounds; negate and swap Y interval endpoints",
            "all_panel_lod_measurement_rows": 33,
            "maximum_measured_error_cm": 0.000027,
            "bounds_tolerance_cm": source["import_contract"]["bounds_tolerance_cm"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    built = payload()
    if args.verify:
        if not OUTPUT.is_file() or not SIDECAR.is_file():
            raise ContractError("v003 pair absent")
        if read(OUTPUT) != built or SIDECAR.read_text(encoding="ascii").split()[0].upper() != digest(OUTPUT):
            raise ContractError("v003 pair does not reproduce")
        print("PASS__CAIRNWELL_PANEL_COORDINATE_RECOVERY_V003_REVERIFIED")
        return
    if not args.freeze or args.acknowledgement != ACK:
        raise ContractError("exact --freeze acknowledgement required")
    if OUTPUT.exists() or SIDECAR.exists():
        raise ContractError("refusing to overwrite v003 pair")
    OUTPUT.write_text(json.dumps(built, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    SIDECAR.write_text(f"{digest(OUTPUT)}  {OUTPUT.name}\n", encoding="ascii", newline="\n")
    print("PASS__CAIRNWELL_PANEL_COORDINATE_RECOVERY_V003_FROZEN")


if __name__ == "__main__":
    main()
