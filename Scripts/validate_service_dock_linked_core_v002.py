"""Validate MR01 v003 or CR01 v006 against fabricated RP01 core v002."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def world_mm(obj):
    return [round(value * 1000.0, 3) for value in obj.matrix_world.translation]


def size_mm(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [round((max(point[i] for point in points) - min(point[i] for point in points)) * 1000.0, 3) for i in range(3)]


def close(actual, expected, tolerance=1.0):
    return all(abs(actual[i] - expected[i]) <= tolerance for i in range(3))


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2 or args[0].lower() not in {"mr01", "cr01"}:
        raise SystemExit("Usage: -- mr01|cr01 output_validation.json")
    mode = args[0].lower()
    output = Path(args[1]).resolve()
    blend = Path(bpy.data.filepath).resolve()
    objects = bpy.data.objects
    failures = []
    expected_root = "ROOT_LB_MR01_SERVICE_DOCK_V003" if mode == "mr01" else "ROOT_LB_CR01_SERVICE_DOCK_V006"
    if expected_root not in objects:
        failures.append(f"missing variant root {expected_root}")
    if "ROOT_LB_RP01_DOCK_CORE_V002" not in objects:
        failures.append("missing linked RP01 core v002 root")
    base = objects.get("SM_LB_RP01_DockBase")
    base_size = size_mm(base) if base else None
    if base_size is None or not close(base_size, [2600.0, 1400.0, 110.0]):
        failures.append(f"base mismatch: {base_size}")
    common_expected = {
        "SCK_DockDatum": [0.0, 735.0, 310.0],
        "SCK_ChargeContact_L": [-120.0, 735.0, 340.0],
        "SCK_ChargeContact_R": [120.0, 735.0, 340.0],
        "SCK_NetworkContact": [0.0, 735.0, 390.0],
    }
    if mode == "cr01":
        common_expected.update({
            "SCK_WaterFill": [-210.0, 735.0, 280.0],
            "SCK_DirtyExtract": [210.0, 735.0, 280.0],
        })
    sockets = {}
    for name, expected in common_expected.items():
        obj = objects.get(name)
        actual = world_mm(obj) if obj else None
        passed = actual is not None and close(actual, expected)
        sockets[name] = {"expected_blender_mm": expected, "actual_blender_mm": actual, "pass": passed}
        if not passed:
            failures.append(f"socket mismatch {name}: {actual}")
    linked_libraries = sorted(str(library.filepath) for library in bpy.data.libraries)
    linked_objects = [obj.name for obj in objects if obj.library]
    if len(linked_libraries) != 1 or "DockCore_Candidate_v002" not in linked_libraries[0] or len(linked_objects) != 97:
        failures.append(f"fabricated core link mismatch: libraries={linked_libraries}, linked_objects={len(linked_objects)}")
    if "SM_LB_RP01_DockCanopy" not in objects or "SM_LB_RP01_DockRearServiceDoor_L" not in objects:
        failures.append("fabricated canopy/service-door detail missing")
    variant_results = {}
    if mode == "mr01":
        tools = sorted(obj.name for obj in objects if re.match(r"^SM_LB_MR01_T[1-8]_", obj.name))
        cradles = sorted(obj.name for obj in objects if re.match(r"^SM_LB_MR01_DockToolCradle_\d\d$", obj.name))
        rack_sockets = sorted(obj.name for obj in objects if re.match(r"^SCK_DockToolRack_\d\d$", obj.name))
        expected_pivots = {
            "PVT_DockCalibrationProbe": [0.0, 900.0, 950.0],
            "PVT_DockToolRackDoor": [500.0, 1000.0, 900.0],
            "PVT_DockWasteDrawer": [-500.0, 900.0, 420.0],
        }
        for name, expected in expected_pivots.items():
            obj = objects.get(name)
            actual = world_mm(obj) if obj else None
            if actual is None or not close(actual, expected):
                failures.append(f"MR pivot mismatch {name}: {actual}")
        if len(tools) != 8 or len(cradles) != 8 or len(rack_sockets) != 8:
            failures.append(f"MR eight-tool invariant failed: tools={len(tools)}, cradles={len(cradles)}, sockets={len(rack_sockets)}")
        variant_results = {"tools": tools, "cradles": cradles, "rack_sockets": rack_sockets, "pivots": expected_pivots}
    else:
        shifted = [obj.name for obj in objects if obj.get("lb_v005_robot_centred_shift_mm") == 1445.0]
        if len(shifted) != 60:
            failures.append(f"CR shifted cleaning object count mismatch: {len(shifted)}")
        variant_results = {"shifted_cleaning_object_count": len(shifted), "outside_envelope": "TBC"}
    bad_scales = [obj.name for obj in objects if any(abs(value - 1.0) > 1e-6 for value in obj.scale)]
    if bad_scales:
        failures.append(f"non-unit scales: {bad_scales}")
    payload = {
        "$schema": f"cairnwell/validation/{mode}-service-dock-fabricated-core/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FABRICATED_SHARED_CORE_EXACT_VARIANT_INTERFACES__VISUAL_UNREAL_RUNTIME_GATES_OPEN__NOT_PROMOTED" if not failures else "FAIL__SOURCE_GATE",
        "mode": mode,
        "blend": str(blend),
        "blend_sha256": sha256(blend),
        "base_size_blender_mm": base_size,
        "sockets": sockets,
        "linked_libraries": linked_libraries,
        "linked_object_count": len(linked_objects),
        "variant_results": variant_results,
        "bad_scales": bad_scales,
        "failures": failures,
        "fleet_installation_requirement": {f"{mode.upper()}_robots": 2, f"{mode.upper()}_dock_instances": 2},
        "holds": [
            "Fresh visual comparison must decide whether this successor advances beyond the prior source checkpoint.",
            "Clean export/reimport, actual Unreal robot fit, collision, service sweeps, navigation, charging/runtime and Press Shop fixed-camera gates remain open."
        ],
        "promotion_authorized": False
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "linked_objects": len(linked_objects), "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
