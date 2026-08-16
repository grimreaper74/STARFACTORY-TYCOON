"""Freeze exact offline lane scripts/tests/docs without cutting a project baseline."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUTPUT = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_lane_static_freeze_v001.json"
SIDECAR = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_lane_static_freeze_v001.sha256"
BASELINE = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_baseline_v001.json"
TARGET = PROJECT / "Content/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"
FILES = [
    "Scripts/build_vehicle_wip_native_kit_unreal_import_contract_v001.py",
    "Scripts/vehicle_wip_native_kit_unreal_import_contract_v001.json",
    "Scripts/prepare_vehicle_wip_native_kit_unreal_import_baseline_v001.py",
    "Scripts/vehicle_wip_native_kit_unreal_runtime_v001.py",
    "Scripts/import_vehicle_wip_native_kit_v001.py",
    "Scripts/validate_vehicle_wip_native_kit_v001.py",
    "Scripts/run_vehicle_wip_native_kit_unreal_import_lane_v001.ps1",
    "Scripts/tests/test_vehicle_wip_native_kit_unreal_import_lane_v001.py",
    "Docs/VEHICLE_WIP_NATIVE_KIT_UNREAL_IMPORT_LANE_v001.md",
    "Scripts/freeze_vehicle_wip_native_kit_unreal_import_lane_static_v001.py",
]


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def main() -> None:
    if OUTPUT.exists() or SIDECAR.exists():
        raise RuntimeError("refusing to overwrite existing static lane freeze")
    if BASELINE.exists() or TARGET.exists():
        raise RuntimeError("baseline or target Content unexpectedly exists")
    rows = []
    for relative in FILES:
        path = PROJECT / relative
        if not path.is_file():
            raise RuntimeError("static lane file missing: " + relative)
        rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
    canonical = "".join(f"{row['sha256']}  {row['path']}\n" for row in sorted(rows, key=lambda item: item["path"]))
    payload = {
        "$schema": "lineboss/vehicle-wip-native-kit-v001/static-unreal-lane-freeze/v1",
        "status": "FROZEN__OFFLINE_SCRIPTS_TESTS_DOCS_ONLY__NO_PROJECT_BASELINE__NO_UE_RUN",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "destination_reserved_but_absent": "/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001",
        "whole_project_baseline_exists": False,
        "target_content_exists": False,
        "file_count": len(rows),
        "canonical_tree_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper(),
        "files": sorted(rows, key=lambda item: item["path"]),
        "mutation_rule": "Any changed lane script/test/doc requires a new static freeze version before the later project baseline is cut.",
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SIDECAR.write_text(f"{sha256(OUTPUT)}  Scripts/{OUTPUT.name}\n", encoding="utf-8")
    print("PASS__VEHICLE_WIP_NATIVE_STATIC_LANE_FROZEN__NO_BASELINE_NO_UE")
    print("tree=" + payload["canonical_tree_sha256"])
    print("receipt=" + sha256(OUTPUT))


if __name__ == "__main__":
    main()
