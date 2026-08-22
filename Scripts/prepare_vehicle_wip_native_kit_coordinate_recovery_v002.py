"""Freeze the read-only Unreal-coordinate correction for VehicleWIPNativeKit v001.

The guarded import preserved all 16 newly-created native packages but compared
Blender exporter bounds to UE's FBX-handedness converted mesh bounds.  This
creates a separate recovery authority: it never imports, replaces, saves or
deletes vehicle assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
SOURCE = SCRIPTS / "vehicle_wip_native_kit_unreal_import_contract_v001.json"
BASELINE = SCRIPTS / "vehicle_wip_native_kit_unreal_import_baseline_v001.json"
FAILED_RUN = PROJECT / ("Saved/Audits/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/"
                        "UnrealImportLane_v001/20260821T015722Z-085b45bb")
DESTINATION = PROJECT / "Content/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"
OUTPUT = SCRIPTS / "vehicle_wip_native_kit_coordinate_recovery_v002_contract.json"
SIDECAR = OUTPUT.with_suffix(".sha256")
ACK = "FREEZE_VEHICLE_WIP_NATIVE_KIT_COORDINATE_RECOVERY_V002"
SOURCE_SHA = "87D9FD32964CC0AD0F4AA52CC6F27A0E23BFDA23A18B2F714E6E2807CCA9684D"
FAILED_FILES = {
    "import_failure_v001.json": (7494, "AD2F204526D3847F7B6A42DA54E2DD3AA8CB09E5F95510F47756705CB03D3FE8"),
    "lane_summary_v001.json": (1461, "3A253CD12ED3EF6D568D97E25EAF4FEAAB361D57C466F2B3CF9468F580D26940"),
    "unreal_import.log": (440132, "7F14BE8300AFDC523138D79374950C7596305395A18471CC9E0563A5E27BC74B"),
    "unreal_import.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "unreal_import.stdout.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
}


class ContractError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_pairs)


def row(path: Path) -> dict:
    return {"bytes": path.stat().st_size, "sha256": sha(path)}


def corrected(bounds: dict) -> dict:
    minimum, maximum = bounds["minimum_cm"], bounds["maximum_cm"]
    return {
        "minimum_cm": [minimum[0], -maximum[1], minimum[2]],
        "maximum_cm": [maximum[0], -minimum[1], maximum[2]],
        "dimensions_cm": bounds["dimensions_cm"],
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def payload() -> dict:
    if sha(SOURCE) != SOURCE_SHA:
        raise ContractError("frozen native source-contract drift")
    source, baseline = read(SOURCE), read(BASELINE)
    actual_failure = {path.name: row(path) for path in FAILED_RUN.iterdir() if path.is_file()}
    expected_failure = {name: {"bytes": size, "sha256": digest} for name, (size, digest) in FAILED_FILES.items()}
    if actual_failure != expected_failure:
        raise ContractError("original native import incident closure drift")
    expected_paths = {spec["disk_path"] for spec in source["assets"].values()}
    actual_paths = {str(path.relative_to(PROJECT)).replace("\\", "/") for path in DESTINATION.rglob("*.uasset")}
    if actual_paths != expected_paths or len(actual_paths) != 16:
        raise ContractError("expected exact preserved 16-package native target")
    packages = {path: row(PROJECT / path) for path in sorted(actual_paths)}
    corrected_rows = {}
    for key, spec in baseline["assets"].items():
        lods = spec.get("lods", [])
        if len(lods) != 3:
            raise ContractError(f"invalid three-LOD baseline: {key}")
        corrected_rows[key] = [corrected(lod["expected_unreal_bounds"]) for lod in lods]
    return {
        "$schema": "lineboss/vehicle-wip-native-kit-v001/coordinate-recovery/v2",
        "status": "FROZEN__READ_ONLY_NATIVE_VEHICLE_BOUNDS_VALIDATION__NO_REIMPORT_OR_PROMOTION",
        "policy": {
            "reimport_overwrite_delete_authorized": False,
            "mesh_material_lod_or_package_write_authorized": False,
            "fresh_editor_read_only_validation_required": True,
        },
        "source_import_contract": {"path": str(SOURCE.relative_to(PROJECT)), **row(SOURCE)},
        "import_baseline": {"path": str(BASELINE.relative_to(PROJECT)), **row(BASELINE)},
        "v001_import_failure": {"run_id": FAILED_RUN.name, "files": actual_failure,
            "reason": "exporter-space Y bounds compared after Unreal FBX handedness conversion"},
        "destination_package_files": packages,
        "corrected_expected_unreal_bounds": corrected_rows,
        "proof": {"coordinate_transform": "(X,Y,Z) exporter bounds -> (X,-Y,Z) Unreal bounds; negate and swap Y interval endpoints",
            "asset_count": 16, "authored_lod_count": 48,
            "bounds_tolerance_cm": baseline["import_contract"]["bounds_tolerance_cm"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--acknowledgement", default="")
    args = parser.parse_args()
    built = payload()
    if args.verify:
        if not OUTPUT.is_file() or not SIDECAR.is_file() or read(OUTPUT) != built:
            raise ContractError("coordinate recovery pair does not reproduce")
        if SIDECAR.read_text(encoding="ascii").split()[0].upper() != sha(OUTPUT):
            raise ContractError("coordinate recovery sidecar drift")
        print("PASS__VEHICLE_WIP_NATIVE_KIT_COORDINATE_RECOVERY_V002_REVERIFIED")
        return
    if not args.freeze or args.acknowledgement != ACK:
        raise ContractError("exact --freeze acknowledgement required")
    if OUTPUT.exists() or SIDECAR.exists():
        raise ContractError("refusing to overwrite coordinate recovery pair")
    OUTPUT.write_text(json.dumps(built, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    SIDECAR.write_text(f"{sha(OUTPUT)}  {OUTPUT.name}\n", encoding="ascii", newline="\n")
    print("PASS__VEHICLE_WIP_NATIVE_KIT_COORDINATE_RECOVERY_V002_FROZEN")


if __name__ == "__main__":
    main()
